"""
Whisper AVANÇADO - Versão Final com Todas as Melhorias
Implementa:
- Diarização separada (PyAnnote antes do Whisper)
- Segmentação por tópicos com palavras-chave
- Limpeza de vícios de fala
- Normalização robusta de termos
- Pós-correção semântica (opcional com LLM)
- Organização em blocos temáticos estruturados
"""
import whisper
import os
import sys
import time
import torch
import re
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import warnings
warnings.filterwarnings("ignore")

# Tenta importar PyAnnote (opcional)
try:
    from pyannote.audio import Pipeline
    PYANNOTE_AVAILABLE = True
except ImportError:
    PYANNOTE_AVAILABLE = False
    print("⚠️  PyAnnote não disponível. Usando diarização simplificada.")

# ============================================================================
# CONFIGURAÇÕES
# ============================================================================

# Glossário de termos técnicos
GLOSSARIO_TERMOS = [
    "pitch", "MVP", "Storytelling", "Impulsione", 
    "call to action", "ROI", "payback",
    "prontuário", "fluxograma", "slides",
    "ChatGPT", "protótipo", "validação",
    "piloto", "cooperativa", "Unimed",
    "banca", "mentoria", "pre-pitch",
    "Distrito 28", "hub", "SIAC", "IBAMA", "IFS"
]

# Normalização de termos (correções mais robustas)
NORMALIZACAO_TERMOS = {
    "pitch": ["bit", "pitt", "pit", "PIT", "PTIP", "pichi", "pitchi"],
    "ChatGPT": ["chat IPT", "chat ipt", "chatGPT", "chat gpt"],
    "slides": ["exides", "exide", "slids"],
    "Storytelling": ["story télia", "story tell", "storytel", "story telling"],
    "Impulsione": ["Impulsionian", "impulsione", "impusione"],
    "fluxograma": ["fluxo-grama", "fluxo grama"],
    "prontuário": ["pronto arimétrico", "prontuário eletrônico"],
    "protótipo": ["prototipo", "protótipo"],
    "Sharks": ["Cháx", "Shark"],
    "Shark Tank": ["Shark Ten", "Shark Tank"],
    "pre-pitch": ["prepitch", "prepit", "pre-pitch"],
    "mentoria": ["mentories", "mentorie"],
    "capilar": ["capitalá"],
    "frizz": ["fris"],
    "Anelícia Libardoni": ["Anuletícia Libardo"],
}

# Vícios de fala para remover/limpar
VICIOS_FALA = [
    r'\bné\b',
    r'\btá\b',
    r'\benfim\b',
    r'\be\.\.\.\b',
    r'\bentão\.\.\.\b',
    r'\bassim\.\.\.\b',
    r'\bné\?\s*',
    r'\btá\?\s*',
    r'\bné\s*',
    r'\btá\s*',
]

# Palavras-chave para segmentação por tópicos
TOPICOS_KEYWORDS = {
    "Apresentação": ["apresentação", "capa", "logo", "slogan", "primeiro slide"],
    "Problema": ["problema", "dor", "história", "storytelling", "validação", "dados", "pesquisa"],
    "Solução": ["solução", "protótipo", "fluxo", "funcionalidade", "aplicativo", "sistema"],
    "Benefícios": ["benefícios", "resultados", "impacto", "métrica", "indicador"],
    "Diferencial": ["diferencial", "comparativo", "processo atual", "ganho"],
    "Time": ["time", "equipe", "membros", "competências", "especialista"],
    "Próximos Passos": ["próximos passos", "plano", "implementação", "cronograma", "riscos", "investimento", "recursos"],
    "Call to Action": ["call to action", "chamada para ação", "você", "invista", "revolucionar"],
    "Avaliação": ["banca avaliadora", "banca", "avaliar", "observar", "pontuar", "perguntas frequentes"],
    "Regras": ["regras", "presença", "engajamento", "mentoria", "planilha", "prazo", "dia 18"],
    "Exemplo": ["Shark Tank", "Shark Ten", "exemplo", "vídeo", "Solta Beauty"],
    "Logística": ["pre-pitch", "Distrito 28", "hub", "horário", "local", "presencial", "online"],
    "Finalização": ["música", "foto", "lista de presença", "QR Code", "encerrar"]
}

# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================

def formatar_timestamp(segundos):
    """Converte segundos em formato HH:MM:SS"""
    return str(timedelta(seconds=int(segundos)))

