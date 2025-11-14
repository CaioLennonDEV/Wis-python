"""
Whisper com Separação de Speakers (Diarização)
Identifica quem está falando em cada momento
"""
import whisper
import os
import sys
import time
import torch
import re
from pathlib import Path
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings("ignore")

def formatar_timestamp(segundos):
    """Converte segundos em formato HH:MM:SS"""
    return str(timedelta(seconds=int(segundos)))

def detectar_mudancas_speaker_simples(segments, threshold_pausa=3.0, threshold_energia=0.5):
    """
    Detecta mudanças de speaker baseado em:
    1. Pausas longas (>3s geralmente indica mudança)
    2. Mudanças de energia/volume
    3. Padrões de fala
    """
    if not segments:
        return []
    
    speakers = []
    speaker_atual = 1
    
    for i, seg in enumerate(segments):
        if i == 0:
            speakers.append({
                'speaker': f'Speaker {speaker_atual}',
                'start': seg['start'],
                'end': seg['end'],
                'text': seg['text'].strip()
            })
        else:
            # Calcula pausa entre segmentos
            pausa = seg['start'] - segments[i-1]['end']
            
            # Detecta mudança de speaker
            mudou_speaker = False
            
            # Critério 1: Pausa longa
            if pausa > threshold_pausa:
                mudou_speaker = True
                speaker_atual += 1
            
            # Critério 2: Mudança brusca de probabilidade de fala
            elif 'no_speech_prob' in seg and 'no_speech_prob' in segments[i-1]:
                diff_prob = abs(seg['no_speech_prob'] - segments[i-1]['no_speech_prob'])
                if diff_prob > threshold_energia and pausa > 1.5:
                    mudou_speaker = True
                    speaker_atual += 1
            
            speakers.append({
                'speaker': f'Speaker {speaker_atual}',
                'start': seg['start'],
                'end': seg['end'],
                'text': seg['text'].strip(),
                'pausa_anterior': pausa
            })
    
    return speakers

def agrupar_por_speaker(speaker_segments):
    """
    Agrupa segmentos consecutivos do mesmo speaker
    """
    if not speaker_segments:
        return []
    
    agrupados = []
    grupo_atual = {
        'speaker': speaker_segments[0]['speaker'],
        'start': speaker_segments[0]['start'],
        'end': speaker_segments[0]['end'],
        'text': speaker_segments[0]['text']
    }
    
    for i in range(1, len(speaker_segments)):
        seg = speaker_segments[i]
        
        # Se é o mesmo speaker e pausa curta, agrupa
        if (seg['speaker'] == grupo_atual['speaker'] and 
            seg.get('pausa_anterior', 0) < 2.0):
            grupo_atual['end'] = seg['end']
            grupo_atual['text'] += ' ' + seg['text']
        else:
            # Salva grupo atual e inicia novo
            agrupados.append(grupo_atual)
            grupo_atual = {
                'speaker': seg['speaker'],
                'start': seg['start'],
                'end': seg['end'],
                'text': seg['text']
            }
    
    # Adiciona último grupo
    if grupo_atual['text']:
        agrupados.append(grupo_atual)
    
    return agrupados

def renomear_speakers_interativo(speaker_segments):
    """
    Permite ao usuário dar nomes aos speakers
    """
    # Identifica speakers únicos
    speakers_unicos = sorted(set(seg['speaker'] for seg in speaker_segments))
    
    print("\n" + "="*70)
    print("🎤 IDENTIFICAÇÃO DE SPEAKERS")
    print("="*70)
    print(f"\nEncontrados {len(speakers_unicos)} speaker(s) diferentes")
    print("\nPrimeiras falas de cada speaker:")
    print()
    
    # Mostra amostra de cada speaker
    for speaker in speakers_unicos:
        primeira_fala = next(seg for seg in speaker_segments if seg['speaker'] == speaker)
        preview = primeira_fala['text'][:100] + "..." if len(primeira_fala['text']) > 100 else primeira_fala['text']
        print(f"{speaker}:")
        print(f"  [{formatar_timestamp(primeira_fala['start'])}] {preview}")
        print()
    
    # Pergunta se quer renomear
    print("Deseja dar nomes aos speakers? (s/n) [padrão: n]: ", end="")
    resposta = input().strip().lower()
    
    if resposta == 's':
        mapeamento = {}
        for speaker in speakers_unicos:
            print(f"\nNome para {speaker} (Enter para manter): ", end="")
            nome = input().strip()
            if nome:
                mapeamento[speaker] = nome
            else:
                mapeamento[speaker] = speaker
        
        # Aplica mapeamento
        for seg in speaker_segments:
            seg['speaker'] = mapeamento.get(seg['speaker'], seg['speaker'])
    
    return speaker_segments

