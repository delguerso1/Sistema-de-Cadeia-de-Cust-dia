from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.pdfgen import canvas
from io import BytesIO
import html
import qrcode
from django.conf import settings
from django.utils import timezone
from pathlib import Path
from .models import Custodia
from .utils import formatar_tamanho


def criar_qrcode_hash(hash_value: str) -> BytesIO:
    """Cria um QR Code com o hash e retorna como BytesIO"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(hash_value)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    img_bytes = BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    return img_bytes


def gerar_pdf_custodia(custodia: Custodia) -> str:
    """
    Gera o PDF completo da cadeia de custódia
    
    Retorna o caminho do arquivo PDF gerado
    """
    # Criar nome do arquivo
    nome_arquivo = f"custodia_{custodia.numero_documento}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    caminho_pdf = Path(settings.PDFS_DIR) / nome_arquivo
    
    # Garantir que a pasta existe
    settings.PDFS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Criar documento PDF
    doc = SimpleDocTemplate(
        str(caminho_pdf),
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    # Container para elementos do PDF
    story = []
    
    # Estilos
    styles = getSampleStyleSheet()
    
    # Estilos customizados
    titulo_style = ParagraphStyle(
        'TituloCustom',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    subtitulo_style = ParagraphStyle(
        'SubtituloCustom',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=12,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )
    
    hash_style = ParagraphStyle(
        'HashStyle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.HexColor('#c0392b'),
        fontName='Courier-Bold',
        alignment=TA_CENTER,
        backColor=colors.HexColor('#ecf0f1'),
        borderPadding=10
    )
    
    normal_style = ParagraphStyle(
        'NormalCustom',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#34495e'),
        alignment=TA_JUSTIFY
    )
    
    # Estilo para células da tabela (quebra de linha)
    cell_style = ParagraphStyle(
        'CellCustom',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.black,
        alignment=TA_LEFT,
        leftIndent=0,
        rightIndent=0,
        spaceBefore=0,
        spaceAfter=0,
    )
    
    # ========== CABEÇALHO ==========
    story.append(Paragraph("DOCUMENTO DE CADEIA DE CUSTÓDIA", titulo_style))
    story.append(Paragraph("DOCUMENTOS E ARQUIVOS", titulo_style))
    story.append(Spacer(1, 0.5*cm))
    
    # Informações do documento
    info_doc_data = [
        ['Número do Documento:', custodia.numero_documento],
        ['Data e Hora de Geração:', timezone.now().strftime('%d/%m/%Y %H:%M:%S')],
    ]
    info_doc_table = Table(info_doc_data, colWidths=[6*cm, 10*cm])
    info_doc_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#ecf0f1')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    story.append(info_doc_table)
    story.append(Spacer(1, 0.8*cm))
    
    # ========== INFORMAÇÕES DO POLICIAL ==========
    story.append(Paragraph("INFORMAÇÕES DO POLICIAL RESPONSÁVEL", subtitulo_style))
    
    policial_data = [
        ['Nome Completo:', custodia.policial.nome_completo],
        ['Matrícula/Registro:', custodia.policial.matricula],
        ['Cargo/Função:', custodia.policial.cargo or 'Não informado'],
        ['Delegacia/Unidade:', custodia.policial.delegacia or 'Não informado'],
    ]
    policial_table = Table(policial_data, colWidths=[6*cm, 10*cm])
    policial_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#ecf0f1')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    story.append(policial_table)
    story.append(Spacer(1, 0.8*cm))
    
    # ========== INFORMAÇÕES DO CASO ==========
    story.append(Paragraph("INFORMAÇÕES DO CASO", subtitulo_style))
    
    caso_data = [
        ['Número do Procedimento/Inquérito:', custodia.caso.numero_procedimento],
        ['Local do Crime:', custodia.caso.local_crime],
        ['Data e Hora da Coleta no Local:', custodia.caso.data_coleta.strftime('%d/%m/%Y %H:%M:%S')],
    ]
    caso_table = Table(caso_data, colWidths=[6*cm, 10*cm])
    caso_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#ecf0f1')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    story.append(caso_table)
    story.append(Spacer(1, 0.8*cm))
    
    # ========== INFORMAÇÕES TÉCNICAS ==========
    story.append(Paragraph("INFORMAÇÕES TÉCNICAS", subtitulo_style))
    
    # Hash em destaque: label e valor em tabela para evitar sobreposição
    story.append(Spacer(1, 0.3*cm))
    hash_table_data = [
        [Paragraph("Código Hash SHA-256 da Pasta:", normal_style)],
        [Paragraph(custodia.hash_pasta, hash_style)],
    ]
    hash_table = Table(hash_table_data, colWidths=[16*cm])
    hash_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (0, 0), 4),
        ('TOPPADDING', (0, 1), (0, 1), 8),
    ]))
    story.append(hash_table)
    story.append(Spacer(1, 0.3*cm))
    
    # Outras informações técnicas
    info_tec_data = [
        ['Data e Hora da Geração do Hash:', custodia.data_criacao.strftime('%d/%m/%Y %H:%M:%S')],
        ['Caminho Completo da Pasta:', custodia.caminho_pasta],
        ['Tamanho Total da Pasta:', formatar_tamanho(custodia.tamanho_total or 0)],
        ['Total de Arquivos:', str(custodia.total_arquivos)],
    ]
    info_tec_table = Table(info_tec_data, colWidths=[6*cm, 10*cm])
    info_tec_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#ecf0f1')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    story.append(info_tec_table)
    story.append(Spacer(1, 0.8*cm))
    
    # ========== INVENTÁRIO DE ARQUIVOS ==========
    story.append(Paragraph("INVENTÁRIO DE ARQUIVOS", subtitulo_style))
    
    arquivos = custodia.arquivos.all()[:100]  # Limitar a 100 arquivos na primeira página
    
    if arquivos:
        # Cabeçalho da tabela
        arquivos_data = [['Nome do Arquivo', 'Tamanho', 'Data Modificação', 'Tipo']]
        
        for arquivo in arquivos:
            nome_seguro = html.escape(arquivo.nome_arquivo or '')
            tipo_seguro = html.escape(arquivo.tipo_mime or 'N/A')
            arquivos_data.append([
                Paragraph(nome_seguro, cell_style),
                formatar_tamanho(arquivo.tamanho_bytes or 0),
                arquivo.data_modificacao.strftime('%d/%m/%Y %H:%M') if arquivo.data_modificacao else 'N/A',
                Paragraph(tipo_seguro, cell_style),
            ])
        
        # Colunas: nome maior, tipo maior para MIME longos; tamanho e data fixos
        arquivos_table = Table(arquivos_data, colWidths=[6*cm, 2.5*cm, 2.8*cm, 4.7*cm])
        arquivos_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
        ]))
        story.append(arquivos_table)
        
        if custodia.total_arquivos > 100:
            story.append(Spacer(1, 0.3*cm))
            story.append(Paragraph(
                f"<i>Nota: Exibindo 100 de {custodia.total_arquivos} arquivos. "
                "Consulte o banco de dados para lista completa.</i>",
                normal_style
            ))
    else:
        story.append(Paragraph("Nenhum arquivo registrado.", normal_style))
    
    story.append(Spacer(1, 0.8*cm))
    
    # ========== ESTATÍSTICAS ==========
    story.append(Paragraph("ESTATÍSTICAS", subtitulo_style))
    
    # Contar arquivos por tipo
    tipos_arquivo = {}
    for arquivo in custodia.arquivos.all():
        extensao = Path(arquivo.nome_arquivo).suffix.lower() or 'sem extensão'
        tipos_arquivo[extensao] = tipos_arquivo.get(extensao, 0) + 1
    
    stats_data = [
        ['Total de Arquivos:', str(custodia.total_arquivos)],
        ['Tamanho Total:', formatar_tamanho(custodia.tamanho_total or 0)],
    ]
    
    if tipos_arquivo:
        tipos_str = ', '.join([f"{ext} ({count})" for ext, count in sorted(tipos_arquivo.items())])
        stats_data.append(['Formatos de Arquivo:', tipos_str])
    
    stats_table = Table(stats_data, colWidths=[6*cm, 10*cm])
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#ecf0f1')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    story.append(stats_table)
    story.append(Spacer(1, 0.8*cm))
    
    # ========== QR CODE ==========
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph("VERIFICAÇÃO RÁPIDA", subtitulo_style))
    story.append(Paragraph("Escaneie o QR Code abaixo para verificar o hash:", normal_style))
    story.append(Spacer(1, 0.3*cm))
    
    # Criar QR Code
    qr_img_bytes = criar_qrcode_hash(custodia.hash_pasta)
    qr_img = Image(qr_img_bytes, width=5*cm, height=5*cm)
    story.append(qr_img)
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph(f"Hash: {custodia.hash_pasta}", hash_style))
    story.append(Spacer(1, 0.5*cm))
    
    # ========== OBSERVAÇÕES ==========
    if custodia.observacoes:
        story.append(Paragraph("OBSERVAÇÕES", subtitulo_style))
        story.append(Paragraph(custodia.observacoes, normal_style))
        story.append(Spacer(1, 0.5*cm))
    
    # ========== RODAPÉ ==========
    story.append(Spacer(1, 1*cm))
    story.append(Paragraph(
        "<i>Este documento foi gerado automaticamente pelo Sistema de Cadeia de Custódia. "
        "O hash SHA-256 garante a integridade dos arquivos. Qualquer alteração nos arquivos "
        "resultará em um hash diferente.</i>",
        normal_style
    ))
    
    # Construir PDF
    doc.build(story)
    
    return str(caminho_pdf)