def extrair_audio_segmento(audio_file: str, inicio: float, fim: float, output_file: str):
    """
    Extrai segmento de áudio (requer ffmpeg)
    """
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

# ============================================================================
# DIARIZAÇÃO SEPARADA (PyAnnote)
# ============================================================================

def diarizar_com_pyannote(audio_file: str, auth_token: Optional[str] = None):
    """
    Diarização usando PyAnnote (antes do Whisper)
    Retorna lista de segmentos com speaker e timestamps
    """
    if not PYANNOTE_AVAILABLE:
        return None
    
    try:
        print("🔍 Iniciando diarização com PyAnnote...")
        
        # Carrega pipeline de diarização
        if auth_token:
            pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1",
                use_auth_token=auth_token
            )
        else:
            # Tenta carregar sem token (pode não funcionar)
            try:
                pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization-3.1")
            except:
                print("⚠️  PyAnnote requer token de autenticação. Use diarização simplificada.")
                return None
        
        # Executa diarização
        diarization = pipeline(audio_file)
        
        # Converte para formato simples
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

# ============================================================================
# NORMALIZAÇÃO DE TERMOS
# ============================================================================

def normalizar_termos(texto: str) -> str:
    """
    Normaliza termos técnicos usando dicionário robusto
    """
    texto_normalizado = texto
    
    for termo_correto, variacoes in NORMALIZACAO_TERMOS.items():
        for variacao in variacoes:
            # Busca palavra completa (não substring)
            pattern = r'\b' + re.escape(variacao) + r'\b'
            texto_normalizado = re.sub(pattern, termo_correto, texto_normalizado, flags=re.IGNORECASE)
    
    return texto_normalizado

# ============================================================================
# LIMPEZA DE VÍCIOS DE FALA
# ============================================================================

def limpar_vicios_fala(texto: str, modo: str = "medio") -> str:
    """
    Remove ou limpa vícios de fala comuns
    
    Modos:
    - "leve": Remove apenas repetições excessivas
    - "medio": Remove vícios comuns (né, tá, enfim) ⭐ RECOMENDADO
    - "agressivo": Remove todos os vícios + ajustes de fluidez
    """
    texto_limpo = texto
    
    if modo == "leve":
        # Remove apenas repetições
        texto_limpo = re.sub(r'\.\.\.+', '...', texto_limpo)
        texto_limpo = re.sub(r'\s+', ' ', texto_limpo)
    
    elif modo == "medio":
        # Remove vícios comuns
        for vicio in VICIOS_FALA:
            texto_limpo = re.sub(vicio, '', texto_limpo, flags=re.IGNORECASE)
        # Limpa espaços duplos
        texto_limpo = re.sub(r'\s+', ' ', texto_limpo)
        # Remove vírgulas duplas
        texto_limpo = re.sub(r',\s*,', ',', texto_limpo)
    
    elif modo == "agressivo":
        # Remove todos os vícios
        for vicio in VICIOS_FALA:
            texto_limpo = re.sub(vicio, '', texto_limpo, flags=re.IGNORECASE)
        # Ajustes de fluidez
        texto_limpo = re.sub(r'\s+', ' ', texto_limpo)
        texto_limpo = re.sub(r'([.!?])\1+', r'\1', texto_limpo)
        texto_limpo = re.sub(r'([.!?])([A-Za-z])', r'\1 \2', texto_limpo)
        texto_limpo = re.sub(r'\s+([,.!?;:])', r'\1', texto_limpo)
    
    return texto_limpo.strip()

# ============================================================================
# SEGMENTAÇÃO POR TÓPICOS
# ============================================================================

def identificar_topico(texto: str) -> Optional[str]:
    """
    Identifica tópico baseado em palavras-chave
    """
    texto_lower = texto.lower()
    
    # Conta matches por tópico
    scores = {}
    for topico, keywords in TOPICOS_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw.lower() in texto_lower)
        if score > 0:
            scores[topico] = score
    
    if scores:
        # Retorna tópico com maior score
        return max(scores.items(), key=lambda x: x[1])[0]
    
    return None

