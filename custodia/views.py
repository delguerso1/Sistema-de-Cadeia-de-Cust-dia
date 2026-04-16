from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.http import FileResponse, Http404
from pathlib import Path
from typing import List, Optional
from .forms import CustodiaForm
from .models import Arquivo, Custodia
from .pdf_generator import gerar_pdf_custodia


def _normalizar_hash_busca(texto: str) -> str:
    if not texto:
        return ''
    return ''.join(texto.split()).lower()


def _campo_hash_coincide(valor: Optional[str], h_busca: str) -> bool:
    if not valor:
        return False
    v = valor.lower()
    h = h_busca.lower()
    if len(h) == 64:
        return v == h
    return h in v


def _buscar_por_hash_no_banco(h_normalizado: str) -> List[dict]:
    """
    Retorna lista de dicts: custodia, motivos (onde o hash apareceu),
    tem_posterior, proxima (próxima versão na cadeia, se existir).
    """
    hl = h_normalizado
    is_full = len(hl) == 64

    if is_full:
        q_cust = (
            Q(hash_pasta__iexact=hl)
            | Q(hash_cadeia_anterior__iexact=hl)
            | Q(hash_conteudo_novos__iexact=hl)
        )
        q_arq = Q(hash_arquivo__iexact=hl)
    else:
        q_cust = (
            Q(hash_pasta__icontains=hl)
            | Q(hash_cadeia_anterior__icontains=hl)
            | Q(hash_conteudo_novos__icontains=hl)
        )
        q_arq = Q(hash_arquivo__icontains=hl)

    ids = set(Custodia.objects.filter(q_cust).values_list('id', flat=True))
    ids |= set(Arquivo.objects.filter(q_arq).values_list('custodia_id', flat=True))

    if not ids:
        return []

    custodias = (
        Custodia.objects.filter(pk__in=ids)
        .select_related('caso', 'policial', 'custodia_anterior')
        .prefetch_related('arquivos')
        .order_by('-data_criacao', '-id')
    )

    resultados = []
    for c in custodias:
        motivos: list[str] = []
        if _campo_hash_coincide(c.hash_pasta, hl):
            motivos.append('Hash final da cadeia (esta versão)')
        if _campo_hash_coincide(c.hash_cadeia_anterior, hl):
            motivos.append('Hash final da versão anterior (referência explícita)')
        if _campo_hash_coincide(c.hash_conteudo_novos, hl):
            motivos.append('Hash agregado (novos ou alterados nesta versão)')
        for arq in c.arquivos.all():
            if _campo_hash_coincide(arq.hash_arquivo, hl):
                motivos.append(f'Hash do arquivo no inventário: {arq.caminho_relativo}')

        if not motivos:
            continue

        proxima = (
            Custodia.objects.filter(custodia_anterior_id=c.id)
            .order_by('versao', 'id')
            .first()
        )
        resultados.append(
            {
                'custodia': c,
                'motivos': motivos,
                'tem_posterior': proxima is not None,
                'proxima': proxima,
            }
        )
    return resultados


def index(request):
    """View para página inicial com formulário de cadastro"""
    if request.method == 'POST':
        form = CustodiaForm(request.POST)
        if form.is_valid():
            try:
                # Salvar dados e processar
                custodia = form.save()
                
                # Gerar PDF
                try:
                    caminho_pdf = gerar_pdf_custodia(custodia)
                    custodia.pdf_gerado = True
                    custodia.caminho_pdf = caminho_pdf
                    custodia.save()
                except Exception as e:
                    messages.warning(
                        request,
                        f'Custódia criada com sucesso, mas houve erro ao gerar PDF: {str(e)}'
                    )
                
                # Redirecionar para página de resultado
                return redirect('custodia:resultado', custodia_id=custodia.id)
                
            except ValidationError as e:
                for msg in e.messages:
                    messages.error(request, msg)
            except Exception as e:
                messages.error(request, f'Erro ao processar custódia: {str(e)}')
        else:
            messages.error(request, 'Por favor, corrija os erros no formulário.')
    else:
        form = CustodiaForm()
    
    return render(request, 'custodia/index.html', {'form': form})


