"""
ORGANIZAR - Apenas organiza transcrição corrigida
Pega arquivo TXT corrigido e gera TXT organizado por tópicos
"""
import sys
import os
import re
from pathlib import Path
from utils import (
    segmentar_por_topicos,
    organizar_por_topicos,
    formatar_timestamp
)

def extrair_segmentos_do_arquivo(caminho_arquivo: str) -> list:
    """
    Extrai segmentos de arquivo corrigido
    Formato: [HH:MM:SS] Speaker X: texto
    """
    segmentos = []
    
    with open(caminho_arquivo, 'r', encoding='utf-8') as f:
        linhas = f.readlines()
    
    timestamp_pattern = r'\[(\d+):(\d+):(\d+)\]'
    speaker_pattern = r'Speaker\s+(\d+)'
    
    segmento_atual = None
    dentro_da_secao_transcricao = False
    
    for linha in linhas:
        linha = linha.strip()
        
        # Detecta início da seção de transcrição
        if 'TRANSCRIÇÃO CORRIGIDA' in linha or 'TRANSCRIÇÃO' in linha:
            dentro_da_secao_transcricao = True
            continue
        
        if not dentro_da_secao_transcricao:
            continue
            
        if not linha or linha.startswith('=') or linha.startswith('📁') or linha.startswith('🤖') or linha.startswith('📊') or linha.startswith('🎤'):
            continue
        
        # Detecta timestamp e speaker
        match_timestamp = re.search(timestamp_pattern, linha)
        match_speaker = re.search(speaker_pattern, linha, re.IGNORECASE)
        
        if match_timestamp and match_speaker:
            # Salva segmento anterior
            if segmento_atual:
                segmentos.append(segmento_atual)
            
            # Cria novo segmento
            horas, minutos, segundos = map(int, match_timestamp.groups())
            timestamp_segundos = horas * 3600 + minutos * 60 + segundos
            speaker = f"Speaker {match_speaker.group(1)}"
            
            # Extrai texto
            partes = linha.split(':', 2)
            if len(partes) >= 3:
                texto = partes[2].strip()
            else:
                texto = ''
            
            segmento_atual = {
                'start': timestamp_segundos,
                'end': timestamp_segundos + 10,
                'speaker': speaker,
                'text': texto
            }
        elif segmento_atual and linha:
            # Continua texto
            if not segmento_atual['text']:
                segmento_atual['text'] = linha
            else:
                segmento_atual['text'] += ' ' + linha
    
    # Adiciona último segmento
    if segmento_atual:
        segmentos.append(segmento_atual)
    
    # Ajusta timestamps
    for i, seg in enumerate(segmentos):
        if i > 0:
            seg['start'] = segmentos[i-1]['end']
        if i < len(segmentos) - 1:
            seg['end'] = seg['start'] + max(5, len(seg['text'].split()) * 0.5)
    
    return segmentos

