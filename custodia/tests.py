"""Testes de versionamento de custódia por caso."""
import tempfile
from pathlib import Path

from django.test import Client, TestCase
from django.urls import reverse

from .models import Custodia
from .utils import calcular_hash_cadeia


class CustodiaVersioningTests(TestCase):
    """Valida criação automática de versões para o mesmo procedimento/caso."""

    def setUp(self):
        self.client = Client()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        base = Path(self.tmp.name)
        (base / "arquivo1.txt").write_bytes(b"conteudo-a")

    def _post_custodia(self, procedimento="INQ-VERS-001"):
        url = reverse("custodia:index")
        data = {
            "nome_policial": "Fulano da Silva",
            "matricula": "MAT999",
            "cargo": "Investigador",
            "delegacia": "DP",
            "numero_procedimento": procedimento,
            "local_crime": "Rua Teste, 1",
            "data_coleta": "2024-06-01T10:00:00",
            "caminho_pasta": str(Path(self.tmp.name)),
            "observacoes": "",
        }
        return self.client.post(url, data)

    def test_primeira_versao_ativa(self):
        response = self._post_custodia()
        self.assertEqual(response.status_code, 302)
        c = Custodia.objects.get(caso__numero_procedimento="INQ-VERS-001")
        self.assertEqual(c.versao, 1)
        self.assertTrue(c.ativo)
        self.assertIsNone(c.custodia_anterior_id)
        self.assertEqual(c.hash_pasta, c.hash_conteudo_novos)
        self.assertEqual(c.hash_cadeia_anterior, "")

    def test_segunda_versao_desativa_anterior_e_encadeia(self):
        r1 = self._post_custodia()
        self.assertEqual(r1.status_code, 302)
        # Novo arquivo na mesma pasta (novo hash consolidado)
        (Path(self.tmp.name) / "arquivo2.txt").write_bytes(b"conteudo-b")
        r2 = self._post_custodia()
        self.assertEqual(r2.status_code, 302)

        qs = Custodia.objects.filter(
            caso__numero_procedimento="INQ-VERS-001"
        ).order_by("versao")
        self.assertEqual(qs.count(), 2)

        v1, v2 = qs[0], qs[1]
        self.assertEqual(v1.versao, 1)
        self.assertEqual(v2.versao, 2)
        self.assertFalse(v1.ativo)
        self.assertTrue(v2.ativo)
        self.assertEqual(v2.custodia_anterior_id, v1.id)
        self.assertEqual(v2.hash_cadeia_anterior, v1.hash_pasta)
        self.assertEqual(
            v2.hash_pasta,
            calcular_hash_cadeia(v1.hash_pasta, v2.hash_conteudo_novos),
        )
        arq_v2 = {a.caminho_relativo: a.novo_ou_alterado for a in v2.arquivos.all()}
        self.assertFalse(arq_v2["arquivo1.txt"])
        self.assertTrue(arq_v2["arquivo2.txt"])

    def test_reprocessar_sem_arquivos_novos_falha(self):
        self._post_custodia("INQ-NODELTA")
        r2 = self._post_custodia("INQ-NODELTA")
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(
            Custodia.objects.filter(caso__numero_procedimento="INQ-NODELTA").count(),
            1,
        )

    def test_lista_padrao_so_versoes_ativas(self):
        self._post_custodia("INQ-LISTA")
        (Path(self.tmp.name) / "extra.txt").write_bytes(b"x")
        self._post_custodia("INQ-LISTA")

        url = reverse("custodia:lista")
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)
        # Uma custódia ativa por procedimento na listagem padrão
        self.assertEqual(
            Custodia.objects.filter(
                caso__numero_procedimento="INQ-LISTA", ativo=True
            ).count(),
            1,
        )
        self.assertEqual(
            Custodia.objects.filter(caso__numero_procedimento="INQ-LISTA").count(),
            2,
        )

        rh = self.client.get(url + "?historico=1")
        self.assertEqual(rh.status_code, 200)
        self.assertEqual(len(rh.context["custodias"]), 2)

    def test_busca_hash_na_lista_encontra_hash_final(self):
        self._post_custodia("INQ-HASH")
        c = Custodia.objects.get(caso__numero_procedimento="INQ-HASH")
        url = reverse("custodia:lista") + "?hash=" + c.hash_pasta
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.context["busca_hash_executada"])
        self.assertIsNone(r.context["busca_hash_erro"])
        self.assertEqual(len(r.context["resultados_busca"]), 1)
        self.assertTrue(r.context["resultados_busca"][0]["tem_posterior"] is False)