def transcrever_com_speakers(caminho_video, modelo="large", renomear=True):
    """
    Transcrição com identificação de speakers
    
    Args:
        caminho_video: Caminho do arquivo
        modelo: tiny, base, small, medium, large
        renomear: Se deve permitir renomear speakers
    """
    print("="*70)
    print("🎙️  WHISPER COM SEPARAÇÃO DE SPEAKERS")
    print("="*70)
    print()
    
    # Verifica arquivo
    if not os.path.exists(caminho_video):
        print(f"❌ Arquivo não encontrado: {caminho_video}")
        return None
    
    tamanho_mb = os.path.getsize(caminho_video) / (1024 * 1024)
    print(f"📁 Arquivo: {os.path.basename(caminho_video)}")
    print(f"📊 Tamanho: {tamanho_mb:.2f} MB")
    print()
    
    # Verifica GPU
    tem_gpu = torch.cuda.is_available()
    if tem_gpu:
        gpu_name = torch.cuda.get_device_name(0)
        print(f"✓ GPU: {gpu_name}")
    else:
        print("⚠️  Usando CPU (será mais lento)")
    print()
    
    # Estimativa (otimizada)
    tempo_por_mb = {
        'tiny': 0.5 if tem_gpu else 3,
        'base': 1 if tem_gpu else 4,
        'small': 2 if tem_gpu else 6,
        'medium': 4 if tem_gpu else 12,
        'large': 6 if tem_gpu else 25,
    }
    
    tempo_estimado = tamanho_mb * tempo_por_mb.get(modelo, 10)
    print(f"⏱️  Tempo estimado: {tempo_estimado/60:.1f} minutos")
    print(f"🤖 Modelo: {modelo}")
    print(f"🎯 Modo: Com separação de speakers")
    print()
    
    try:
        # Carrega modelo
        print("📥 Carregando modelo Whisper...")
        inicio_carga = time.time()
        model = whisper.load_model(modelo)
        tempo_carga = time.time() - inicio_carga
        print(f"✓ Modelo carregado em {tempo_carga:.1f}s")
        print()
        
        # Transcreve
        print(f"🎙️  Iniciando transcrição às {datetime.now().strftime('%H:%M:%S')}")
        print("⏳ Processando...")
        print()
        
        inicio = time.time()
        
        # Configurações ULTRA otimizadas para velocidade máxima
        resultado = model.transcribe(
            caminho_video,
            language='pt',
            task='transcribe',
            fp16=tem_gpu,
            verbose=True,
            # Otimizações AGRESSIVAS de velocidade
            word_timestamps=False,
            condition_on_previous_text=False,
            temperature=0.0,
            beam_size=1,
            best_of=1,
            patience=1.0,  # Reduz paciência do beam search
            length_penalty=1.0,
            compression_ratio_threshold=2.4,
            logprob_threshold=-1.0,
            no_speech_threshold=0.6,
            # Configurações adicionais para velocidade
            initial_prompt=None,  # Remove prompt inicial
            suppress_tokens="-1",  # Desabilita supressão de tokens
        )
        
        tempo_total = time.time() - inicio
        
        print(f"\n✓ Transcrição concluída em {tempo_total/60:.1f} minutos")
        print()
        
        # Detecta speakers
        print("🔍 Detectando speakers...")
        segments = resultado.get('segments', [])
        speaker_segments = detectar_mudancas_speaker_simples(segments)
        
        # Agrupa por speaker
        print("📊 Agrupando falas...")
        speaker_agrupado = agrupar_por_speaker(speaker_segments)
        
        # Renomeia speakers se solicitado
        if renomear:
            speaker_agrupado = renomear_speakers_interativo(speaker_agrupado)
        
        # Salva resultados
        nome_base = Path(caminho_video).stem
        
        # Arquivo com speakers
        arquivo_speakers = f"{nome_base}_com_speakers.txt"
        with open(arquivo_speakers, "w", encoding="utf-8") as f:
            f.write("="*70 + "\n")
            f.write("🎙️  TRANSCRIÇÃO COM SPEAKERS\n")
            f.write("="*70 + "\n\n")
            f.write(f"📁 Arquivo: {os.path.basename(caminho_video)}\n")
            f.write(f"🤖 Modelo: {modelo}\n")
            f.write(f"⏱️  Duração: {resultado.get('duration', 0)/60:.1f} minutos\n")
            f.write(f"⚡ Tempo de processamento: {tempo_total/60:.1f} minutos\n")
            f.write(f"🎤 Speakers detectados: {len(set(seg['speaker'] for seg in speaker_agrupado))}\n")
            f.write("\n" + "="*70 + "\n")
            f.write("TRANSCRIÇÃO\n")
            f.write("="*70 + "\n\n")
            
            speaker_anterior = None
            for seg in speaker_agrupado:
                # Adiciona linha em branco entre speakers diferentes
                if speaker_anterior and speaker_anterior != seg['speaker']:
                    f.write("\n")
                
                timestamp = formatar_timestamp(seg['start'])
                f.write(f"[{timestamp}] {seg['speaker']}:\n")
                f.write(f"{seg['text']}\n\n")
                
                speaker_anterior = seg['speaker']
        
        # Estatísticas
        num_speakers = len(set(seg['speaker'] for seg in speaker_agrupado))
        num_palavras = sum(len(seg['text'].split()) for seg in speaker_agrupado)
        duracao_min = resultado.get('duration', 0) / 60
        
        # Conta falas por speaker
        falas_por_speaker = {}
        for seg in speaker_agrupado:
            speaker = seg['speaker']
            if speaker not in falas_por_speaker:
                falas_por_speaker[speaker] = {'count': 0, 'palavras': 0}
            falas_por_speaker[speaker]['count'] += 1
            falas_por_speaker[speaker]['palavras'] += len(seg['text'].split())
        
        print("\n" + "="*70)
        print("📈 ESTATÍSTICAS")
        print("="*70)
        print(f"⏱️  Duração: {duracao_min:.1f} minutos")
        print(f"⚡ Tempo de processamento: {tempo_total/60:.1f} minutos")
        print(f"🚀 Velocidade: {duracao_min/(tempo_total/60):.1f}x tempo real")
        print(f"📝 Palavras: {num_palavras:,}")
        print(f"🎤 Speakers: {num_speakers}")
        print(f"📊 Segmentos: {len(speaker_agrupado)}")
        
        print("\n" + "="*70)
        print("🎤 ESTATÍSTICAS POR SPEAKER")
        print("="*70)
        for speaker, stats in sorted(falas_por_speaker.items()):
            porcentagem = (stats['palavras'] / num_palavras * 100) if num_palavras > 0 else 0
            print(f"{speaker}:")
            print(f"  Falas: {stats['count']}")
            print(f"  Palavras: {stats['palavras']:,} ({porcentagem:.1f}%)")
        
        print("\n" + "="*70)
        print("💾 ARQUIVO SALVO")
        print("="*70)
        print(f"📄 {arquivo_speakers}")
        
        print("\n" + "="*70)
        print("📝 PRÉVIA")
        print("="*70)
        for i, seg in enumerate(speaker_agrupado[:5]):  # Primeiras 5 falas
            timestamp = formatar_timestamp(seg['start'])
            preview = seg['text'][:100] + "..." if len(seg['text']) > 100 else seg['text']
            print(f"[{timestamp}] {seg['speaker']}:")
            print(f"{preview}\n")
        
        if len(speaker_agrupado) > 5:
            print(f"... e mais {len(speaker_agrupado) - 5} falas")
        
        print("="*70)
        
        return {
            'resultado': resultado,
            'speaker_segments': speaker_agrupado,
            'arquivo': arquivo_speakers,
            'estatisticas': {
                'speakers': num_speakers,
                'palavras': num_palavras,
                'duracao_min': duracao_min,
                'tempo_processamento': tempo_total/60,
                'falas_por_speaker': falas_por_speaker
            }
        }
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Transcrição cancelada")
        return None
    except Exception as e:
        print(f"\n❌ Erro: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("="*70)
        print("🎙️  WHISPER COM SEPARAÇÃO DE SPEAKERS")
        print("="*70)
        print("\nUso: python whisper_com_speakers.py <arquivo> [modelo]")
        print("\nModelos disponíveis (otimizados):")
        print("  - tiny:   Muito rápido (~30s-1min para 60MB) - qualidade básica")
        print("  - base:   Rápido (~1-2 min para 60MB) - boa qualidade")
        print("  - small:  Balanceado (~2-4 min para 60MB) - ótima qualidade ⭐")
        print("  - medium: Lento (~4-8 min para 60MB) - excelente qualidade")
        print("  - large:  Muito lento (~6-12 min para 60MB) - máxima qualidade")
        print("\nExemplos:")
        print('  python whisper_com_speakers.py "reuniao.mp4"')
        print('  python whisper_com_speakers.py "reuniao.mp4" large')
        sys.exit(1)
    
    caminho = sys.argv[1].strip('"\'')
    modelo = sys.argv[2] if len(sys.argv) > 2 else "large"
    
    transcrever_com_speakers(caminho, modelo=modelo, renomear=True)
