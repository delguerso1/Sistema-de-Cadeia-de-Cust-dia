# Sistema de Cadeia de Custódia para Vídeos de Monitoramento

## 1. Visão Geral

Sistema web desenvolvido para garantir a integridade e rastreabilidade de vídeos de monitoramento através da geração de códigos hash e documentação em PDF, atendendo aos requisitos legais da cadeia de custódia em investigações policiais.

## 2. Objetivos

- Gerar código hash (SHA-256) para pastas contendo vídeos de monitoramento
- Criar documento PDF com todas as informações relevantes da cadeia de custódia
- Armazenar registros em banco de dados para auditoria e consulta
- Garantir rastreabilidade completa desde a coleta até o armazenamento

## 3. Arquitetura da Aplicação

### 3.1. Tecnologias Recomendadas

**Frontend:**
- HTML5, CSS3, JavaScript (Vanilla ou framework leve como Vue.js/React)
- Interface simples e intuitiva para preenchimento de formulários

**Backend:**
- Python com Flask ou FastAPI (recomendado para simplicidade)
- Alternativa: Node.js com Express

**Banco de Dados:**
- PostgreSQL (recomendado para robustez e integridade)
- Alternativa: SQLite (para instalação simples)

**Bibliotecas Principais:**
- `hashlib` (Python) - Geração de hash SHA-256
- `reportlab` ou `weasyprint` (Python) - Geração de PDF
- `os` / `pathlib` - Manipulação de arquivos e pastas
- `datetime` - Manipulação de datas e horários

### 3.2. Estrutura de Pastas

```
sistema-custodia/
├── app/
│   ├── __init__.py
│   ├── routes.py          # Rotas da aplicação
│   ├── models.py          # Modelos do banco de dados
│   ├── hash_generator.py  # Lógica de geração de hash
│   ├── pdf_generator.py   # Geração de documentos PDF
│   └── utils.py           # Funções auxiliares
├── templates/
│   ├── index.html         # Página principal
│   └── resultado.html     # Página de resultado
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── main.js
├── uploads/               # Pasta temporária para uploads
├── pdfs/                  # PDFs gerados
├── database/
│   └── init_db.py         # Script de inicialização do BD
├── requirements.txt
├── config.py              # Configurações
└── app.py                 # Arquivo principal
```

## 4. Funcionalidades Principais

### 4.1. Cadastro de Informações do Policial

**Campos Obrigatórios:**
- Nome completo
- Matrícula/Registro
- Cargo/Função
- Delegacia/Unidade
- Data e hora da coleta no local do crime
- Local do crime (endereço)
- Número do procedimento/inquérito
- Observações (opcional)

### 4.2. Upload e Seleção de Pasta

- Interface para seleção da pasta contendo os vídeos
- Validação de tipos de arquivo (formats de vídeo comuns: .mp4, .avi, .mov, .mkv, etc.)
- Exibição prévia dos arquivos encontrados na pasta

### 4.3. Geração de Hash

**Algoritmo:** SHA-256

**Processo:**
1. Listar todos os arquivos na pasta selecionada **e em todas as subpastas (busca recursiva)**
2. Ordenar arquivos por caminho relativo (para garantir consistência)
3. Calcular hash individual de cada arquivo
4. Combinar hashes incluindo o caminho relativo (preserva estrutura de pastas)
5. Gerar hash final da pasta (hash do hash combinado)

**Exemplo de Implementação:**
```python
import hashlib
import os
from pathlib import Path

def calcular_hash_pasta(caminho_pasta):
    hashes_arquivos = []
    pasta_base = Path(caminho_pasta)
    
    # Listar e ordenar arquivos recursivamente (inclui todas as subpastas)
    arquivos = sorted(pasta_base.rglob('*'))
    
    for arquivo in arquivos:
        if arquivo.is_file():
            # Calcular hash do conteúdo do arquivo
            hash_arquivo = hashlib.sha256()
            with open(arquivo, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    hash_arquivo.update(chunk)
            
            # Usar caminho relativo para preservar estrutura de pastas
            caminho_relativo = arquivo.relative_to(pasta_base)
            hashes_arquivos.append(f"{caminho_relativo}:{hash_arquivo.hexdigest()}")
    
    # Combinar todos os hashes
    hash_combinado = hashlib.sha256()
    hash_combinado.update(''.join(hashes_arquivos).encode())
    
    return hash_combinado.hexdigest()
```

