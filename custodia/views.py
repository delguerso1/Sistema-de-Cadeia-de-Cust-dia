from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import FileResponse, Http404
from django.conf import settings
from pathlib import Path
from .forms import CustodiaForm
from .models import Custodia
from .pdf_generator import gerar_pdf_custodia


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
                
            except Exception as e:
                messages.error(request, f'Erro ao processar: {str(e)}')
                return redirect('custodia:index')
        else:
            messages.error(request, 'Formulário inválido.')
            return redirect('custodia:index')
    
    return redirect('custodia:index')


def resultado(request, custodia_id):
    """View para exibir resultado da custódia criada"""
    custodia = get_object_or_404(Custodia, id=custodia_id)
    
    context = {
        'custodia': custodia,
        'hash_formatado': custodia.hash_pasta,
        'tamanho_formatado': custodia.tamanho_total_formatado(),
        'pdf_disponivel': custodia.pdf_gerado and Path(custodia.caminho_pdf).exists() if custodia.caminho_pdf else False,
    }
    
    return render(request, 'custodia/resultado.html', context)


def download_pdf(request, custodia_id):
    """View para download do PDF gerado"""
    custodia = get_object_or_404(Custodia, id=custodia_id)
    
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
    """View para listar todas as custódias (funcionalidade adicional)"""
    custodias = Custodia.objects.all().order_by('-data_criacao')[:50]
    
    context = {
        'custodias': custodias
    }
    
    return render(request, 'custodia/lista.html', context)


def detalhes_custodia(request, custodia_id):
    """View para exibir detalhes completos de uma custódia"""
    custodia = get_object_or_404(Custodia, id=custodia_id)
    
    # Obter arquivos paginados
    arquivos = custodia.arquivos.all()[:100]
    
    context = {
        'custodia': custodia,
        'arquivos': arquivos,
        'total_arquivos': custodia.total_arquivos,
        'pdf_disponivel': custodia.pdf_gerado and Path(custodia.caminho_pdf).exists() if custodia.caminho_pdf else False,
    }
    
    return render(request, 'custodia/detalhes.html', context)
