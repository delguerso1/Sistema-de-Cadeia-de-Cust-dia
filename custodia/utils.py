import hashlib
import os
from pathlib import Path
from typing import List, Dict, Tuple
import mimetypes
from datetime import datetime


# Extensões de vídeo (mantido para informação, mas não é mais obrigatório)
EXTENSOES_VIDEO = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v', '.3gp', '.mpg', '.mpeg', '.ts', '.m2ts'}


def validar_arquivo_video(caminho_arquivo: str) -> bool:
    """Verifica se o arquivo é um vídeo baseado na extensão (informação apenas)"""
    extensao = Path(caminho_arquivo).suffix.lower()
    return extensao in EXTENSOES_VIDEO


def calcular_hash_arquivo(caminho_arquivo: Path) -> str:
    """Calcula o hash SHA-256 de um arquivo individual"""
    hash_sha256 = hashlib.sha256()
    try:
        with open(caminho_arquivo, 'rb') as f:
            # Lê em chunks de 4KB para arquivos grandes
            for chunk in iter(lambda: f.read(4096), b''):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    except Exception as e:
        raise Exception(f"Erro ao calcular hash do arquivo {caminho_arquivo}: {str(e)}")


def calcular_hash_pasta(caminho_pasta: str) -> Tuple[str, List[Dict]]:
    """
    Calcula o hash SHA-256 de uma pasta completa (recursivo)
    
    Retorna:
        - hash_final: Hash SHA-256 da pasta
        - lista_arquivos: Lista com informações de todos os arquivos
    """
    pasta_base = Path(caminho_pasta)
    
    if not pasta_base.exists():
        raise ValueError(f"Pasta não encontrada: {caminho_pasta}")
    
    if not pasta_base.is_dir():
        raise ValueError(f"Caminho não é uma pasta: {caminho_pasta}")
    
    hashes_arquivos = []
    lista_arquivos = []
    
    # Listar e ordenar arquivos recursivamente (inclui todas as subpastas)
    arquivos = sorted(pasta_base.rglob('*'))
    
    for arquivo in arquivos:
        if arquivo.is_file():
            try:
                # Calcular hash do conteúdo do arquivo
                hash_arquivo = calcular_hash_arquivo(arquivo)
                
                # Usar caminho relativo para preservar estrutura de pastas
                caminho_relativo = str(arquivo.relative_to(pasta_base))
                
                # Coletar informações do arquivo
                info_arquivo = coletar_info_arquivo(arquivo, pasta_base)
                info_arquivo['hash'] = hash_arquivo
                
                # Adicionar ao hash combinado
                hashes_arquivos.append(f"{caminho_relativo}:{hash_arquivo}")
                lista_arquivos.append(info_arquivo)
                
            except Exception as e:
                # Continua processando outros arquivos mesmo se um falhar
                print(f"Erro ao processar arquivo {arquivo}: {str(e)}")
                continue
    
    # Combinar todos os hashes
    hash_combinado = hashlib.sha256()
    hash_combinado.update(''.join(hashes_arquivos).encode('utf-8'))
    
    hash_final = hash_combinado.hexdigest()
    
    return hash_final, lista_arquivos


def combinar_hashes_entradas_rel_hash(entradas: List[str]) -> str:
    """
    Combina entradas 'caminho_relativo:hash' (lista já ordenada ou será ordenada aqui)
    no mesmo formato de calcular_hash_pasta.
    """
    if not entradas:
        return hashlib.sha256(b'').hexdigest()
    ordenado = sorted(entradas)
    h = hashlib.sha256()
    h.update(''.join(ordenado).encode('utf-8'))
    return h.hexdigest()


def combinar_hashes_lista_arquivos(lista_info: List[Dict]) -> str:
    """Agrega hashes a partir de dicionários com caminho_relativo e hash."""
    entradas = [f"{x['caminho_relativo']}:{x['hash']}" for x in lista_info]
    return combinar_hashes_entradas_rel_hash(entradas)


