"""
TRANSCREVER - Apenas transcrição com Whisper
Gera arquivo TXT bruto sem correções
"""
import whisper
import os
import sys
import time
import torch
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import warnings
warnings.filterwarnings("ignore")

# Tenta importar PyAnnote (opcional)
try:
    from pyannote.audio import Pipeline
    PYANNOTE_AVAILABLE = True
except ImportError:
    PYANNOTE_AVAILABLE = False

# Glossário de termos técnicos (para melhorar reconhecimento)
GLOSSARIO_TERMOS = [
    "pitch", "MVP", "Storytelling", "Impulsione", 
    "call to action", "ROI", "payback",
    "prontuário", "fluxograma", "slides",
    "ChatGPT", "protótipo", "validação",
    "piloto", "cooperativa", "Unimed",
    "banca", "mentoria", "pre-pitch",
    "Distrito 28", "hub", "SIAC", "IBAMA", "IFS"
]

def formatar_timestamp(segundos):
    """Converte segundos em formato HH:MM:SS"""
    return str(timedelta(seconds=int(segundos)))

def extrair_audio_segmento(audio_file: str, inicio: float, fim: float, output_file: str):
    """Extrai segmento de áudio (requer ffmpeg)"""
    import subprocess
    try:
        cmd = [
            'ffmpeg', '-i', audio_file,
            '-ss', str(inicio),
            '-t', str(fim - inicio),
            '-acodec', 'copy',
            output_file,
            '-y', '-loglevel', 'quiet'
        ]
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        return os.path.exists(output_file)
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Erro ao extrair segmento: {e}")
        return False
    except FileNotFoundError:
        print("⚠️  ffmpeg não encontrado. Instale ffmpeg para usar diarização com PyAnnote.")
        return False
    except Exception as e:
        print(f"⚠️  Erro ao extrair segmento: {e}")
        return False

def diarizar_com_pyannote(audio_file: str, auth_token: Optional[str] = None):
    """Diarização usando PyAnnote (antes do Whisper)"""
    if not PYANNOTE_AVAILABLE:
        return None
    
    try:
        print("🔍 Iniciando diarização com PyAnnote...")
        
        if auth_token:
            pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1",
                use_auth_token=auth_token
            )
        else:
            try:
                pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization-3.1")
            except:
                print("⚠️  PyAnnote requer token de autenticação. Use diarização simplificada.")
                return None
        
        diarization = pipeline(audio_file)
        
        segmentos = []
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            segmentos.append({
                'start': turn.start,
                'end': turn.end,
                'speaker': speaker
            })
        
        print(f"✓ Diarização concluída: {len(segmentos)} segmentos, {len(set(s['speaker'] for s in segmentos))} speakers")
        return segmentos
        
    except Exception as e:
        print(f"⚠️  Erro na diarização PyAnnote: {e}")
        print("   Usando diarização simplificada...")
        return None

