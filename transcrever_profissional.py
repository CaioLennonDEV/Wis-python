"""
TRANSCREVER PROFISSIONAL - Com PyAnnote real + otimizações
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

# PyAnnote (opcional mas recomendado)
try:
    from pyannote.audio import Pipeline
    PYANNOTE_AVAILABLE = True
except ImportError:
    PYANNOTE_AVAILABLE = False
    print("⚠️  PyAnnote não instalado. Instale com: pip install pyannote-audio")

def formatar_timestamp(segundos):
    """Formata timestamp como HH:MM:SS"""
    h = int(segundos // 3600)
    m = int((segundos % 3600) // 60)
    s = int(segundos % 60)
    return f"{h}:{m:02d}:{s:02d}"

def diarizar_pyannote(audio_file: str, hf_token: str = None):
    """
    Diarização REAL com PyAnnote
    Retorna segmentos com speaker identificado
    """
    if not PYANNOTE_AVAILABLE:
        print("❌ PyAnnote não disponível")
        return None
    
    try:
        print("🔍 Iniciando diarização com PyAnnote...")
        print("   (Isso pode levar alguns minutos...)")
        
        # Carrega pipeline
        if hf_token:
            pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1",
                use_auth_token=hf_token
            )
        else:
            # Tenta sem token (se já aceitou termos)
            pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1"
            )
        
        # Move para GPU se disponível
        if torch.cuda.is_available():
            pipeline.to(torch.device("cuda"))
        
        # Executa diarização
        inicio = time.time()
        diarization = pipeline(audio_file)
        tempo = time.time() - inicio
        
        # Extrai segmentos
        segmentos = []
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            segmentos.append({
                'start': turn.start,
                'end': turn.end,
                'speaker': speaker
            })
        
        num_speakers = len(set(s['speaker'] for s in segmentos))
        print(f"✓ Diarização concluída em {tempo:.1f}s")
        print(f"   {len(segmentos)} segmentos, {num_speakers} speakers detectados")
        
        return segmentos
        
    except Exception as e:
        print(f"❌ Erro na diarização: {e}")
        print("\n💡 Para usar PyAnnote:")
        print("   1. Crie conta em https://huggingface.co")
        print("   2. Aceite termos em https://hf.co/pyannote/speaker-diarization-3.1")
        print("   3. Crie token em https://hf.co/settings/tokens")
        print("   4. Use: --hf-token SEU_TOKEN")
        return None

def transcrever_segmento(model, audio_file: str, start: float, end: float, tem_gpu: bool):
    """Transcreve um segmento específico do áudio"""
    import subprocess
    import tempfile
    
    # Extrai segmento com ffmpeg
    temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
    temp_path = temp_file.name
    temp_file.close()
    
    try:
        cmd = [
            'ffmpeg', '-i', audio_file,
            '-ss', str(start),
            '-t', str(end - start),
            '-ar', '16000',  # Sample rate para Whisper
            '-ac', '1',  # Mono
            temp_path,
            '-y', '-loglevel', 'quiet'
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        
        # Transcreve
        resultado = model.transcribe(
            temp_path,
            language='pt',
            fp16=tem_gpu,
            beam_size=1,
            best_of=1,
            temperature=0.0,
            condition_on_previous_text=False,
            word_timestamps=False,
        )
        
        return resultado.get('text', '').strip()
        
    except Exception as e:
        print(f"⚠️  Erro ao transcrever segmento: {e}")
        return ""
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

def transcrever_profissional(
    caminho_video: str,
    modelo: str = "small",
    usar_pyannote: bool = True,
    hf_token: str = None
):
    """
    Transcrição profissional com diarização real
    """
    print("="*70)
    print("⚡ TRANSCRIÇÃO PROFISSIONAL")
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
    
    print(f"🤖 Modelo Whisper: {modelo}")
    print(f"🎤 PyAnnote: {'Sim' if usar_pyannote and PYANNOTE_AVAILABLE else 'Não'}")
    print()
    
    try:
        # ETAPA 1: Diarização (se habilitado)
        segmentos_diarizados = None
        if usar_pyannote and PYANNOTE_AVAILABLE:
            segmentos_diarizados = diarizar_pyannote(caminho_video, hf_token)
            
            if not segmentos_diarizados:
                print("\n⚠️  Diarização falhou, usando modo simplificado")
                usar_pyannote = False
        
        # ETAPA 2: Carrega Whisper
        print("\n📥 Carregando Whisper...")
        inicio_carga = time.time()
        
        if tem_gpu:
            model = whisper.load_model(modelo, device="cuda")
        else:
            model = whisper.load_model(modelo)
        
        print(f"✓ Carregado em {time.time() - inicio_carga:.1f}s")
        print()
        
        # ETAPA 3: Transcrição
        segmentos_finais = []
        
        if segmentos_diarizados:
            # Modo PROFISSIONAL: transcreve por segmento diarizado
            print("🎙️  Transcrevendo com diarização real...")
            print(f"   {len(segmentos_diarizados)} segmentos para processar")
            print()
            
            inicio = time.time()
            
            for i, seg_dia in enumerate(segmentos_diarizados, 1):
                duracao_seg = seg_dia['end'] - seg_dia['start']
                
                # Pula segmentos muito curtos (< 0.5s)
                if duracao_seg < 0.5:
                    continue
                
                if i % 10 == 0 or i == 1:
                    print(f"   Processando {i}/{len(segmentos_diarizados)}...")
                
                texto = transcrever_segmento(
                    model,
                    caminho_video,
                    seg_dia['start'],
                    seg_dia['end'],
                    tem_gpu
                )
                
                if texto:
                    segmentos_finais.append({
                        'start': seg_dia['start'],
                        'end': seg_dia['end'],
                        'speaker': seg_dia['speaker'],
                        'text': texto
                    })
            
            tempo_total = time.time() - inicio
            print(f"\n✓ Transcrição concluída em {tempo_total/60:.1f} min")
            
        else:
            # Modo SIMPLIFICADO: transcrição completa + detecção por pausas
            print("🎙️  Transcrevendo (modo simplificado)...")
            print(f"   Iniciado às {datetime.now().strftime('%H:%M:%S')}")
            
            inicio = time.time()
            
            resultado = model.transcribe(
                caminho_video,
                language='pt',
                fp16=tem_gpu,
                verbose=False,
                beam_size=1,
                best_of=1,
                temperature=0.0,
                condition_on_previous_text=False,
                word_timestamps=False,
            )
            
            tempo_total = time.time() - inicio
            print(f"✓ Concluído em {tempo_total/60:.1f} min")
            
            # Detecta speakers por pausas
            segments = resultado.get('segments', [])
            speaker_atual = 1
            
            for i, seg in enumerate(segments):
                # Detecta mudança de speaker por pausa longa
                if i > 0:
                    pausa = seg['start'] - segments[i-1]['end']
                    if pausa > 2.5:
                        speaker_atual += 1
                
                segmentos_finais.append({
                    'start': seg['start'],
                    'end': seg['end'],
                    'speaker': f'Speaker {speaker_atual}',
                    'text': seg['text'].strip()
                })
        
        # ETAPA 4: Salva resultado BRUTO
        nome_base = Path(caminho_video).stem
        os.makedirs("output", exist_ok=True)
        arquivo_bruto = f"output/{nome_base}_transcricao_bruta.txt"
        
        with open(arquivo_bruto, 'w', encoding='utf-8') as f:
            f.write("="*70 + "\n")
            f.write("📝 TRANSCRIÇÃO BRUTA (SEM CORREÇÕES)\n")
            f.write("="*70 + "\n\n")
            f.write(f"📁 Arquivo: {os.path.basename(caminho_video)}\n")
            f.write(f"🤖 Modelo: {modelo}\n")
            f.write(f"🎤 Diarização: {'PyAnnote' if segmentos_diarizados else 'Simplificada'}\n")
            f.write(f"📊 Segmentos: {len(segmentos_finais)}\n")
            f.write(f"🎤 Speakers: {len(set(s['speaker'] for s in segmentos_finais))}\n")
            f.write("\n" + "="*70 + "\n")
            f.write("TRANSCRIÇÃO BRUTA\n")
            f.write("="*70 + "\n\n")
            
            speaker_anterior = None
            for seg in segmentos_finais:
                if speaker_anterior and speaker_anterior != seg['speaker']:
                    f.write("\n")
                
                timestamp = formatar_timestamp(seg['start'])
                f.write(f"[{timestamp}] {seg['speaker']}:\n")
                f.write(f"{seg['text']}\n\n")
                
                speaker_anterior = seg['speaker']
        
        # Stats
        num_speakers = len(set(s['speaker'] for s in segmentos_finais))
        num_palavras = sum(len(s['text'].split()) for s in segmentos_finais)
        
        print("\n" + "="*70)
        print("✅ TRANSCRIÇÃO CONCLUÍDA")
        print("="*70)
        print(f"📄 Arquivo: {arquivo_bruto}")
        print(f"📊 Segmentos: {len(segmentos_finais)}")
        print(f"🎤 Speakers: {num_speakers}")
        print(f"📝 Palavras: {num_palavras:,}")
        print("\n💡 Próximo passo:")
        print(f'   python pos_processar.py "{arquivo_bruto}"')
        print("="*70)
        
        return arquivo_bruto
        
    except KeyboardInterrupt:
        print("\n⚠️  Cancelado")
        return None
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("="*70)
        print("⚡ TRANSCRIÇÃO PROFISSIONAL")
        print("="*70)
        print("\nUso: python transcrever_profissional.py <arquivo> [opções]")
        print("\nOpções:")
        print("  [modelo]           - tiny, base, small, medium, large (padrão: small)")
        print("  --sem-pyannote     - Desabilita diarização PyAnnote")
        print("  --hf-token TOKEN   - Token HuggingFace para PyAnnote")
        print("\nExemplos:")
        print('  python transcrever_profissional.py "video.mp4"')
        print('  python transcrever_profissional.py "video.mp4" small')
        print('  python transcrever_profissional.py "video.mp4" --hf-token hf_...')
        print('  python transcrever_profissional.py "video.mp4" --sem-pyannote')
        print("\n💡 Para usar PyAnnote (diarização real):")
        print("   1. pip install pyannote-audio")
        print("   2. Aceite termos: https://hf.co/pyannote/speaker-diarization-3.1")
        print("   3. Crie token: https://hf.co/settings/tokens")
        sys.exit(1)
    
    caminho = sys.argv[1].strip('"\'')
    modelo = "small"
    usar_pyannote = True
    hf_token = None
    
    # Processa argumentos
    i = 2
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg in ['tiny', 'base', 'small', 'medium', 'large']:
            modelo = arg
        elif arg == '--sem-pyannote':
            usar_pyannote = False
        elif arg == '--hf-token' and i + 1 < len(sys.argv):
            hf_token = sys.argv[i + 1]
            i += 1
        i += 1
    
    transcrever_profissional(caminho, modelo, usar_pyannote, hf_token)