### 4.4. Coleta de Informações dos Arquivos

Para cada arquivo na pasta **e subpastas (busca recursiva)**, coletar:
- Nome do arquivo
- Caminho completo
- Tamanho em bytes e formato legível (MB/GB)
- Data de modificação
- Tipo MIME (se disponível)
- Duração do vídeo (se possível extrair)

### 4.5. Geração de PDF

**Conteúdo do Documento PDF:**

1. **Cabeçalho:**
   - Título: "DOCUMENTO DE CADEIA DE CUSTÓDIA - VÍDEOS DE MONITORAMENTO"
   - Número do documento (gerado automaticamente)
   - Data e hora de geração

2. **Informações do Policial Responsável:**
   - Nome completo
   - Matrícula/Registro
   - Cargo/Função
   - Delegacia/Unidade

3. **Informações do Caso:**
   - Número do procedimento/inquérito
   - Local do crime
   - Data e hora da coleta no local

4. **Informações Técnicas:**
   - Código Hash SHA-256 da pasta (em destaque)
   - Data e hora da geração do hash
   - Caminho completo da pasta armazenada
   - Nome do HD externo (se aplicável)

5. **Inventário de Arquivos:**
   - Tabela com:
     - Nome do arquivo
     - Tamanho
     - Data de modificação
     - Hash individual (opcional, para arquivos críticos)

6. **Estatísticas:**
   - Total de arquivos
   - Tamanho total da pasta
   - Formato dos arquivos

7. **Rodapé:**
   - Assinatura digital (hash do documento)
   - QR Code com o hash principal (para verificação rápida)
   - Observações adicionais

### 4.6. Banco de Dados

**Estrutura de Tabelas:**

**Tabela: `custodias`**
```sql
CREATE TABLE custodias (
    id SERIAL PRIMARY KEY,
    numero_documento VARCHAR(50) UNIQUE NOT NULL,
    hash_pasta VARCHAR(64) UNIQUE NOT NULL,
    data_criacao TIMESTAMP NOT NULL,
    caminho_pasta TEXT NOT NULL,
    tamanho_total BIGINT,
    total_arquivos INTEGER,
    observacoes TEXT,
    pdf_gerado BOOLEAN DEFAULT FALSE,
    caminho_pdf TEXT
);
```

**Tabela: `policiais`**
```sql
CREATE TABLE policiais (
    id SERIAL PRIMARY KEY,
    nome_completo VARCHAR(255) NOT NULL,
    matricula VARCHAR(50) UNIQUE NOT NULL,
    cargo VARCHAR(100),
    delegacia VARCHAR(255),
    ativo BOOLEAN DEFAULT TRUE
);
```

**Tabela: `casos`**
```sql
CREATE TABLE casos (
    id SERIAL PRIMARY KEY,
    numero_procedimento VARCHAR(100) UNIQUE NOT NULL,
    local_crime TEXT,
    data_coleta TIMESTAMP,
    observacoes TEXT
);
```

**Tabela: `custodia_policial`** (Relacionamento)
```sql
CREATE TABLE custodia_policial (
    id SERIAL PRIMARY KEY,
    custodia_id INTEGER REFERENCES custodias(id),
    policial_id INTEGER REFERENCES policiais(id),
    data_entrega TIMESTAMP NOT NULL
);
```

**Tabela: `custodia_caso`** (Relacionamento)
```sql
CREATE TABLE custodia_caso (
    id SERIAL PRIMARY KEY,
    custodia_id INTEGER REFERENCES custodias(id),
    caso_id INTEGER REFERENCES casos(id)
);
```

**Tabela: `arquivos`**
```sql
CREATE TABLE arquivos (
    id SERIAL PRIMARY KEY,
    custodia_id INTEGER REFERENCES custodias(id),
    nome_arquivo VARCHAR(255) NOT NULL,
    caminho_completo TEXT NOT NULL,
    tamanho_bytes BIGINT,
    data_modificacao TIMESTAMP,
    hash_arquivo VARCHAR(64),
    tipo_mime VARCHAR(100),
    duracao_segundos INTEGER
);
```

## 5. Fluxo de Trabalho

1. **Acesso ao Sistema:**
   - Policial acessa a aplicação web
   - Preenche formulário com suas informações (ou seleciona perfil se já cadastrado)

2. **Informações do Caso:**
   - Preenche dados do procedimento/inquérito
   - Informa local e data da coleta

