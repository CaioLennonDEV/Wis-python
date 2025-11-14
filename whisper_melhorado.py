"""
Whisper MELHORADO - Transcrição de Alta Qualidade com Correções
Implementa todas as melhorias sugeridas:
- Modelo large-v3 (máxima acurácia)
- Correção semântica pós-processamento
- Glossário de termos técnicos
- Diarização melhorada
- Post-processamento estruturado
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
from typing import List, Dict, Optional
import warnings
warnings.filterwarnings("ignore")

# ============================================================================
# GLOSSÁRIO DE TERMOS TÉCNICOS (Hotwords)
# ============================================================================
GLOSSARIO_TERMOS = [
    "pitch", "MVP", "Storytelling", "Impulsione", 
    "call to action", "ROI", "payback",
    "prontuário", "fluxograma", "slides",
    "chatGPT", "ChatGPT", "protótipo",
    "prototipo", "validação", "piloto",
    "cooperativa", "Unimed", "banca",
    "mentoria", "mentories", "prepitch",
    "pre-pitch", "Distrito 28", "hub"
]

# ============================================================================
# DICIONÁRIO DE CORREÇÕES COMUNS
# ============================================================================
CORRECOES_AUTOMATICAS = {
    # Erros comuns identificados na transcrição Beta
    "bit": "pitch",
    "chat IPT": "ChatGPT",
    "chat IPT": "ChatGPT",
    "exides": "slides",
    "story télia": "Storytelling",
    "story tell": "Storytelling",
    "storytel": "Storytelling",
    "Impulsionian": "Impulsione",
    "estrocesse": "trouxessem",
    "estrocesse": "trouxessem",
    "exágio": "exagio",
    "destaquezinhos": "destaques",
    "exide": "slide",
    "exides": "slides",
    "pitt": "pitch",
    "pitts": "pitches",
    "PIT": "pitch",
    "PTIP": "pitch",
    "prontuário": "prontuário",  # manter correto
    "fluxo-grama": "fluxograma",
    "fluxo grama": "fluxograma",
    "pronto arimétrico": "prontuário eletrônico",
    "capitalá": "capilar",
    "Cháx": "Sharks",
    "Cháx": "Sharks",
    "smart money": "smart money",  # manter
    "Anuletícia": "Anelícia",  # nome próprio
    "Libardo": "Libardoni",  # nome próprio
    "Alisson Askel": "Alisson Askel",  # manter
    "Solta Beauty": "Solta Beauty",  # manter
    "fris": "frizz",
    "prepitch": "pre-pitch",
    "prepit": "pre-pitch",
    "prepit": "pre-pitch",
    "prepitch": "pre-pitch",
    "mentories": "mentorias",
    "mentorie": "mentoria",
    "Distrito 28": "Distrito 28",  # manter
    "hub": "hub",  # manter
    "Siak": "SIAC",  # possível correção
    "Ibama": "IBAMA",  # manter
    "IFs": "IFS",  # possível correção
    "Gloo": "Glow",  # possível correção
    "Bibutton": "Bibutton",  # manter
    "Constituição Livre": "Constituição Livre",  # manter
    "Iato": "Iato",  # manter
    "Yuri": "Yuri",  # manter
    "Lucas": "Lucas",  # manter
    "Isabela": "Isabela",  # manter
    "Bruno": "Bruno",  # manter
    "Isis": "Isis",  # manter
    "Rafa": "Rafa",  # manter
    "Fabiano": "Fabiano",  # manter
    "Jean": "Jean",  # manter
    "Caio": "Caio",  # manter
    "Yuri": "Yuri",  # manter
}

# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================

def formatar_timestamp(segundos):
    """Converte segundos em formato HH:MM:SS"""
    return str(timedelta(seconds=int(segundos)))

def carregar_glossario_personalizado(caminho_arquivo: Optional[str] = None) -> List[str]:
    """
    Carrega glossário personalizado de arquivo JSON (opcional)
    Formato: {"termos": ["termo1", "termo2", ...]}
    """
    if caminho_arquivo and os.path.exists(caminho_arquivo):
        try:
            with open(caminho_arquivo, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('termos', [])
        except Exception as e:
            print(f"⚠️  Erro ao carregar glossário: {e}")
    return []

# ============================================================================
# CORREÇÃO SEMÂNTICA
# ============================================================================

def corrigir_palavras_distorcidas(texto: str, correcoes: Dict[str, str]) -> str:
    """
    Corrige palavras distorcidas usando dicionário de correções
    Mantém contexto e não altera palavras que fazem sentido
    """
    texto_corrigido = texto
    
    # Aplica correções (case-insensitive, mas preserva capitalização)
    for erro, correcao in correcoes.items():
        # Busca palavra completa (não substring)
        pattern = r'\b' + re.escape(erro) + r'\b'
        texto_corrigido = re.sub(pattern, correcao, texto_corrigido, flags=re.IGNORECASE)
    
    return texto_corrigido

def corrigir_termos_tecnicos(texto: str, glossario: List[str]) -> str:
    """
    Força reconhecimento de termos técnicos do glossário
    Tenta identificar variações comuns e corrigir
    """
    texto_corrigido = texto
    
    # Mapeia termos do glossário para variações comuns
    variacoes = {
        "pitch": ["bit", "pitt", "pit", "PIT", "PTIP"],
        "ChatGPT": ["chat IPT", "chat ipt", "chatGPT"],
        "slides": ["exides", "exide", "slids"],
        "Storytelling": ["story télia", "story tell", "storytel"],
        "Impulsione": ["Impulsionian", "impulsione"],
        "fluxograma": ["fluxo-grama", "fluxo grama"],
        "prontuário": ["pronto arimétrico", "prontuário"],
    }
    
    for termo_correto, variacoes_erradas in variacoes.items():
        if termo_correto.lower() in [t.lower() for t in glossario]:
            for variacao in variacoes_erradas:
                pattern = r'\b' + re.escape(variacao) + r'\b'
                texto_corrigido = re.sub(pattern, termo_correto, texto_corrigido, flags=re.IGNORECASE)
    
    return texto_corrigido

def corrigir_concordancia_basica(texto: str) -> str:
    """
    Correções básicas de concordância e fluidez
    """
    # Remove espaços duplos
    texto = re.sub(r'\s+', ' ', texto)
    
    # Corrige pontuação dupla
    texto = re.sub(r'([.!?])\1+', r'\1', texto)
    
    # Adiciona espaço após pontuação se necessário
    texto = re.sub(r'([.!?])([A-Za-z])', r'\1 \2', texto)
    
    # Remove espaços antes de pontuação
    texto = re.sub(r'\s+([,.!?;:])', r'\1', texto)
    
    return texto.strip()

def aplicar_correcao_semantica(texto: str, modo: str = "medio") -> str:
    """
    Aplica correção semântica completa
    
    Modos:
    - "leve": Apenas correções automáticas básicas
    - "medio": Correções automáticas + termos técnicos (RECOMENDADO)
    - "agressivo": Todas as correções + ajustes de concordância
    """
    if modo == "leve":
        texto = corrigir_palavras_distorcidas(texto, CORRECOES_AUTOMATICAS)
    elif modo == "medio":
        texto = corrigir_palavras_distorcidas(texto, CORRECOES_AUTOMATICAS)
        texto = corrigir_termos_tecnicos(texto, GLOSSARIO_TERMOS)
    elif modo == "agressivo":
        texto = corrigir_palavras_distorcidas(texto, CORRECOES_AUTOMATICAS)
        texto = corrigir_termos_tecnicos(texto, GLOSSARIO_TERMOS)
        texto = corrigir_concordancia_basica(texto)
    
    return texto

# ============================================================================
# DIARIZAÇÃO MELHORADA
# ============================================================================

def detectar_speakers_melhorado(segments: List[Dict], 
                                threshold_pausa: float = 2.5,
                                threshold_energia: float = 0.3,
                                min_duracao_fala: float = 0.5) -> List[Dict]:
    """
    Detecta mudanças de speaker com algoritmo melhorado
    
    Melhorias:
    - Considera duração mínima de fala
    - Analisa padrões de energia
    - Detecta mudanças mais precisas
    """
    if not segments:
        return []
    
    speakers = []
    speaker_atual = 1
    
    for i, seg in enumerate(segments):
        # Ignora segmentos muito curtos (provavelmente ruído)
        if seg.get('end', 0) - seg.get('start', 0) < min_duracao_fala:
            continue
        
        if i == 0:
            speakers.append({
                'speaker': f'Speaker {speaker_atual}',
                'start': seg['start'],
                'end': seg['end'],
                'text': seg['text'].strip(),
                'confidence': seg.get('no_speech_prob', 0.5)
            })
        else:
            pausa = seg['start'] - segments[i-1]['end']
            
            # Probabilidade de não ser fala (quanto maior, mais silêncio)
            prob_silencioso_atual = seg.get('no_speech_prob', 0.5)
            prob_silencioso_anterior = segments[i-1].get('no_speech_prob', 0.5)
            
            # Mudança de energia/volume
            mudanca_energia = abs(prob_silencioso_atual - prob_silencioso_anterior)
            
            # Critérios para mudança de speaker
            mudou_speaker = False
            
            # Critério 1: Pausa longa (indicador forte)
            if pausa > threshold_pausa:
                mudou_speaker = True
            
            # Critério 2: Mudança brusca de energia + pausa média
            elif mudanca_energia > threshold_energia and pausa > 1.0:
                mudou_speaker = True
            
            # Critério 3: Pausa média + alta confiança de fala anterior
            elif pausa > 1.5 and prob_silencioso_anterior < 0.3:
                mudou_speaker = True
            
            if mudou_speaker:
                speaker_atual += 1
            
            speakers.append({
                'speaker': f'Speaker {speaker_atual}',
                'start': seg['start'],
                'end': seg['end'],
                'text': seg['text'].strip(),
                'confidence': prob_silencioso_atual,
                'pausa_anterior': pausa
            })
    
    return speakers

def agrupar_speakers_inteligente(speaker_segments: List[Dict],
                                 max_pausa_agrupamento: float = 2.0) -> List[Dict]:
    """
    Agrupa segmentos do mesmo speaker de forma inteligente
    Considera pausas e contexto
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
    
    for seg in speaker_segments[1:]:
        pausa = seg.get('pausa_anterior', 0)
        
        # Agrupa se mesmo speaker e pausa curta
        if (seg['speaker'] == grupo_atual['speaker'] and 
            pausa < max_pausa_agrupamento):
            grupo_atual['end'] = seg['end']
            # Adiciona espaço entre segmentos
            if grupo_atual['text'] and seg['text']:
                grupo_atual['text'] += ' ' + seg['text']
            else:
                grupo_atual['text'] += seg['text']
        else:
            # Salva grupo atual
            if grupo_atual['text'].strip():
                agrupados.append(grupo_atual)
            
            # Inicia novo grupo
            grupo_atual = {
                'speaker': seg['speaker'],
                'start': seg['start'],
                'end': seg['end'],
                'text': seg['text']
            }
    
    # Adiciona último grupo
    if grupo_atual['text'].strip():
        agrupados.append(grupo_atual)
    
    return agrupados