def transcrever(caminho_video: str,
                modelo: str = "large-v3",
                usar_pyannote: bool = True,
                pyannote_token: Optional[str] = None):
    """
    TRANSCREVE vídeo/áudio e salva resultado bruto
    
    Args:
        caminho_video: Caminho do arquivo de vídeo/áudio
        modelo: Modelo Whisper (tiny, base, small, medium, large, large-v3)
        usar_pyannote: Se True, usa PyAnnote para diarização
        pyannote_token: Token de autenticação PyAnnote
    """
    print("="*70)
    print("🎙️  TRANSCRIÇÃO COM WHISPER")
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
        print("⚠️  CPU (será mais lento)")
    
    print(f"🤖 Modelo: {modelo}")
    print(f"🎤 PyAnnote: {'Sim' if usar_pyannote and PYANNOTE_AVAILABLE else 'Não'}")
    print()
    
    try:
        # PASSO 1: Diarização (se disponível)
        segmentos_diarizacao = None
        if usar_pyannote and PYANNOTE_AVAILABLE:
            segmentos_diarizacao = diarizar_com_pyannote(caminho_video, pyannote_token)
        
        # PASSO 2: Carrega modelo Whisper
        print("📥 Carregando modelo Whisper...")
        inicio_carga = time.time()
        
        try:
            model = whisper.load_model(modelo)
        except Exception:
            if modelo == "large-v3":
                print("⚠️  large-v3 não disponível, usando large")
                model = whisper.load_model("large")
            else:
                raise
        
        tempo_carga = time.time() - inicio_carga
        print(f"✓ Modelo carregado em {tempo_carga:.1f}s")
        print()
        
        # PASSO 3: Transcrição
        segmentos_transcritos = []
        
        if segmentos_diarizacao:
            # Transcreve por segmento diarizado
            print("🎙️  Transcrevendo por segmentos diarizados...")
            
            for i, seg_dia in enumerate(segmentos_diarizacao):
                print(f"   Segmento {i+1}/{len(segmentos_diarizacao)}: {formatar_timestamp(seg_dia['start'])} - {formatar_timestamp(seg_dia['end'])}")
                
                temp_audio = f"temp_segment_{i}.wav"
                if extrair_audio_segmento(caminho_video, seg_dia['start'], seg_dia['end'], temp_audio):
                    resultado = model.transcribe(
                        temp_audio,
                        language='pt',
                        task='transcribe',
                        fp16=tem_gpu,
                        word_timestamps=True,
                        initial_prompt=" ".join(GLOSSARIO_TERMOS[:20])
                    )
                    
                    texto = resultado.get('text', '').strip()
                    if texto:
                        segmentos_transcritos.append({
                            'start': seg_dia['start'],
                            'end': seg_dia['end'],
                            'speaker': seg_dia['speaker'],
                            'text': texto
                        })
                    
                    if os.path.exists(temp_audio):
                        os.remove(temp_audio)
            
            print(f"✓ Transcrição concluída: {len(segmentos_transcritos)} segmentos")
        else:
            # Transcrição tradicional (sem diarização separada)
            print("🎙️  Transcrevendo...")
            inicio = time.time()
            
            resultado = model.transcribe(
                caminho_video,
                language='pt',
                task='transcribe',
                fp16=tem_gpu,
                word_timestamps=True,
                condition_on_previous_text=True,
                temperature=0.0,
                beam_size=5,
                best_of=5,
                initial_prompt=" ".join(GLOSSARIO_TERMOS[:20])
            )
            
            tempo_total = time.time() - inicio
            print(f"✓ Transcrição concluída em {tempo_total/60:.1f} min")
            
            # Converte segments para formato padrão
            segments = resultado.get('segments', [])
            speaker_atual = 1
            
            for seg in segments:
                segmentos_transcritos.append({
                    'start': seg['start'],
                    'end': seg['end'],
                    'speaker': f'Speaker {speaker_atual}',
                    'text': seg['text'].strip()
                })
                # Detecta mudança de speaker (simplificado)
                if len(segmentos_transcritos) > 1:
                    pausa = seg['start'] - segments[segments.index(seg)-1]['end']
                    if pausa > 2.5:
                        speaker_atual += 1
                        segmentos_transcritos[-1]['speaker'] = f'Speaker {speaker_atual}'
        
        # PASSO 4: Salva transcrição BRUTA
        nome_base = Path(caminho_video).stem
        os.makedirs("output", exist_ok=True)
        arquivo_bruto = f"output/{nome_base}_transcricao_bruta.txt"
        
        with open(arquivo_bruto, 'w', encoding='utf-8') as f:
            f.write("="*70 + "\n")
            f.write("📝 TRANSCRIÇÃO BRUTA (SEM CORREÇÕES)\n")
            f.write("="*70 + "\n\n")
            f.write(f"📁 Arquivo: {os.path.basename(caminho_video)}\n")
            f.write(f"🤖 Modelo: {modelo}\n")
            f.write(f"🎤 PyAnnote: {'Sim' if usar_pyannote and PYANNOTE_AVAILABLE else 'Não'}\n")
            f.write(f"📊 Segmentos: {len(segmentos_transcritos)}\n")
            f.write(f"🎤 Speakers: {len(set(s['speaker'] for s in segmentos_transcritos))}\n")
            f.write("\n" + "="*70 + "\n")
            f.write("TRANSCRIÇÃO BRUTA\n")
            f.write("="*70 + "\n\n")
            
            speaker_anterior = None
            for seg in segmentos_transcritos:
                if speaker_anterior and speaker_anterior != seg['speaker']:
                    f.write("\n")
                
                timestamp = formatar_timestamp(seg['start'])
                f.write(f"[{timestamp}] {seg['speaker']}:\n")
                f.write(f"{seg['text']}\n\n")
                
                speaker_anterior = seg['speaker']
        
        print("\n" + "="*70)
        print("✅ TRANSCRIÇÃO CONCLUÍDA")
        print("="*70)
        print(f"📄 Arquivo bruto salvo: {arquivo_bruto}")
        print(f"📊 Segmentos: {len(segmentos_transcritos)}")
        print(f"🎤 Speakers: {len(set(s['speaker'] for s in segmentos_transcritos))}")
        print("\n💡 Próximo passo: Corrija o arquivo com:")
        print(f"   python corrigir.py \"{arquivo_bruto}\"")
        print("="*70)
        
        return arquivo_bruto
        
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
        print("🎙️  TRANSCREVER - Transcrição com Whisper")
        print("="*70)
        print("\nUso: python transcrever.py <arquivo> [opções]")
        print("\nOpções:")
        print("  [modelo]              - tiny, base, small, medium, large, large-v3 (padrão: large-v3)")
        print("  --sem-pyannote        - Não usa PyAnnote (diarização simplificada)")
        print("  --pyannote-token TOKEN - Token de autenticação PyAnnote")
        print("\nExemplos:")
        print('  python transcrever.py "video.mp4"')
        print('  python transcrever.py "video.mp4" large-v3')
        print('  python transcrever.py "video.mp4" --pyannote-token SEU_TOKEN')
        print("\nSaída:")
        print("  Gera: output/video_transcricao_bruta.txt")
        sys.exit(1)
    
    caminho = sys.argv[1].strip('"\'')
    modelo = "large-v3"
    usar_pyannote = True
    pyannote_token = None
    
    # Processa argumentos
    i = 2
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg in ['tiny', 'base', 'small', 'medium', 'large', 'large-v3']:
            modelo = arg
        elif arg == '--sem-pyannote':
            usar_pyannote = False
        elif arg == '--pyannote-token' and i + 1 < len(sys.argv):
            pyannote_token = sys.argv[i + 1]
            i += 1
        i += 1
    
    transcrever(caminho, modelo=modelo, usar_pyannote=usar_pyannote, pyannote_token=pyannote_token)