def calcular_hash_cadeia(hash_anterior_hex: str, hash_conteudo_novos_hex: str) -> str:
    """
    Hash final da cadeia: incorpora explicitamente o hash da versão anterior
    e o agregado desta versão (novos/alterados).
    """
    raw = f"{hash_anterior_hex}|{hash_conteudo_novos_hex}"
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()


def particionar_novos_ou_alterados(
    lista_atual: List[Dict],
    mapa_anterior: Dict[str, str],
) -> Tuple[List[Dict], List[Dict]]:
    """
    mapa_anterior: caminho_relativo -> hash_arquivo da versão anterior.
    Retorna (lista novos ou alterados, lista inalterados).
    """
    novos = []
    inalterados = []
    for info in lista_atual:
        rel = info['caminho_relativo']
        h = info['hash']
        if rel not in mapa_anterior or mapa_anterior[rel] != h:
            novos.append(info)
        else:
            inalterados.append(info)
    return novos, inalterados


def coletar_info_arquivo(arquivo: Path, pasta_base: Path) -> Dict:
    """
    Coleta informações detalhadas de um arquivo
    
    Retorna dicionário com:
    - nome_arquivo
    - caminho_completo
    - caminho_relativo
    - tamanho_bytes
    - data_modificacao
    - tipo_mime
    - extensao
    - eh_video
    """
    try:
        stat_info = arquivo.stat()
        
        caminho_relativo = str(arquivo.relative_to(pasta_base))
        extensao = arquivo.suffix.lower()
        
        # Detectar tipo MIME
        tipo_mime, _ = mimetypes.guess_type(str(arquivo))
        if not tipo_mime:
            tipo_mime = 'application/octet-stream'
        
        info = {
            'nome_arquivo': arquivo.name,
            'caminho_completo': str(arquivo),
            'caminho_relativo': caminho_relativo,
            'tamanho_bytes': stat_info.st_size,
            'data_modificacao': datetime.fromtimestamp(stat_info.st_mtime),
            'tipo_mime': tipo_mime,
            'extensao': extensao,
            'eh_video': validar_arquivo_video(str(arquivo)),
        }
        
        return info
        
    except Exception as e:
        raise Exception(f"Erro ao coletar informações do arquivo {arquivo}: {str(e)}")


def formatar_tamanho(tamanho_bytes: int) -> str:
    """Formata tamanho em bytes para formato legível (KB, MB, GB, etc.)"""
    if tamanho_bytes == 0:
        return "0 B"
    
    tamanho = float(tamanho_bytes)
    for unidade in ['B', 'KB', 'MB', 'GB', 'TB']:
        if tamanho < 1024.0:
            return f"{tamanho:.2f} {unidade}"
        tamanho /= 1024.0
    return f"{tamanho:.2f} PB"


def gerar_numero_documento(caso_numero: str) -> str:
    """
    Gera um número de documento único baseado no número do caso
    Formato: CUST-{NUMERO_CASO}-{TIMESTAMP}
    """
    from datetime import datetime
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    # Remove caracteres especiais do número do caso
    caso_limpo = ''.join(c for c in caso_numero if c.isalnum() or c in ['-', '_'])
    return f"CUST-{caso_limpo}-{timestamp}"


def validar_pasta_arquivos(caminho_pasta: str) -> Tuple[bool, str]:
    """
    Valida se a pasta contém arquivos (qualquer tipo de arquivo)
    
    Retorna:
        - (True, "") se válida
        - (False, mensagem_erro) se inválida
    """
    try:
        pasta = Path(caminho_pasta)
        
        if not pasta.exists():
            return False, "Pasta não encontrada"
        
        if not pasta.is_dir():
            return False, "Caminho não é uma pasta"
        
        # Verificar se há pelo menos um arquivo (qualquer tipo)
        arquivos = list(pasta.rglob('*'))
        arquivos_encontrados = [f for f in arquivos if f.is_file()]
        
        if not arquivos_encontrados:
            return False, "Nenhum arquivo encontrado na pasta"
        
        return True, ""
        
    except Exception as e:
        return False, f"Erro ao validar pasta: {str(e)}"
