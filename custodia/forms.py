from django import forms
from django.core.exceptions import ValidationError
from django.db import transaction
from .models import Policial, Caso, Custodia


class CustodiaForm(forms.Form):
    """Formulário completo para cadastro de cadeia de custódia"""
    
    # Informações do Policial
    nome_policial = forms.CharField(
        max_length=255,
        label="Nome Completo",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Digite o nome completo do policial'
        }),
        required=True
    )
    
    matricula = forms.CharField(
        max_length=50,
        label="Matrícula/Registro",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ex: 12345'
        }),
        required=True
    )
    
    cargo = forms.CharField(
        max_length=100,
        label="Cargo/Função",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ex: Delegado, Investigador, etc.'
        }),
        required=False
    )
    
    delegacia = forms.CharField(
        max_length=255,
        label="Delegacia/Unidade",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nome da delegacia ou unidade'
        }),
        required=False
    )
    
    # Informações do Caso
    numero_procedimento = forms.CharField(
        max_length=100,
        label="Número do Procedimento/Inquérito",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ex: INQ 001/2024'
        }),
        required=True
    )
    
    local_crime = forms.CharField(
        label="Local do Crime",
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Endereço completo do local do crime'
        }),
        required=True
    )
    
    data_coleta = forms.DateTimeField(
        label="Data e Hora da Coleta no Local",
        widget=forms.DateTimeInput(attrs={
            'class': 'form-control',
            'type': 'datetime-local'
        }),
        required=True
    )
    
    # Seleção de Pasta
    caminho_pasta = forms.CharField(
        label="Caminho da Pasta com Documentos",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'C:\\Caminho\\Para\\Pasta\\Documentos',
            'id': 'caminho-pasta'
        }),
        required=True,
        help_text="Digite o caminho completo da pasta contendo os documentos/arquivos (inclui todas as subpastas)"
    )
    
    observacoes = forms.CharField(
        label="Observações",
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Observações adicionais (opcional)'
        }),
        required=False
    )
    
    def clean_matricula(self):
        matricula = self.cleaned_data.get('matricula')
        if matricula:
            # Validar que contém apenas letras e números
            if not matricula.replace(' ', '').isalnum():
                raise ValidationError('A matrícula deve conter apenas letras e números.')
        return matricula
    
    def clean_caminho_pasta(self):
        caminho = self.cleaned_data.get('caminho_pasta')
        if caminho:
            from pathlib import Path
            from .utils import validar_pasta_arquivos
            
            pasta = Path(caminho.strip())
            if not pasta.exists():
                raise ValidationError('A pasta especificada não existe.')
            
            if not pasta.is_dir():
                raise ValidationError('O caminho especificado não é uma pasta.')
            
            # Validar se contém arquivos (qualquer tipo)
            valido, mensagem = validar_pasta_arquivos(str(pasta))
            if not valido:
                raise ValidationError(mensagem)
        
        return caminho
    
    def save(self):
        """Salva os dados no banco de dados (nova versão automática por caso/procedimento)."""
        from .models import Arquivo
        from datetime import datetime

        # Obter dados do formulário
        nome_policial = self.cleaned_data['nome_policial']
        matricula = self.cleaned_data['matricula']
        cargo = self.cleaned_data.get('cargo', '')
        delegacia = self.cleaned_data.get('delegacia', '')
        numero_procedimento = self.cleaned_data['numero_procedimento']
        local_crime = self.cleaned_data['local_crime']
        data_coleta = self.cleaned_data['data_coleta']
        caminho_pasta = self.cleaned_data['caminho_pasta']
        observacoes = self.cleaned_data.get('observacoes', '')

        from .utils import (
            calcular_hash_pasta,
            combinar_hashes_lista_arquivos,
            calcular_hash_cadeia,
            particionar_novos_ou_alterados,
        )

        # Varredura completa da pasta (hashes por arquivo + lista)
        _, lista_arquivos = calcular_hash_pasta(caminho_pasta)

        with transaction.atomic():
            # Criar ou obter Policial
            policial, _ = Policial.objects.get_or_create(
                matricula=matricula,
                defaults={
                    'nome_completo': nome_policial,
                    'cargo': cargo,
                    'delegacia': delegacia
                }
            )

            # Atualizar dados do policial se necessário
            if policial.nome_completo != nome_policial or policial.cargo != cargo or policial.delegacia != delegacia:
                policial.nome_completo = nome_policial
                policial.cargo = cargo
                policial.delegacia = delegacia
                policial.save()

            # Criar ou obter Caso
            caso, _ = Caso.objects.get_or_create(
                numero_procedimento=numero_procedimento,
                defaults={
                    'local_crime': local_crime,
                    'data_coleta': data_coleta
                }
            )

            # Atualizar dados do caso se necessário
            if caso.local_crime != local_crime or caso.data_coleta != data_coleta:
                caso.local_crime = local_crime
                caso.data_coleta = data_coleta
                caso.save()

            # Versão: desativa a atual do caso e encadeia a nova
            ultima = (
                Custodia.objects.select_for_update()
                .filter(caso=caso, ativo=True)
                .order_by('-versao', '-data_criacao', '-id')
                .first()
            )

            hash_cadeia_anterior = ''
            novos_infos = []
            if ultima:
                mapa_prev = {
                    a.caminho_relativo: a.hash_arquivo
                    for a in ultima.arquivos.all()
                }
                novos_infos, _ = particionar_novos_ou_alterados(lista_arquivos, mapa_prev)
                if not novos_infos:
                    raise ValidationError(
                        'Não há arquivos novos nem alterados em relação à versão anterior '
                        'deste procedimento. Inclua documentos ou altere arquivos existentes '
                        'antes de gerar uma nova versão.'
                    )
                hash_conteudo_novos = combinar_hashes_lista_arquivos(novos_infos)
                hash_cadeia_anterior = ultima.hash_pasta
                hash_pasta_final = calcular_hash_cadeia(hash_cadeia_anterior, hash_conteudo_novos)
                Custodia.objects.filter(pk=ultima.pk).update(ativo=False)
                nova_versao = ultima.versao + 1
                custodia_anterior = ultima
                novos_paths = {x['caminho_relativo'] for x in novos_infos}
            else:
                hash_conteudo_novos = combinar_hashes_lista_arquivos(lista_arquivos)
                hash_pasta_final = hash_conteudo_novos
                nova_versao = 1
                custodia_anterior = None
                novos_paths = None

            # Gerar número do documento (microsegundos evitam colisão em reenvios no mesmo segundo)
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')
            caso_limpo = ''.join(c for c in numero_procedimento if c.isalnum() or c in ['-', '_'])
            numero_documento = f"CUST-{caso_limpo}-{timestamp}"

            # Calcular tamanho total
            tamanho_total = sum(arquivo['tamanho_bytes'] for arquivo in lista_arquivos)

            # Criar Custodia
            custodia = Custodia.objects.create(
                numero_documento=numero_documento,
                hash_pasta=hash_pasta_final,
                hash_cadeia_anterior=hash_cadeia_anterior,
                hash_conteudo_novos=hash_conteudo_novos,
                caminho_pasta=caminho_pasta,
                tamanho_total=tamanho_total,
                total_arquivos=len(lista_arquivos),
                observacoes=observacoes,
                policial=policial,
                caso=caso,
                versao=nova_versao,
                custodia_anterior=custodia_anterior,
                ativo=True,
            )

            # Criar registros de Arquivo (inventário completo; marca o que entrou no delta desta versão)
            for info_arquivo in lista_arquivos:
                rel = info_arquivo['caminho_relativo']
                novo_flag = True if novos_paths is None else (rel in novos_paths)
                Arquivo.objects.create(
                    custodia=custodia,
                    nome_arquivo=info_arquivo['nome_arquivo'],
                    caminho_completo=info_arquivo['caminho_completo'],
                    caminho_relativo=info_arquivo['caminho_relativo'],
                    tamanho_bytes=info_arquivo['tamanho_bytes'],
                    data_modificacao=info_arquivo['data_modificacao'],
                    hash_arquivo=info_arquivo.get('hash', ''),
                    tipo_mime=info_arquivo['tipo_mime'],
                    novo_ou_alterado=novo_flag,
                )

        return custodia