# ============================================================================
# TRANSCRIÇÃO MELHORADA
# ============================================================================

def transcrever_melhorado(caminho_video: str,
                         modelo: str = "large-v3",
                         modo_correcao: str = "medio",
                         glossario_personalizado: Optional[str] = None,
                         preservar_original: bool = False):
    """
    Transcrição melhorada com todas as otimizações
    
    Args:
        caminho_video: Caminho do arquivo de vídeo/áudio
        modelo: Modelo Whisper (large-v3 recomendado)
        modo_correcao: "leve", "medio" ou "agressivo"
        glossario_personalizado: Caminho para arquivo JSON com termos adicionais
        preservar_original: Se True, mantém texto original sem correções
    """
    print("="*70)
    print("🎯 WHISPER MELHORADO - TRANSCRIÇÃO DE ALTA QUALIDADE")
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
    
    # Carrega glossário personalizado se fornecido
    glossario_completo = GLOSSARIO_TERMOS.copy()
    if glossario_personalizado:
        termos_extras = carregar_glossario_personalizado(glossario_personalizado)
        glossario_completo.extend(termos_extras)
        print(f"📚 Glossário: {len(glossario_completo)} termos")
    
    print(f"🤖 Modelo: {modelo}")
    print(f"🔧 Modo correção: {modo_correcao}")
    print(f"💾 Preservar original: {preservar_original}")
    print()
    
    try:
        # Carrega modelo
        print("📥 Carregando modelo Whisper...")
        inicio_carga = time.time()
        
        # Tenta carregar large-v3, fallback para large
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
        
        # Transcreve
        print(f"🎙️  Iniciando transcrição às {datetime.now().strftime('%H:%M:%S')}")
        print("⏳ Processando...")
        print()
        
        inicio = time.time()
        
        # Configurações otimizadas para QUALIDADE (não velocidade)
        resultado = model.transcribe(
            caminho_video,
            language='pt',
            task='transcribe',
            fp16=tem_gpu,
            verbose=True,
            # Configurações para máxima qualidade
            word_timestamps=True,  # Importante para diarização
            condition_on_previous_text=True,  # Melhora contexto
            temperature=0.0,  # Determinístico
            beam_size=5,  # Maior = melhor qualidade
            best_of=5,
            patience=1.0,
            length_penalty=1.0,
            compression_ratio_threshold=2.4,
            logprob_threshold=-1.0,
            no_speech_threshold=0.6,
            # Initial prompt com termos técnicos
            initial_prompt=" ".join(glossario_completo[:20]) if glossario_completo else None,
        )
        
        tempo_total = time.time() - inicio
        duracao = resultado.get('duration', 0) / 60
        
        print(f"\n✓ Transcrição concluída em {tempo_total/60:.1f} minutos")
        print()
        
        # Processa segments
        segments = resultado.get('segments', [])
        print(f"📊 Segmentos brutos: {len(segments)}")
        
        # Detecta speakers
        print("🔍 Detectando speakers (algoritmo melhorado)...")
        speaker_segments = detectar_speakers_melhorado(segments)
        print(f"✓ Speakers detectados: {len(set(s['speaker'] for s in speaker_segments))}")
        
        # Agrupa speakers
        print("📊 Agrupando falas...")
        speaker_agrupado = agrupar_speakers_inteligente(speaker_segments)
        print(f"✓ Segmentos agrupados: {len(speaker_agrupado)}")
        
        # Aplica correções
        if not preservar_original:
            print(f"🔧 Aplicando correções semânticas (modo: {modo_correcao})...")
            for seg in speaker_agrupado:
                texto_original = seg['text']
                texto_corrigido = aplicar_correcao_semantica(texto_original, modo_correcao)
                seg['text'] = texto_corrigido
                seg['texto_original'] = texto_original if texto_original != texto_corrigido else None
            print("✓ Correções aplicadas")
        else:
            print("ℹ️  Modo preservar original ativado - sem correções")
        
        # Salva resultados
        nome_base = Path(caminho_video).stem
        arquivo_saida = f"{nome_base}_melhorado.txt"
        
        with open(arquivo_saida, "w", encoding="utf-8") as f:
            f.write("="*70 + "\n")
            f.write("🎯 TRANSCRIÇÃO MELHORADA\n")
            f.write("="*70 + "\n\n")
            f.write(f"📁 Arquivo: {os.path.basename(caminho_video)}\n")
            f.write(f"🤖 Modelo: {modelo}\n")
            f.write(f"🔧 Modo correção: {modo_correcao}\n")
            f.write(f"⏱️  Duração: {duracao:.1f} min\n")
            f.write(f"⚡ Tempo processamento: {tempo_total/60:.1f} min\n")
            f.write(f"🎤 Speakers: {len(set(s['speaker'] for s in speaker_agrupado))}\n")
            f.write(f"📚 Termos do glossário: {len(glossario_completo)}\n")
            f.write("\n" + "="*70 + "\n")
            f.write("TRANSCRIÇÃO\n")
            f.write("="*70 + "\n\n")
            
            speaker_anterior = None
            for seg in speaker_agrupado:
                # Linha em branco entre speakers diferentes
                if speaker_anterior and speaker_anterior != seg['speaker']:
                    f.write("\n")
                
                timestamp = formatar_timestamp(seg['start'])
                f.write(f"[{timestamp}] {seg['speaker']}:\n")
                f.write(f"{seg['text']}\n\n")
                
                # Mostra correção se houver
                if not preservar_original and seg.get('texto_original'):
                    f.write(f"  [Corrigido de: {seg['texto_original'][:100]}...]\n\n")
                
                speaker_anterior = seg['speaker']
        
        # Estatísticas
        num_speakers = len(set(s['speaker'] for s in speaker_agrupado))
        num_palavras = sum(len(s['text'].split()) for s in speaker_agrupado)
        
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
        print(f"⏱️  Duração: {duracao:.1f} min")
        print(f"⚡ Tempo processamento: {tempo_total/60:.1f} min")
        print(f"🚀 Velocidade: {duracao/(tempo_total/60):.1f}x tempo real")
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
        print(f"📄 {arquivo_saida}")
        print("="*70)
        
        return {
            'resultado': resultado,
            'speaker_segments': speaker_agrupado,
            'arquivo': arquivo_saida,
            'estatisticas': {
                'speakers': num_speakers,
                'palavras': num_palavras,
                'duracao_min': duracao,
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

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("="*70)
        print("🎯 WHISPER MELHORADO - TRANSCRIÇÃO DE ALTA QUALIDADE")
        print("="*70)
        print("\nUso: python whisper_melhorado.py <arquivo> [opções]")
        print("\nOpções:")
        print("  [modelo]           - tiny, base, small, medium, large, large-v3 (padrão: large-v3)")
        print("  [modo_correcao]     - leve, medio, agressivo (padrão: medio)")
        print("  [glossario.json]   - Arquivo JSON com termos adicionais")
        print("  --preservar        - Mantém texto original sem correções")
        print("\nExemplos:")
        print('  python whisper_melhorado.py "video.mp4"')
        print('  python whisper_melhorado.py "video.mp4" large-v3 medio')
        print('  python whisper_melhorado.py "video.mp4" large-v3 medio glossario.json')
        print('  python whisper_melhorado.py "video.mp4" large-v3 medio --preservar')
        print("\nMelhorias implementadas:")
        print("  ✓ Modelo large-v3 (máxima acurácia)")
        print("  ✓ Correção semântica pós-processamento")
        print("  ✓ Glossário de termos técnicos")
        print("  ✓ Diarização melhorada")
        print("  ✓ Post-processamento estruturado")
        sys.exit(1)
    
    caminho = sys.argv[1].strip('"\'')
    modelo = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith('--') else "large-v3"
    modo_correcao = sys.argv[3] if len(sys.argv) > 3 and sys.argv[3] in ['leve', 'medio', 'agressivo'] else "medio"
    glossario = None
    preservar = False
    
    # Processa argumentos
    for arg in sys.argv[2:]:
        if arg == '--preservar':
            preservar = True
        elif arg.endswith('.json'):
            glossario = arg
    
    transcrever_melhorado(
        caminho, 
        modelo=modelo,
        modo_correcao=modo_correcao,
        glossario_personalizado=glossario,
        preservar_original=preservar
    )

