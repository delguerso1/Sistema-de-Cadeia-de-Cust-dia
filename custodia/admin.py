from django.contrib import admin
from .models import Policial, Caso, Custodia, Arquivo


@admin.register(Policial)
class PolicialAdmin(admin.ModelAdmin):
    list_display = ('nome_completo', 'matricula', 'cargo', 'delegacia', 'ativo', 'data_cadastro')
    list_filter = ('ativo', 'delegacia', 'data_cadastro')
    search_fields = ('nome_completo', 'matricula', 'cargo', 'delegacia')
    readonly_fields = ('data_cadastro',)
    ordering = ('nome_completo',)


@admin.register(Caso)
class CasoAdmin(admin.ModelAdmin):
    list_display = ('numero_procedimento', 'local_crime', 'data_coleta', 'data_cadastro')
    list_filter = ('data_coleta', 'data_cadastro')
    search_fields = ('numero_procedimento', 'local_crime')
    readonly_fields = ('data_cadastro',)
    ordering = ('-data_cadastro',)


class ArquivoInline(admin.TabularInline):
    model = Arquivo
    extra = 0
    readonly_fields = ('nome_arquivo', 'caminho_relativo', 'tamanho_bytes', 'data_modificacao', 'hash_arquivo', 'tipo_mime')
    can_delete = False
    fields = ('nome_arquivo', 'caminho_relativo', 'tamanho_bytes', 'data_modificacao', 'hash_arquivo')


@admin.register(Custodia)
class CustodiaAdmin(admin.ModelAdmin):
    list_display = ('numero_documento', 'policial', 'caso', 'hash_pasta_short', 'total_arquivos', 'tamanho_total_formatado', 'pdf_gerado', 'data_criacao')
    list_filter = ('pdf_gerado', 'data_criacao', 'policial', 'caso')
    search_fields = ('numero_documento', 'hash_pasta', 'policial__nome_completo', 'caso__numero_procedimento')
    readonly_fields = ('numero_documento', 'hash_pasta', 'data_criacao', 'tamanho_total', 'total_arquivos', 'caminho_pdf')
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('numero_documento', 'hash_pasta', 'data_criacao')
        }),
        ('Relacionamentos', {
            'fields': ('policial', 'caso')
        }),
        ('Informações da Pasta', {
            'fields': ('caminho_pasta', 'tamanho_total', 'total_arquivos')
        }),
        ('PDF', {
            'fields': ('pdf_gerado', 'caminho_pdf')
        }),
        ('Outros', {
            'fields': ('observacoes',)
        }),
    )
    inlines = [ArquivoInline]
    ordering = ('-data_criacao',)
    
    def hash_pasta_short(self, obj):
        return f"{obj.hash_pasta[:16]}..." if obj.hash_pasta else "-"
    hash_pasta_short.short_description = "Hash (resumido)"
    
    def tamanho_total_formatado(self, obj):
        return obj.tamanho_total_formatado()
    tamanho_total_formatado.short_description = "Tamanho Total"


@admin.register(Arquivo)
class ArquivoAdmin(admin.ModelAdmin):
    list_display = ('nome_arquivo', 'custodia', 'tamanho_formatado', 'hash_arquivo', 'data_modificacao')
    list_filter = ('data_modificacao', 'custodia')
    search_fields = ('nome_arquivo', 'caminho_completo', 'hash_arquivo', 'custodia__numero_documento')
    readonly_fields = ('custodia', 'nome_arquivo', 'caminho_completo', 'caminho_relativo', 'tamanho_bytes', 'data_modificacao', 'hash_arquivo', 'tipo_mime')
    ordering = ('custodia', 'caminho_relativo')
    
    def tamanho_formatado(self, obj):
        return obj.tamanho_formatado()
    tamanho_formatado.short_description = "Tamanho"