3. **Seleção da Pasta:**
   - Seleciona a pasta contendo os vídeos
   - Sistema valida e lista os arquivos encontrados

4. **Geração do Hash:**
   - Sistema calcula hash SHA-256 da pasta
   - Processo pode levar alguns minutos dependendo do tamanho

5. **Armazenamento:**
   - Dados são salvos no banco de dados
   - Hash é armazenado de forma permanente

6. **Geração do PDF:**
   - Sistema gera documento PDF com todas as informações
   - PDF é salvo em pasta segura
   - Caminho do PDF é registrado no banco

7. **Resultado:**
   - Exibição do hash gerado
   - Link para download do PDF
   - Número do documento gerado
   - Opção de impressão

## 6. Recursos de Segurança

### 6.1. Integridade dos Dados
- Hash SHA-256 garante que qualquer alteração nos arquivos será detectada
- Hash é calculado de forma determinística (mesma pasta = mesmo hash)

### 6.2. Auditoria
- Todas as operações são registradas com timestamp
- Histórico completo no banco de dados
- Logs de acesso e modificações

### 6.3. Validação
- Verificação periódica de integridade (recalcular hash e comparar)
- Sistema de alertas para possíveis violações

## 7. Funcionalidades Adicionais Recomendadas

### 7.1. Verificação de Integridade
- Interface para verificar se o hash de uma pasta ainda corresponde ao registrado
- Relatório de verificação

### 7.2. Consulta e Relatórios
- Busca por número de procedimento
- Busca por hash
- Busca por policial
- Relatórios por período

### 7.3. Backup e Exportação
- Exportação de dados para formato JSON/XML
- Backup automático do banco de dados
- Sincronização com sistemas externos (se necessário)

### 7.4. Autenticação e Autorização
- Sistema de login para policiais
- Níveis de acesso (operador, supervisor, administrador)
- Registro de todas as ações realizadas

## 8. Considerações Legais e Técnicas

### 8.1. Validade Legal
- Hash SHA-256 é amplamente aceito em processos judiciais
- Documentação completa garante rastreabilidade
- Timestamps precisos são essenciais

### 8.2. Armazenamento
- HDs externos devem ser mantidos em local seguro
- Recomenda-se manter cópias de backup
- PDFs devem ser arquivados fisicamente e digitalmente

### 8.3. Manutenção
- Sistema deve ser mantido atualizado
- Backups regulares do banco de dados
- Monitoramento de integridade dos arquivos

## 9. Requisitos de Sistema

### 9.1. Servidor
- Python 3.8+ ou Node.js 16+
- PostgreSQL 12+ ou SQLite 3
- Espaço em disco adequado para armazenamento
- Processamento suficiente para cálculo de hash de grandes volumes

### 9.2. Cliente
- Navegador moderno (Chrome, Firefox, Edge)
- JavaScript habilitado
- Conexão estável para upload de arquivos grandes

## 10. Implementação Inicial Simplificada

Para uma versão inicial simples, pode-se usar:

- **Backend:** Flask (Python)
- **Banco:** SQLite (não requer servidor separado)
- **PDF:** ReportLab
- **Frontend:** HTML/CSS/JavaScript puro

Esta configuração permite:
- Instalação rápida
- Funcionamento offline
- Fácil manutenção
- Escalabilidade futura para PostgreSQL

## 11. Exemplo de Uso

1. Policial acessa: `http://localhost:5000`
2. Preenche formulário:
   - Nome: "João Silva"
   - Matrícula: "12345"
   - Procedimento: "INQ 001/2024"
   - Local: "Rua das Flores, 123"
3. Seleciona pasta: `D:\Videos\Caso_001\`
4. Clica em "Gerar Cadeia de Custódia"
5. Sistema processa e gera:
   - Hash: `a3f5b8c9d2e1f4a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0`
   - PDF: `custodia_INQ001_2024_20240115_143022.pdf`
6. Policial baixa o PDF e arquiva junto com o HD externo

## 12. Próximos Passos

1. Desenvolvimento do backend (Flask/FastAPI)
2. Criação do banco de dados
3. Implementação da geração de hash
4. Desenvolvimento do gerador de PDF
5. Interface web
6. Testes com dados reais
7. Deploy em servidor seguro
8. Treinamento dos usuários

---

**Nota Importante:** Este sistema é uma ferramenta de apoio à cadeia de custódia. Recomenda-se consulta com equipe jurídica para garantir conformidade total com requisitos legais específicos da jurisdição.