def segmentar_por_topicos(segmentos: List[Dict], max_chars: int = 600) -> List[Dict]:
    """
    Segmenta transcrição por tópicos e tamanho de bloco
    """
    segmentos_organizados = []
    topico_atual = None
    
    for seg in segmentos:
        texto = seg.get('text', '')
        topico = identificar_topico(texto)
        
        # Se mudou tópico ou bloco muito grande, cria novo segmento
        if topico and topico != topico_atual:
            topico_atual = topico
            seg['topico'] = topico
        elif len(texto) > max_chars and topico_atual:
            # Divide bloco grande
            seg['topico'] = topico_atual
        else:
            seg['topico'] = topico_atual or "Geral"
        
        segmentos_organizados.append(seg)
    
    return segmentos_organizados

# ============================================================================
# PÓS-CORREÇÃO SEMÂNTICA (LLM)
# ============================================================================

def corrigir_com_llm(texto: str, api_key: Optional[str] = None, modelo: str = "gpt-3.5-turbo") -> str:
    """
    Pós-correção semântica usando LLM (opcional)
    Requer API key do OpenAI ou outro provedor
    """
    if not api_key:
        return texto  # Retorna original se não tiver API key
    
    try:
        import openai
        openai.api_key = api_key
        
        prompt = f"""Limpe e corrija a transcrição abaixo:

- Corrija concordância e gramática
- Retire vícios de fala ("né", "tá", "enfim") apenas se não afetar o sentido
- Mantenha o sentido original
- NÃO resuma
- Melhore fluidez e clareza
- Mantenha termos técnicos (pitch, MVP, Storytelling, etc.)

Texto:
{texto}

Texto corrigido:"""
        
        response = openai.ChatCompletion.create(
            model=modelo,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=len(texto.split()) * 2
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        print(f"⚠️  Erro na correção LLM: {e}")
        return texto

# ============================================================================
# ETAPA 1: TRANSCRIÇÃO (SOMENTE TRANSCREVE, SEM CORREÇÕES)
# ============================================================================

def transcrever_apenas(caminho_video: str,
                      modelo: str = "large-v3",
                      usar_pyannote: bool = True,
                      pyannote_token: Optional[str] = None):
    """
    ETAPA 1: Apenas transcreve o vídeo e salva resultado bruto
    Não aplica correções - isso fica para a etapa 2
    """
    print("="*70)
    print("📝 ETAPA 1: TRANSCRIÇÃO (SEM CORREÇÕES)")
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
        
        # PASSO 3: Transcrição (SEM correções)
        segmentos_transcritos = []
        
        if segmentos_diarizacao:
            # Transcreve por segmento diarizado
            print("🎙️  Transcrevendo por segmentos diarizados...")
            
            for i, seg_dia in enumerate(segmentos_diarizacao):
                print(f"   Segmento {i+1}/{len(segmentos_diarizacao)}: {formatar_timestamp(seg_dia['start'])} - {formatar_timestamp(seg_dia['end'])}")
                
                # Extrai áudio do segmento
                temp_audio = f"temp_segment_{i}.wav"
                if extrair_audio_segmento(caminho_video, seg_dia['start'], seg_dia['end'], temp_audio):
                    # Transcreve segmento
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
                    
                    # Remove arquivo temporário
                    if os.path.exists(temp_audio):
                        os.remove(temp_audio)
            
            print(f"✓ Transcrição concluída: {len(segmentos_transcritos)} segmentos")
        else:
            # Transcrição tradicional (sem diarização separada)
            print("🎙️  Transcrevendo (método tradicional)...")
            inicio = time.time()
            
            resultado = model.transcribe(
                caminho_video,
                language='pt',
                task='transcribe',
                fp16=tem_gpu,
                verbose=True,
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
        
        # PASSO 4: Salva transcrição BRUTA (sem correções)
        nome_base = Path(caminho_video).stem
        arquivo_bruto = f"{nome_base}_transcricao_bruta.txt"
        
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
        print("✅ ETAPA 1 CONCLUÍDA")
        print("="*70)
        print(f"📄 Arquivo bruto salvo: {arquivo_bruto}")
        print(f"📊 Segmentos: {len(segmentos_transcritos)}")
        print(f"🎤 Speakers: {len(set(s['speaker'] for s in segmentos_transcritos))}")
        print("\n💡 Próximo passo: Execute a correção com:")
        print(f"   python whisper_avancado.py --corrigir \"{arquivo_bruto}\"")
        print("="*70)
        
        return {
            'arquivo_bruto': arquivo_bruto,
            'segmentos': segmentos_transcritos
        }
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Transcrição cancelada")
        return None
    except Exception as e:
        print(f"\n❌ Erro: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

# ============================================================================
# ETAPA 2: CORREÇÃO E ORGANIZAÇÃO (APLICA MELHORIAS)
# ============================================================================

def corrigir_e_organizar(caminho_arquivo_bruto: str,
                         modo_limpeza: str = "medio",
                         usar_llm: bool = False,
                         llm_api_key: Optional[str] = None,
                         max_chars_bloco: int = 600):
    """
    ETAPA 2: Aplica correções e organiza transcrição bruta
    Lê arquivo bruto e aplica todas as melhorias
    """
    print("="*70)
    print("🔧 ETAPA 2: CORREÇÃO E ORGANIZAÇÃO")
    print("="*70)
    print()
    
    if not os.path.exists(caminho_arquivo_bruto):
        print(f"❌ Arquivo não encontrado: {caminho_arquivo_bruto}")
        return None
    
    print(f"📁 Arquivo bruto: {os.path.basename(caminho_arquivo_bruto)}")
    print(f"🔧 Modo limpeza: {modo_limpeza}")
    print(f"🤖 LLM: {'Sim' if usar_llm else 'Não'}")
    print()
    
    # Lê arquivo bruto
    print("📖 Lendo transcrição bruta...")
    segmentos = extrair_segmentos_do_arquivo_bruto(caminho_arquivo_bruto)
    print(f"✓ {len(segmentos)} segmentos carregados")
    
    # Aplica melhorias
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
    segmentos = segmentar_por_topicos(segmentos, max_chars_bloco)
    
    # 4. Pós-correção com LLM (opcional)
    if usar_llm and llm_api_key:
        print("   ✓ Aplicando correção semântica com LLM...")
        for seg in segmentos:
            seg['text'] = corrigir_com_llm(seg['text'], llm_api_key)
    
    # Organiza por tópicos
    print("   ✓ Organizando por tópicos...")
    transcricao_organizada = organizar_por_topicos(segmentos)
    
    # Salva resultado final
    nome_base = Path(caminho_arquivo_bruto).stem.replace('_transcricao_bruta', '')
    arquivo_final = f"{nome_base}_avancado.txt"
    
    # Lê metadados do arquivo bruto
    metadados = ler_metadados_arquivo_bruto(caminho_arquivo_bruto)
    
    salvar_transcricao_organizada(arquivo_final, transcricao_organizada, {
        'arquivo': metadados.get('arquivo', os.path.basename(caminho_arquivo_bruto)),
        'modelo': metadados.get('modelo', 'N/A'),
        'modo_limpeza': modo_limpeza,
        'pyannote': metadados.get('pyannote', False),
        'llm': usar_llm
    })
    
    print("\n" + "="*70)
    print("✅ ETAPA 2 CONCLUÍDA")
    print("="*70)
    print(f"📄 Arquivo final: {arquivo_final}")
    print(f"📊 Segmentos: {len(segmentos)}")
    print(f"🎤 Speakers: {len(set(s.get('speaker', 'Speaker 1') for s in segmentos))}")
    print(f"📑 Tópicos: {len(transcricao_organizada)}")
    print("="*70)
    
    return {
        'arquivo_final': arquivo_final,
        'segmentos': segmentos,
        'organizada': transcricao_organizada
    }

def extrair_segmentos_do_arquivo_bruto(caminho_arquivo: str) -> List[Dict]:
    """
    Extrai segmentos de arquivo bruto gerado na etapa 1
    """
    segmentos = []
    
    with open(caminho_arquivo, 'r', encoding='utf-8') as f:
        linhas = f.readlines()
    
    timestamp_pattern = r'\[(\d+):(\d+):(\d+)\]'
    speaker_pattern = r'Speaker\s+(\d+)'
    
    segmento_atual = None
    
    for linha in linhas:
        linha = linha.strip()
        if not linha or linha.startswith('=') or linha.startswith('📁') or linha.startswith('🤖'):
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
            texto = linha.split(':', 1)[-1].strip() if ':' in linha else ''
            
            segmento_atual = {
                'start': timestamp_segundos,
                'end': timestamp_segundos + 10,
                'speaker': speaker,
                'text': texto
            }
        elif segmento_atual and linha:
            # Continua texto
            if segmento_atual['text']:
                segmento_atual['text'] += ' ' + linha
            else:
                segmento_atual['text'] = linha
    
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

def ler_metadados_arquivo_bruto(caminho_arquivo: str) -> Dict:
    """
    Lê metadados do arquivo bruto
    """
    metadados = {}
    
    with open(caminho_arquivo, 'r', encoding='utf-8') as f:
        for linha in f:
            if '📁 Arquivo:' in linha:
                metadados['arquivo'] = linha.split(':', 1)[-1].strip()
            elif '🤖 Modelo:' in linha:
                metadados['modelo'] = linha.split(':', 1)[-1].strip()
            elif '🎤 PyAnnote:' in linha:
                metadados['pyannote'] = 'Sim' in linha
    
    return metadados

# ============================================================================
# FUNÇÃO PRINCIPAL (CHAMA AS DUAS ETAPAS)
# ============================================================================

def transcrever_avancado(caminho_video: str,
                         modelo: str = "large-v3",
                         usar_pyannote: bool = True,
                         pyannote_token: Optional[str] = None,
                         modo_limpeza: str = "medio",
                         usar_llm: bool = False,
                         llm_api_key: Optional[str] = None,
                         max_chars_bloco: int = 600,
                         apenas_transcrever: bool = False,
                         apenas_corrigir: bool = False):
    """
    Função principal: Executa as duas etapas em sequência
    
    Args:
        caminho_video: Caminho do arquivo de vídeo OU arquivo bruto (se apenas_corrigir=True)
        modelo: Modelo Whisper
        usar_pyannote: Se True, usa PyAnnote para diarização
        pyannote_token: Token de autenticação PyAnnote
        modo_limpeza: "leve", "medio" ou "agressivo"
        usar_llm: Se True, usa LLM para pós-correção
        llm_api_key: API key para LLM
        max_chars_bloco: Tamanho máximo de bloco antes de dividir
        apenas_transcrever: Se True, só faz etapa 1 (transcrição)
        apenas_corrigir: Se True, só faz etapa 2 (correção) - caminho_video deve ser arquivo bruto
    """
    # Se apenas corrigir, pula direto para etapa 2
    if apenas_corrigir:
        return corrigir_e_organizar(
            caminho_video,
            modo_limpeza=modo_limpeza,
            usar_llm=usar_llm,
            llm_api_key=llm_api_key,
            max_chars_bloco=max_chars_bloco
        )
    
    # ETAPA 1: Transcrição
    resultado_etapa1 = transcrever_apenas(
        caminho_video,
        modelo=modelo,
        usar_pyannote=usar_pyannote,
        pyannote_token=pyannote_token
    )
    
    if not resultado_etapa1:
        return None
    
    # Se apenas transcrever, para aqui
    if apenas_transcrever:
        return resultado_etapa1
    
    # ETAPA 2: Correção e organização
    resultado_etapa2 = corrigir_e_organizar(
        resultado_etapa1['arquivo_bruto'],
        modo_limpeza=modo_limpeza,
        usar_llm=usar_llm,
        llm_api_key=llm_api_key,
        max_chars_bloco=max_chars_bloco
    )
    
    return resultado_etapa2

def organizar_por_topicos(segmentos: List[Dict]) -> Dict[str, List[Dict]]:
    """
    Organiza segmentos por tópicos
    """
    organizado = {}
    
    for seg in segmentos:
        topico = seg.get('topico', 'Geral')
        if topico not in organizado:
            organizado[topico] = []
        organizado[topico].append(seg)
    
    return organizado

def salvar_transcricao_organizada(arquivo: str, transcricao_organizada: Dict, metadados: Dict):
    """
    Salva transcrição organizada por tópicos
    """
    with open(arquivo, 'w', encoding='utf-8') as f:
        f.write("="*70 + "\n")
        f.write("🚀 TRANSCRIÇÃO AVANÇADA - VERSÃO FINAL\n")
        f.write("="*70 + "\n\n")
        f.write(f"📁 Arquivo: {metadados['arquivo']}\n")
        f.write(f"🤖 Modelo: {metadados['modelo']}\n")
        f.write(f"🔧 Modo limpeza: {metadados['modo_limpeza']}\n")
        f.write(f"🎤 PyAnnote: {'Sim' if metadados['pyannote'] else 'Não'}\n")
        f.write(f"🤖 LLM: {'Sim' if metadados['llm'] else 'Não'}\n")
        f.write("\n" + "="*70 + "\n")
        f.write("TRANSCRIÇÃO ORGANIZADA POR TÓPICOS\n")
        f.write("="*70 + "\n\n")
        
        # Ordena tópicos por ordem de aparição
        topicos_ordenados = sorted(transcricao_organizada.keys(), 
                                   key=lambda t: min(s['start'] for s in transcricao_organizada[t]))
        
        for topico in topicos_ordenados:
            segmentos = transcricao_organizada[topico]
            
            f.write("\n" + "="*70 + "\n")
            f.write(f"📑 {topico.upper()}\n")
            f.write("="*70 + "\n\n")
            
            speaker_anterior = None
            for seg in segmentos:
                if speaker_anterior and speaker_anterior != seg['speaker']:
                    f.write("\n")
                
                timestamp = formatar_timestamp(seg['start'])
                f.write(f"[{timestamp}] {seg['speaker']}:\n")
                f.write(f"{seg['text']}\n\n")
                
                speaker_anterior = seg['speaker']
            
            f.write("\n")

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("="*70)
        print("🚀 WHISPER AVANÇADO - VERSÃO FINAL (POR ETAPAS)")
        print("="*70)
        print("\nUso: python whisper_avancado.py <arquivo> [opções]")
        print("\nModos de execução:")
        print("  (padrão)              - Executa ETAPA 1 (transcreve) + ETAPA 2 (corrige)")
        print("  --apenas-transcrever  - Só executa ETAPA 1 (transcreve e salva bruto)")
        print("  --corrigir            - Só executa ETAPA 2 (corrige arquivo bruto)")
        print("\nOpções:")
        print("  [modelo]              - tiny, base, small, medium, large, large-v3 (padrão: large-v3)")
        print("  [modo_limpeza]        - leve, medio, agressivo (padrão: medio)")
        print("  --sem-pyannote        - Não usa PyAnnote (diarização simplificada)")
        print("  --pyannote-token TOKEN - Token de autenticação PyAnnote")
        print("  --llm                 - Usa LLM para pós-correção (requer --llm-key)")
        print("  --llm-key KEY         - API key para LLM (OpenAI)")
        print("\nExemplos:")
        print('  # Executa tudo (transcreve + corrige)')
        print('  python whisper_avancado.py "video.mp4"')
        print('')
        print('  # Só transcreve (mais rápido)')
        print('  python whisper_avancado.py "video.mp4" --apenas-transcrever')
        print('')
        print('  # Só corrige arquivo bruto já gerado')
        print('  python whisper_avancado.py "video_transcricao_bruta.txt" --corrigir')
        print('')
        print('  # Com opções')
        print('  python whisper_avancado.py "video.mp4" large-v3 medio --llm --llm-key sk-...')
        print("\nMelhorias implementadas:")
        print("  ✓ Diarização separada (PyAnnote)")
        print("  ✓ Segmentação por tópicos")
        print("  ✓ Limpeza de vícios de fala")
        print("  ✓ Normalização robusta de termos")
        print("  ✓ Pós-correção semântica (LLM opcional)")
        print("  ✓ Organização em blocos temáticos")
        print("\n💡 Dica: Use --apenas-transcrever para transcrever mais rápido,")
        print("   depois use --corrigir para aplicar melhorias quando quiser.")
        sys.exit(1)
    
    caminho = sys.argv[1].strip('"\'')
    modelo = "large-v3"
    modo_limpeza = "medio"
    usar_pyannote = True
    pyannote_token = None
    usar_llm = False
    llm_api_key = None
    apenas_transcrever = False
    apenas_corrigir = False
    
    # Processa argumentos
    i = 2
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg in ['tiny', 'base', 'small', 'medium', 'large', 'large-v3']:
            modelo = arg
        elif arg in ['leve', 'medio', 'agressivo']:
            modo_limpeza = arg
        elif arg == '--sem-pyannote':
            usar_pyannote = False
        elif arg == '--pyannote-token' and i + 1 < len(sys.argv):
            pyannote_token = sys.argv[i + 1]
            i += 1
        elif arg == '--llm':
            usar_llm = True
        elif arg == '--llm-key' and i + 1 < len(sys.argv):
            llm_api_key = sys.argv[i + 1]
            i += 1
        elif arg == '--apenas-transcrever':
            apenas_transcrever = True
        elif arg == '--corrigir':
            apenas_corrigir = True
        i += 1
    
    transcrever_avancado(
        caminho,
        modelo=modelo,
        usar_pyannote=usar_pyannote,
        pyannote_token=pyannote_token,
        modo_limpeza=modo_limpeza,
        usar_llm=usar_llm,
        llm_api_key=llm_api_key,
        apenas_transcrever=apenas_transcrever,
        apenas_corrigir=apenas_corrigir
    )

