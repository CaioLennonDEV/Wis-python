"""
Funções auxiliares compartilhadas entre os scripts
"""
import re
from typing import List, Dict

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

def normalizar_termos(texto: str) -> str:
    """Normaliza termos técnicos usando dicionário robusto"""
    texto_normalizado = texto
    
    for termo_correto, variacoes in NORMALIZACAO_TERMOS.items():
        for variacao in variacoes:
            pattern = r'\b' + re.escape(variacao) + r'\b'
            texto_normalizado = re.sub(pattern, termo_correto, texto_normalizado, flags=re.IGNORECASE)
    
    return texto_normalizado

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
        texto_limpo = re.sub(r'\.\.\.+', '...', texto_limpo)
        texto_limpo = re.sub(r'\s+', ' ', texto_limpo)
    
    elif modo == "medio":
        for vicio in VICIOS_FALA:
            texto_limpo = re.sub(vicio, '', texto_limpo, flags=re.IGNORECASE)
        texto_limpo = re.sub(r'\s+', ' ', texto_limpo)
        texto_limpo = re.sub(r',\s*,', ',', texto_limpo)
    
    elif modo == "agressivo":
        for vicio in VICIOS_FALA:
            texto_limpo = re.sub(vicio, '', texto_limpo, flags=re.IGNORECASE)
        texto_limpo = re.sub(r'\s+', ' ', texto_limpo)
        texto_limpo = re.sub(r'([.!?])\1+', r'\1', texto_limpo)
        texto_limpo = re.sub(r'([.!?])([A-Za-z])', r'\1 \2', texto_limpo)
        texto_limpo = re.sub(r'\s+([,.!?;:])', r'\1', texto_limpo)
    
    return texto_limpo.strip()

def identificar_topico(texto: str) -> str:
    """Identifica tópico baseado em palavras-chave"""
    texto_lower = texto.lower()
    
    scores = {}
    for topico, keywords in TOPICOS_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw.lower() in texto_lower)
        if score > 0:
            scores[topico] = score
    
    if scores:
        return max(scores.items(), key=lambda x: x[1])[0]
    
    return "Geral"

def segmentar_por_topicos(segmentos: List[Dict], max_chars: int = 600) -> List[Dict]:
    """Segmenta transcrição por tópicos e tamanho de bloco"""
    segmentos_organizados = []
    topico_atual = None
    
    for seg in segmentos:
        texto = seg.get('text', '')
        topico = identificar_topico(texto)
        
        if topico and topico != topico_atual:
            topico_atual = topico
            seg['topico'] = topico
        elif len(texto) > max_chars and topico_atual:
            seg['topico'] = topico_atual
        else:
            seg['topico'] = topico_atual or "Geral"
        
        segmentos_organizados.append(seg)
    
    return segmentos_organizados

def organizar_por_topicos(segmentos: List[Dict]) -> Dict[str, List[Dict]]:
    """Organiza segmentos por tópicos"""
    organizado = {}
    
    for seg in segmentos:
        topico = seg.get('topico', 'Geral')
        if topico not in organizado:
            organizado[topico] = []
        organizado[topico].append(seg)
    
    return organizado

def formatar_timestamp(segundos):
    """Converte segundos em formato HH:MM:SS"""
    from datetime import timedelta
    return str(timedelta(seconds=int(segundos)))

