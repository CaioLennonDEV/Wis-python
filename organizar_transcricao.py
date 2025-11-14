"""
Script para organizar transcrições existentes
Aplica todas as melhorias de organização em arquivos já transcritos
"""
import sys
import os
import re
from pathlib import Path
from whisper_avancado import (
    normalizar_termos,
    limpar_vicios_fala,
    segmentar_por_topicos,
    organizar_por_topicos,
    salvar_transcricao_organizada,
    formatar_timestamp
)

def processar_transcricao_existente(caminho_arquivo: str,
                                    modo_limpeza: str = "medio",
                                    salvar_backup: bool = True):
    """
    Processa arquivo de transcrição existente e aplica todas as melhorias
    """
    if not os.path.exists(caminho_arquivo):
        print(f"❌ Arquivo não encontrado: {caminho_arquivo}")
        return None
    
    print("="*70)
    print("🔧 ORGANIZAÇÃO DE TRANSCRIÇÃO EXISTENTE")
    print("="*70)
    print()
    print(f"📁 Arquivo: {caminho_arquivo}")
    print(f"🔧 Modo limpeza: {modo_limpeza}")
    print()
    
    # Lê arquivo original
    with open(caminho_arquivo, 'r', encoding='utf-8') as f:
        conteudo_original = f.read()
    
    # Cria backup se solicitado
    if salvar_backup:
        backup_path = f"{caminho_arquivo}.backup"
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(conteudo_original)
        print(f"💾 Backup criado: {backup_path}")
    
    # Extrai segmentos do arquivo
    print("📖 Extraindo segmentos...")
    segmentos = extrair_segmentos_do_arquivo(conteudo_original)
    print(f"✓ {len(segmentos)} segmentos extraídos")
    
    # Processa segmentos
    print("\n🔧 Aplicando melhorias...")
    
    # 1. Normalização de termos
    print("   ✓ Normalizando termos técnicos...")
    for seg in segmentos:
        seg['text'] = normalizar_termos(seg['text'])
    
    # 2. Limpeza de vícios de fala
    print(f"   ✓ Limpando vícios de fala (modo: {modo_limpeza})...")
    for seg in segmentos:
        seg['text'] = limpar_vicios_fala(seg['text'], modo_limpeza)
    
    # 3. Segmentação por tópicos
    print("   ✓ Segmentando por tópicos...")
    segmentos = segmentar_por_topicos(segmentos, max_chars=600)
    
    # 4. Organiza por tópicos
    print("   ✓ Organizando por tópicos...")
    transcricao_organizada = organizar_por_topicos(segmentos)
    
    # Salva
    caminho_saida = caminho_arquivo.replace('.txt', '_organizado.txt')
    salvar_transcricao_organizada(caminho_saida, transcricao_organizada, {
        'arquivo': os.path.basename(caminho_arquivo),
        'modelo': 'N/A (arquivo existente)',
        'modo_limpeza': modo_limpeza,
        'pyannote': False,
        'llm': False
    })
    
    print("\n" + "="*70)
    print("✅ ORGANIZAÇÃO CONCLUÍDA")
    print("="*70)
    print(f"📄 Arquivo salvo: {caminho_saida}")
    print(f"📊 Segmentos: {len(segmentos)}")
    print(f"🎤 Speakers: {len(set(s.get('speaker', 'Speaker 1') for s in segmentos))}")
    print(f"📑 Tópicos: {len(transcricao_organizada)}")
    print("="*70)
    
    return caminho_saida

def extrair_segmentos_do_arquivo(conteudo: str) -> list:
    """
    Extrai segmentos de um arquivo de transcrição existente
    Formato esperado: [HH:MM:SS] Speaker X: texto
    """
    segmentos = []
    linhas = conteudo.split('\n')
    
    timestamp_pattern = r'\[(\d+):(\d+):(\d+)\]'
    speaker_pattern = r'Speaker\s+(\d+)'
    
    segmento_atual = None
    
    for linha in linhas:
        linha = linha.strip()
        if not linha:
            continue
        
        # Detecta timestamp e speaker
        match_timestamp = re.search(timestamp_pattern, linha)
        match_speaker = re.search(speaker_pattern, linha, re.IGNORECASE)
        
        if match_timestamp and match_speaker:
            # Salva segmento anterior se existir
            if segmento_atual:
                segmentos.append(segmento_atual)
            
            # Cria novo segmento
            horas, minutos, segundos = map(int, match_timestamp.groups())
            timestamp_segundos = horas * 3600 + minutos * 60 + segundos
            speaker = f"Speaker {match_speaker.group(1)}"
            
            # Extrai texto (tudo após o speaker)
            texto = linha.split(':', 1)[-1].strip() if ':' in linha else ''
            
            segmento_atual = {
                'start': timestamp_segundos,
                'end': timestamp_segundos + 10,  # Estimativa
                'speaker': speaker,
                'text': texto
            }
        elif segmento_atual and linha:
            # Continua texto do segmento atual
            if segmento_atual['text']:
                segmento_atual['text'] += ' ' + linha
            else:
                segmento_atual['text'] = linha
    
    # Adiciona último segmento
    if segmento_atual:
        segmentos.append(segmento_atual)
    
    # Ajusta timestamps baseado em posição
    for i, seg in enumerate(segmentos):
        if i > 0:
            seg['start'] = segmentos[i-1]['end']
        if i < len(segmentos) - 1:
            # Estima duração baseada no tamanho do texto
            seg['end'] = seg['start'] + max(5, len(seg['text'].split()) * 0.5)
    
    return segmentos

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("="*70)
        print("🔧 ORGANIZAÇÃO DE TRANSCRIÇÃO EXISTENTE")
        print("="*70)
        print("\nUso: python organizar_transcricao.py <arquivo.txt> [modo]")
        print("\nModos de limpeza:")
        print("  leve      - Apenas limpeza básica")
        print("  medio     - Limpeza de vícios de fala ⭐ RECOMENDADO")
        print("  agressivo - Limpeza completa + ajustes de fluidez")
        print("\nExemplos:")
        print('  python organizar_transcricao.py "transcricao.txt"')
        print('  python organizar_transcricao.py "transcricao.txt" agressivo')
        sys.exit(1)
    
    arquivo = sys.argv[1].strip('"\'')
    modo = sys.argv[2] if len(sys.argv) > 2 else "medio"
    
    processar_transcricao_existente(arquivo, modo)