def organizar(caminho_arquivo_corrigido: str, max_chars_bloco: int = 600):
    """
    ORGANIZA transcrição corrigida por tópicos
    
    Args:
        caminho_arquivo_corrigido: Caminho do arquivo TXT corrigido
        max_chars_bloco: Tamanho máximo de bloco antes de dividir
    """
    print("="*70)
    print("📑 ORGANIZAR - Organização por Tópicos")
    print("="*70)
    print()
    
    # Tenta encontrar arquivo (pode estar em output/ ou na raiz)
    if not os.path.exists(caminho_arquivo_corrigido):
        caminho_alternativo = f"output/{os.path.basename(caminho_arquivo_corrigido)}"
        if os.path.exists(caminho_alternativo):
            caminho_arquivo_corrigido = caminho_alternativo
        else:
            print(f"❌ Arquivo não encontrado: {caminho_arquivo_corrigido}")
            return None
    
    print(f"📁 Arquivo corrigido: {os.path.basename(caminho_arquivo_corrigido)}")
    print()
    
    # Lê arquivo corrigido
    print("📖 Lendo transcrição corrigida...")
    segmentos = extrair_segmentos_do_arquivo(caminho_arquivo_corrigido)
    print(f"✓ {len(segmentos)} segmentos carregados")
    
    # Segmenta por tópicos
    print("\n📑 Organizando por tópicos...")
    print("   ✓ Segmentando por tópicos...")
    segmentos = segmentar_por_topicos(segmentos, max_chars_bloco)
    
    # Organiza por tópicos
    print("   ✓ Agrupando por tópicos...")
    transcricao_organizada = organizar_por_topicos(segmentos)
    
    # Salva arquivo organizado
    os.makedirs("output", exist_ok=True)
    nome_base = Path(caminho_arquivo_corrigido).stem.replace('_corrigido', '')
    arquivo_organizado = f"output/{nome_base}_organizado.txt"
    
    # Lê metadados do arquivo corrigido
    metadados = {}
    with open(caminho_arquivo_corrigido, 'r', encoding='utf-8') as f:
        for linha in f:
            if '📁 Arquivo original:' in linha or '📁 Arquivo:' in linha:
                metadados['arquivo'] = linha.split(':', 1)[-1].strip()
            elif '🤖 Modelo:' in linha:
                metadados['modelo'] = linha.split(':', 1)[-1].strip()
            elif '🔧 Modo limpeza:' in linha:
                metadados['modo_limpeza'] = linha.split(':', 1)[-1].strip()
    
    # Salva arquivo organizado
    with open(arquivo_organizado, 'w', encoding='utf-8') as f:
        f.write("="*70 + "\n")
        f.write("📑 TRANSCRIÇÃO ORGANIZADA POR TÓPICOS\n")
        f.write("="*70 + "\n\n")
        f.write(f"📁 Arquivo original: {metadados.get('arquivo', os.path.basename(caminho_arquivo_corrigido))}\n")
        f.write(f"🤖 Modelo: {metadados.get('modelo', 'N/A')}\n")
        f.write(f"🔧 Modo limpeza: {metadados.get('modo_limpeza', 'N/A')}\n")
        f.write(f"📊 Segmentos: {len(segmentos)}\n")
        f.write(f"🎤 Speakers: {len(set(s.get('speaker', 'Speaker 1') for s in segmentos))}\n")
        f.write(f"📑 Tópicos: {len(transcricao_organizada)}\n")
        f.write("\n" + "="*70 + "\n")
        f.write("TRANSCRIÇÃO ORGANIZADA POR TÓPICOS\n")
        f.write("="*70 + "\n\n")
        
        # Ordena tópicos por ordem de aparição
        topicos_ordenados = sorted(transcricao_organizada.keys(), 
                                   key=lambda t: min(s['start'] for s in transcricao_organizada[t]))
        
        for topico in topicos_ordenados:
            segmentos_topico = transcricao_organizada[topico]
            
            f.write("\n" + "="*70 + "\n")
            f.write(f"📑 {topico.upper()}\n")
            f.write("="*70 + "\n\n")
            
            speaker_anterior = None
            for seg in segmentos_topico:
                if speaker_anterior and speaker_anterior != seg.get('speaker', 'Speaker 1'):
                    f.write("\n")
                
                timestamp = formatar_timestamp(seg['start'])
                speaker = seg.get('speaker', 'Speaker 1')
                f.write(f"[{timestamp}] {speaker}:\n")
                f.write(f"{seg['text']}\n\n")
                
                speaker_anterior = speaker
            
            f.write("\n")
    
    print("\n" + "="*70)
    print("✅ ORGANIZAÇÃO CONCLUÍDA")
    print("="*70)
    print(f"📄 Arquivo organizado: {arquivo_organizado}")
    print(f"📊 Segmentos: {len(segmentos)}")
    print(f"🎤 Speakers: {len(set(s.get('speaker', 'Speaker 1') for s in segmentos))}")
    print(f"📑 Tópicos: {len(transcricao_organizada)}")
    print("="*70)
    
    return arquivo_organizado

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("="*70)
        print("📑 ORGANIZAR - Organização por Tópicos")
        print("="*70)
        print("\nUso: python organizar.py <arquivo_corrigido.txt>")
        print("\nExemplos:")
        print('  python organizar.py "output/video_corrigido.txt"')
        print("\nSaída:")
        print("  Gera: output/video_organizado.txt")
        sys.exit(1)
    
    arquivo = sys.argv[1].strip('"\'')
    
    organizar(arquivo)
