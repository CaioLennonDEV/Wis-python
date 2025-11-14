"""
CORRIGIR - Apenas corrige transcrição bruta
Pega arquivo TXT bruto e gera TXT corrigido
"""
import sys
import os
import re
from pathlib import Path
from utils import normalizar_termos, limpar_vicios_fala

def extrair_segmentos_do_arquivo(caminho_arquivo: str) -> list:
    """
    Extrai segmentos de arquivo bruto
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
        linha_original = linha
        linha = linha.strip()
        
        # Detecta início da seção de transcrição
        if 'TRANSCRIÇÃO BRUTA' in linha or 'TRANSCRIÇÃO' in linha:
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

def corrigir(caminho_arquivo_bruto: str, modo_limpeza: str = "medio"):
    """
    CORRIGE transcrição bruta
    
    Args:
        caminho_arquivo_bruto: Caminho do arquivo TXT bruto
        modo_limpeza: "leve", "medio" ou "agressivo"
    """
    print("="*70)
    print("🔧 CORRIGIR - Correção de Transcrição")
    print("="*70)
    print()
    
    # Tenta encontrar arquivo (pode estar em output/ ou na raiz)
    if not os.path.exists(caminho_arquivo_bruto):
        caminho_alternativo = f"output/{os.path.basename(caminho_arquivo_bruto)}"
        if os.path.exists(caminho_alternativo):
            caminho_arquivo_bruto = caminho_alternativo
        else:
            print(f"❌ Arquivo não encontrado: {caminho_arquivo_bruto}")
            return None
    
    print(f"📁 Arquivo bruto: {os.path.basename(caminho_arquivo_bruto)}")
    print(f"🔧 Modo limpeza: {modo_limpeza}")
    print()
    
    # Lê arquivo bruto
    print("📖 Lendo transcrição bruta...")
    segmentos = extrair_segmentos_do_arquivo(caminho_arquivo_bruto)
    print(f"✓ {len(segmentos)} segmentos carregados")
    
    # Aplica correções
    print("\n🔧 Aplicando correções...")
    
    # 1. Normalização de termos
    print("   ✓ Normalizando termos técnicos...")
    for seg in segmentos:
        seg['text'] = normalizar_termos(seg['text'])
    
    # 2. Limpeza de vícios de fala
    print(f"   ✓ Limpando vícios de fala (modo: {modo_limpeza})...")
    for seg in segmentos:
        seg['text'] = limpar_vicios_fala(seg['text'], modo_limpeza)
    
    # Salva arquivo corrigido
    os.makedirs("output", exist_ok=True)
    nome_base = Path(caminho_arquivo_bruto).stem.replace('_transcricao_bruta', '')
    arquivo_corrigido = f"output/{nome_base}_corrigido.txt"
    
    # Lê metadados do arquivo bruto
    metadados = {}
    with open(caminho_arquivo_bruto, 'r', encoding='utf-8') as f:
        for linha in f:
            if '📁 Arquivo:' in linha:
                metadados['arquivo'] = linha.split(':', 1)[-1].strip()
            elif '🤖 Modelo:' in linha:
                metadados['modelo'] = linha.split(':', 1)[-1].strip()
            elif '🎤 PyAnnote:' in linha:
                metadados['pyannote'] = 'Sim' in linha
    
    # Salva arquivo corrigido
    with open(arquivo_corrigido, 'w', encoding='utf-8') as f:
        f.write("="*70 + "\n")
        f.write("🔧 TRANSCRIÇÃO CORRIGIDA\n")
        f.write("="*70 + "\n\n")
        f.write(f"📁 Arquivo original: {metadados.get('arquivo', os.path.basename(caminho_arquivo_bruto))}\n")
        f.write(f"🤖 Modelo: {metadados.get('modelo', 'N/A')}\n")
        f.write(f"🔧 Modo limpeza: {modo_limpeza}\n")
        f.write(f"📊 Segmentos: {len(segmentos)}\n")
        f.write(f"🎤 Speakers: {len(set(s.get('speaker', 'Speaker 1') for s in segmentos))}\n")
        f.write("\n" + "="*70 + "\n")
        f.write("TRANSCRIÇÃO CORRIGIDA\n")
        f.write("="*70 + "\n\n")
        
        from utils import formatar_timestamp
        speaker_anterior = None
        for seg in segmentos:
            if speaker_anterior and speaker_anterior != seg.get('speaker', 'Speaker 1'):
                f.write("\n")
            
            timestamp = formatar_timestamp(seg['start'])
            speaker = seg.get('speaker', 'Speaker 1')
            f.write(f"[{timestamp}] {speaker}:\n")
            f.write(f"{seg['text']}\n\n")
            
            speaker_anterior = speaker
    
    print("\n" + "="*70)
    print("✅ CORREÇÃO CONCLUÍDA")
    print("="*70)
    print(f"📄 Arquivo corrigido: {arquivo_corrigido}")
    print(f"📊 Segmentos: {len(segmentos)}")
    print(f"🎤 Speakers: {len(set(s.get('speaker', 'Speaker 1') for s in segmentos))}")
    print("\n💡 Próximo passo: Organize o arquivo com:")
    print(f"   python organizar.py \"{arquivo_corrigido}\"")
    print("="*70)
    
    return arquivo_corrigido

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("="*70)
        print("🔧 CORRIGIR - Correção de Transcrição")
        print("="*70)
        print("\nUso: python corrigir.py <arquivo_bruto.txt> [modo]")
        print("\nModos de limpeza:")
        print("  leve      - Apenas limpeza básica")
        print("  medio     - Remove vícios de fala comuns ⭐ RECOMENDADO")
        print("  agressivo - Limpeza completa + ajustes de fluidez")
        print("\nExemplos:")
        print('  python corrigir.py "output/video_transcricao_bruta.txt"')
        print('  python corrigir.py "output/video_transcricao_bruta.txt" agressivo')
        print("\nSaída:")
        print("  Gera: output/video_corrigido.txt")
        sys.exit(1)
    
    arquivo = sys.argv[1].strip('"\'')
    modo = sys.argv[2] if len(sys.argv) > 2 else "medio"
    
    corrigir(arquivo, modo)
