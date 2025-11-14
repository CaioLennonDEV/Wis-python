"""
Whisper RÁPIDO com Speakers - Otimizado para vídeos longos
Usa modelo small (melhor custo-benefício velocidade/qualidade)
"""
import whisper
import os
import sys
import time
import torch
from pathlib import Path
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings("ignore")

def formatar_timestamp(segundos):
    """Converte segundos em formato HH:MM:SS"""
    return str(timedelta(seconds=int(segundos)))

def detectar_speakers(segments, threshold_pausa=2.5):
    """Detecta mudanças de speaker baseado em pausas"""
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
            pausa = seg['start'] - segments[i-1]['end']
            
            if pausa > threshold_pausa:
                speaker_atual += 1
            
            speakers.append({
                'speaker': f'Speaker {speaker_atual}',
                'start': seg['start'],
                'end': seg['end'],
                'text': seg['text'].strip()
            })
    
    return speakers

def agrupar_speakers(speaker_segments):
    """Agrupa segmentos consecutivos do mesmo speaker"""
    if not speaker_segments:
        return []
    
    agrupados = []
    grupo = {
        'speaker': speaker_segments[0]['speaker'],
        'start': speaker_segments[0]['start'],
        'end': speaker_segments[0]['end'],
        'text': speaker_segments[0]['text']
    }
    
    for seg in speaker_segments[1:]:
        if seg['speaker'] == grupo['speaker']:
            grupo['end'] = seg['end']
            grupo['text'] += ' ' + seg['text']
        else:
            agrupados.append(grupo)
            grupo = {
                'speaker': seg['speaker'],
                'start': seg['start'],
                'end': seg['end'],
                'text': seg['text']
            }
    
    agrupados.append(grupo)
    return agrupados

def transcrever_rapido(caminho_video, modelo="small"):
    """Transcrição rápida com speakers"""
    
    print("="*70)
    print("⚡ WHISPER RÁPIDO COM SPEAKERS")
    print("="*70)
    print()
    
    if not os.path.exists(caminho_video):
        print(f"❌ Arquivo não encontrado: {caminho_video}")
        return None
    
    tamanho_mb = os.path.getsize(caminho_video) / (1024 * 1024)
    print(f"📁 Arquivo: {os.path.basename(caminho_video)}")
    print(f"📊 Tamanho: {tamanho_mb:.2f} MB")
    
    tem_gpu = torch.cuda.is_available()
    if tem_gpu:
        print(f"✓ GPU: {torch.cuda.get_device_name(0)}")
    else:
        print("⚠️  CPU (mais lento)")
    
    print(f"🤖 Modelo: {modelo} (otimizado)")
    print()
    
    try:
        print("📥 Carregando modelo...")
        inicio_carga = time.time()
        model = whisper.load_model(modelo)
        print(f"✓ Carregado em {time.time() - inicio_carga:.1f}s")
        print()
        
        print(f"🎙️  Transcrevendo... ({datetime.now().strftime('%H:%M:%S')})")
        inicio = time.time()
        
        # Configurações MÁXIMA VELOCIDADE
        resultado = model.transcribe(
            caminho_video,
            language='pt',
            fp16=tem_gpu,
            verbose=True,
            # Velocidade máxima
            beam_size=1,
            best_of=1,
            temperature=0,
            condition_on_previous_text=False,
            word_timestamps=False,
            compression_ratio_threshold=2.4,
            no_speech_threshold=0.6,
        )
        
        tempo_total = time.time() - inicio
        duracao = resultado.get('duration', 0) / 60
        
        print(f"\n✓ Concluído em {tempo_total/60:.1f} min")
        print(f"🚀 Velocidade: {duracao/(tempo_total/60):.1f}x tempo real")
        print()
        
        # Processa speakers
        print("🔍 Detectando speakers...")
        segments = resultado.get('segments', [])
        speaker_segments = detectar_speakers(segments)
        speaker_agrupado = agrupar_speakers(speaker_segments)
        
        # Salva
        nome_base = Path(caminho_video).stem
        arquivo = f"{nome_base}_transcricao.txt"
        
        with open(arquivo, "w", encoding="utf-8") as f:
            f.write("="*70 + "\n")
            f.write("⚡ TRANSCRIÇÃO RÁPIDA COM SPEAKERS\n")
            f.write("="*70 + "\n\n")
            f.write(f"📁 {os.path.basename(caminho_video)}\n")
            f.write(f"🤖 Modelo: {modelo}\n")
            f.write(f"⏱️  Duração: {duracao:.1f} min\n")
            f.write(f"⚡ Processamento: {tempo_total/60:.1f} min\n")
            f.write(f"🎤 Speakers: {len(set(s['speaker'] for s in speaker_agrupado))}\n")
            f.write("\n" + "="*70 + "\n\n")
            
            for seg in speaker_agrupado:
                f.write(f"[{formatar_timestamp(seg['start'])}] {seg['speaker']}:\n")
                f.write(f"{seg['text']}\n\n")
        
        # Stats
        num_speakers = len(set(s['speaker'] for s in speaker_agrupado))
        num_palavras = sum(len(s['text'].split()) for s in speaker_agrupado)
        
        print("\n" + "="*70)
        print("📈 ESTATÍSTICAS")
        print("="*70)
        print(f"⏱️  Duração: {duracao:.1f} min")
        print(f"⚡ Processamento: {tempo_total/60:.1f} min")
        print(f"🚀 Velocidade: {duracao/(tempo_total/60):.1f}x")
        print(f"📝 Palavras: {num_palavras:,}")
        print(f"🎤 Speakers: {num_speakers}")
        print(f"📊 Segmentos: {len(speaker_agrupado)}")
        print()
        print(f"💾 Salvo: {arquivo}")
        print("="*70)
        
        return arquivo
        
    except KeyboardInterrupt:
        print("\n⚠️  Cancelado")
        return None
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        return None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("="*70)
        print("⚡ WHISPER RÁPIDO COM SPEAKERS")
        print("="*70)
        print("\nUso: python whisper_rapido.py <arquivo> [modelo]")
        print("\nModelos (velocidade para 1h de vídeo com GPU):")
        print("  - tiny:   ~3-5 min (qualidade básica)")
        print("  - base:   ~5-8 min (boa qualidade)")
        print("  - small:  ~8-15 min (ótima qualidade) ⭐ RECOMENDADO")
        print("  - medium: ~15-25 min (excelente)")
        print("  - large:  ~25-40 min (máxima)")
        print("\nExemplo:")
        print('  python whisper_rapido.py "video.mp4"')
        print('  python whisper_rapido.py "video.mp4" small')
        sys.exit(1)
    
    caminho = sys.argv[1].strip('"\'')
    modelo = sys.argv[2] if len(sys.argv) > 2 else "small"
    
    transcrever_rapido(caminho, modelo)