def processar_custodia(request):
    """View para processar a custódia (pode ser usado via AJAX)"""
    if request.method == 'POST':
        form = CustodiaForm(request.POST)
        if form.is_valid():
            try:
                custodia = form.save()
                
                # Gerar PDF
                caminho_pdf = gerar_pdf_custodia(custodia)
                custodia.pdf_gerado = True
                custodia.caminho_pdf = caminho_pdf
                custodia.save()
                
                return redirect('custodia:resultado', custodia_id=custodia.id)
                
            except ValidationError as e:
                for msg in e.messages:
                    messages.error(request, msg)
                return redirect('custodia:index')
            except Exception as e:
                messages.error(request, f'Erro ao processar: {str(e)}')
                return redirect('custodia:index')
        else:
            messages.error(request, 'Formulário inválido.')
            return redirect('custodia:index')
    
    return redirect('custodia:index')


def resultado(request, custodia_id):
    """View para exibir resultado da custódia criada"""
    custodia = get_object_or_404(
        Custodia.objects.select_related('policial', 'caso', 'custodia_anterior'),
        id=custodia_id,
    )
    
    context = {
        'custodia': custodia,
        'hash_formatado': custodia.hash_pasta,
        'tamanho_formatado': custodia.tamanho_total_formatado(),
        'pdf_disponivel': custodia.pdf_gerado and Path(custodia.caminho_pdf).exists() if custodia.caminho_pdf else False,
    }
    
    return render(request, 'custodia/resultado.html', context)


def download_pdf(request, custodia_id):
    """View para download do PDF gerado"""
    custodia = get_object_or_404(
        Custodia.objects.select_related('policial', 'caso', 'custodia_anterior'),
        id=custodia_id,
    )
    
    if not custodia.pdf_gerado or not custodia.caminho_pdf:
        raise Http404("PDF não foi gerado para esta custódia.")
    
    caminho_pdf = Path(custodia.caminho_pdf)
    
    if not caminho_pdf.exists():
        # Tentar gerar novamente
        try:
            caminho_pdf = Path(gerar_pdf_custodia(custodia))
            custodia.caminho_pdf = str(caminho_pdf)
            custodia.save()
        except Exception as e:
            raise Http404(f"Erro ao gerar PDF: {str(e)}")
    
    try:
        return FileResponse(
            open(caminho_pdf, 'rb'),
            content_type='application/pdf',
            filename=f"custodia_{custodia.numero_documento}.pdf"
        )
    except Exception as e:
        raise Http404(f"Erro ao abrir PDF: {str(e)}")


def lista_custodias(request):
    """View para listar custódias (por padrão só versões atuais; ?historico=1 lista tudo)."""
    historico = request.GET.get('historico') in ('1', 'true', 'yes', 'on')
    qs = Custodia.objects.select_related('policial', 'caso').order_by('-data_criacao')
    if not historico:
        qs = qs.filter(ativo=True)
    custodias = qs[:50]

    busca_hash_valor = request.GET.get('hash', '') or ''
    h_norm = _normalizar_hash_busca(busca_hash_valor)
    resultados_busca = None
    busca_hash_erro = None

    if 'hash' in request.GET:
        if not h_norm:
            busca_hash_erro = 'Informe o código hash para pesquisar.'
            resultados_busca = []
        elif len(h_norm) < 8:
            busca_hash_erro = 'Digite pelo menos 8 caracteres do hash (ou o hash completo de 64 caracteres).'
            resultados_busca = []
        else:
            resultados_busca = _buscar_por_hash_no_banco(h_norm)

    context = {
        'custodias': custodias,
        'historico': historico,
        'busca_hash_valor': busca_hash_valor,
        'resultados_busca': resultados_busca,
        'busca_hash_erro': busca_hash_erro,
        'busca_hash_executada': 'hash' in request.GET,
    }

    return render(request, 'custodia/lista.html', context)


def detalhes_custodia(request, custodia_id):
    """View para exibir detalhes completos de uma custódia"""
    custodia = get_object_or_404(
        Custodia.objects.select_related('policial', 'caso', 'custodia_anterior'),
        id=custodia_id,
    )

    # Obter arquivos paginados
    arquivos = custodia.arquivos.all().order_by('caminho_relativo')

    total_versoes_caso = Custodia.objects.filter(caso_id=custodia.caso_id).count()
    proxima_versao = (
        Custodia.objects.filter(custodia_anterior_id=custodia.id)
        .order_by('-versao', '-data_criacao')
        .first()
    )

    context = {
        'custodia': custodia,
        'arquivos': arquivos,
        'total_arquivos': custodia.total_arquivos,
        'pdf_disponivel': custodia.pdf_gerado and Path(custodia.caminho_pdf).exists() if custodia.caminho_pdf else False,
        'total_versoes_caso': total_versoes_caso,
        'proxima_versao': proxima_versao,
    }

    return render(request, 'custodia/detalhes.html', context)
