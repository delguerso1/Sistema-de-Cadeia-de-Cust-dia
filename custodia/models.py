from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone


class Policial(models.Model):
    """Modelo para armazenar informações dos policiais"""
    nome_completo = models.CharField(max_length=255, verbose_name="Nome Completo")
    matricula = models.CharField(
        max_length=50, 
        unique=True, 
        verbose_name="Matrícula/Registro",
        validators=[RegexValidator(regex=r'^[A-Za-z0-9]+$', message='Matrícula deve conter apenas letras e números')]
    )
    cargo = models.CharField(max_length=100, verbose_name="Cargo/Função", blank=True)
    delegacia = models.CharField(max_length=255, verbose_name="Delegacia/Unidade", blank=True)
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    data_cadastro = models.DateTimeField(auto_now_add=True, verbose_name="Data de Cadastro")

    class Meta:
        verbose_name = "Policial"
        verbose_name_plural = "Policiais"
        ordering = ['nome_completo']

    def __str__(self):
        return f"{self.nome_completo} ({self.matricula})"


class Caso(models.Model):
    """Modelo para armazenar informações dos casos/inquéritos"""
    numero_procedimento = models.CharField(
        max_length=100, 
        unique=True, 
        verbose_name="Número do Procedimento/Inquérito"
    )
    local_crime = models.TextField(verbose_name="Local do Crime")
    data_coleta = models.DateTimeField(verbose_name="Data e Hora da Coleta no Local")
    observacoes = models.TextField(blank=True, verbose_name="Observações")
    data_cadastro = models.DateTimeField(auto_now_add=True, verbose_name="Data de Cadastro")

    class Meta:
        verbose_name = "Caso"
        verbose_name_plural = "Casos"
        ordering = ['-data_cadastro']

    def __str__(self):
        return f"{self.numero_procedimento} - {self.local_crime[:50]}"


class Custodia(models.Model):
    """Modelo principal para armazenar informações da cadeia de custódia"""
    numero_documento = models.CharField(
        max_length=50, 
        unique=True, 
        verbose_name="Número do Documento"
    )
    hash_pasta = models.CharField(
        max_length=64,
        verbose_name="Hash final da cadeia (esta versão)",
        help_text=(
            "Versão 1: igual ao agregado de todos os arquivos. Versões seguintes: "
            "SHA-256 do par (hash da versão anterior | hash agregado só dos arquivos novos ou alterados)."
        ),
    )
    hash_cadeia_anterior = models.CharField(
        max_length=64,
        blank=True,
        verbose_name="Hash final da versão anterior (referência explícita)",
        help_text="Cópia do hash final da custódia imediatamente anterior, para rastreabilidade.",
    )
    hash_conteudo_novos = models.CharField(
        max_length=64,
        verbose_name="Hash agregado (novos ou alterados nesta versão)",
        help_text="Agregado SHA-256 apenas dos arquivos novos ou com conteúdo alterado em relação à versão anterior.",
    )
    data_criacao = models.DateTimeField(default=timezone.now, verbose_name="Data de Criação")
    caminho_pasta = models.TextField(verbose_name="Caminho Completo da Pasta")
    tamanho_total = models.BigIntegerField(verbose_name="Tamanho Total (bytes)", null=True, blank=True)
    total_arquivos = models.IntegerField(verbose_name="Total de Arquivos", default=0)
    observacoes = models.TextField(blank=True, verbose_name="Observações")
    pdf_gerado = models.BooleanField(default=False, verbose_name="PDF Gerado")
    caminho_pdf = models.TextField(blank=True, verbose_name="Caminho do PDF")
    
    # Relacionamentos
    policial = models.ForeignKey(
        Policial, 
        on_delete=models.PROTECT, 
        verbose_name="Policial Responsável",
        related_name='custodias'
    )
    caso = models.ForeignKey(
        Caso, 
        on_delete=models.PROTECT, 
        verbose_name="Caso",
        related_name='custodias'
    )
    versao = models.PositiveIntegerField(
        default=1,
        verbose_name="Versão",
        help_text="Número sequencial da custódia dentro do mesmo procedimento/caso.",
    )
    custodia_anterior = models.ForeignKey(
        'self',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='custodias_posteriores',
        verbose_name="Custódia anterior",
        help_text="Versão imediatamente anterior no mesmo caso, se houver.",
    )
    ativo = models.BooleanField(
        default=True,
        verbose_name="Versão atual do caso",
        help_text="Somente a versão mais recente do caso fica marcada como atual.",
    )

    class Meta:
        verbose_name = "Custódia"
        verbose_name_plural = "Custódias"
        ordering = ['-data_criacao']
        indexes = [
            models.Index(fields=['caso', 'ativo'], name='custodia_caso_ativo_idx'),
            models.Index(fields=['caso', 'versao'], name='custodia_caso_versao_idx'),
        ]

    def __str__(self):
        return f"{self.numero_documento} - {self.hash_pasta[:16]}..."

    def tamanho_total_formatado(self):
        """Retorna o tamanho total formatado em MB/GB"""
        if not self.tamanho_total:
            return "0 B"
        tamanho = self.tamanho_total
        for unidade in ['B', 'KB', 'MB', 'GB', 'TB']:
            if tamanho < 1024.0:
                return f"{tamanho:.2f} {unidade}"
            tamanho /= 1024.0
        return f"{tamanho:.2f} PB"


class Arquivo(models.Model):
    """Modelo para armazenar informações dos arquivos individuais"""
    custodia = models.ForeignKey(
        Custodia, 
        on_delete=models.CASCADE, 
        verbose_name="Custódia",
        related_name='arquivos'
    )
    nome_arquivo = models.CharField(max_length=255, verbose_name="Nome do Arquivo")
    caminho_completo = models.TextField(verbose_name="Caminho Completo")
    caminho_relativo = models.TextField(verbose_name="Caminho Relativo")
    tamanho_bytes = models.BigIntegerField(verbose_name="Tamanho (bytes)", null=True, blank=True)
    data_modificacao = models.DateTimeField(null=True, blank=True, verbose_name="Data de Modificação")
    hash_arquivo = models.CharField(max_length=64, blank=True, verbose_name="Hash SHA-256 do Arquivo")
    tipo_mime = models.CharField(max_length=100, blank=True, verbose_name="Tipo MIME")
    duracao_segundos = models.IntegerField(null=True, blank=True, verbose_name="Duração (segundos)")
    novo_ou_alterado = models.BooleanField(
        default=True,
        verbose_name="Novo ou alterado nesta versão",
        help_text="Falso se o arquivo já existia com o mesmo hash na versão anterior.",
    )

    class Meta:
        verbose_name = "Arquivo"
        verbose_name_plural = "Arquivos"
        ordering = ['caminho_relativo']

    def __str__(self):
        return self.nome_arquivo

    def tamanho_formatado(self):
        """Retorna o tamanho formatado em MB/GB"""
        if not self.tamanho_bytes:
            return "0 B"
        tamanho = self.tamanho_bytes
        for unidade in ['B', 'KB', 'MB', 'GB', 'TB']:
            if tamanho < 1024.0:
                return f"{tamanho:.2f} {unidade}"
            tamanho /= 1024.0
        return f"{tamanho:.2f} PB"
