"""
Dicionário de normalização - VERSÃO COMPLETA E PROFISSIONAL
"""

# Termos técnicos que o Whisper erra
NORMALIZE_TERMOS = {
    # ChatGPT variações
    "chat IPT": "ChatGPT",
    "chat ipt": "ChatGPT",
    "chat gpt": "ChatGPT",
    "chatgpt": "ChatGPT",
    "chat GPT": "ChatGPT",
    "xatipt": "ChatGPT",
    "chat i p t": "ChatGPT",
    
    # Storytelling variações
    "história intérprete": "storytelling",
    "story intérprete": "storytelling",
    "story télia": "storytelling",
    "história télia": "storytelling",
    "estória telling": "storytelling",
    "story telling": "storytelling",
    "estorytelling": "storytelling",
    "história telling": "storytelling",
    
    # Pitch variações
    "pepit": "pré-pitch",
    "prepit": "pré-pitch",
    "pre pitch": "pré-pitch",
    "prepitch": "pré-pitch",
    "pré pitch": "pré-pitch",
    "prépit": "pré-pitch",
    "pre-pit": "pré-pitch",
    
    # Impulsione
    "impusione": "Impulsione",
    "impulsione": "Impulsione",
    "impulsionian": "Impulsione",
    "impulsionan": "Impulsione",
    "impulsiona": "Impulsione",
    
    # Solta Beauty
    "solta beauty": "Solta Beauty",
    "solta beuty": "Solta Beauty",
    "solta biuti": "Solta Beauty",
    
    # MVP
    "mvp": "MVP",
    "m v p": "MVP",
    "eme vê pê": "MVP",
    "m.v.p": "MVP",
    
    # ROI
    "roi": "ROI",
    "r o i": "ROI",
    "erre o i": "ROI",
    "r.o.i": "ROI",
    "captaROInvestimento": "capta ROI investimento",
    
    # Call to action
    "call to action": "call-to-action",
    "call tu action": "call-to-action",
    "coletivo": "call-to-action",
    "call tu éction": "call-to-action",
    
    # Payback
    "pay back": "payback",
    "pei back": "payback",
    "peiback": "payback",
    
    # Validação
    "provalidação": "pró-validação",
    "pro validação": "pró-validação",
    
    # Outros erros comuns
    "exágio": "exemplo",
    "distrinchar": "destrinchar",
    "destrinchan": "destrinchar",
    
    # Termos técnicos corretos
    "prontuário": "prontuário",
    "fluxograma": "fluxograma",
    "slides": "slides",
    "protótipo": "protótipo",
    "validação": "validação",
    "piloto": "piloto",
    "cooperativa": "cooperativa",
    "unimed": "Unimed",
    "banca": "banca",
    "mentoria": "mentoria",
    "distrito 28": "Distrito 28",
    "hub": "hub",
    "siac": "SIAC",
    "ibama": "IBAMA",
    "ifs": "IFS",
}

# Vícios de fala para remover (ordem importa!)
VICIOS_FALA_LEVE = [
    r'\bné\?',
    r'\btá\?',
    r'\bah\b',
    r'\boh\b',
    r'\beh\b',
]

VICIOS_FALA_MEDIO = VICIOS_FALA_LEVE + [
    r'\bné\b',
    r'\btá\b',
    r'\btipo\b',
    r'\bassim\b',
    r'\bsabe\b',
    r'\bentendeu\b',
    r'\bpois é\b',
]

VICIOS_FALA_AGRESSIVO = VICIOS_FALA_MEDIO + [
    r'\bentão\b',
    r'\benfim\b',
    r'\bé\.\.\.+',
    r'\buh\b',
    r'\bahn\b',
    r'\bcara\b',
    r'\bmano\b',
    r'\bvelho\b',
]

# Padrões de limpeza
PADROES_LIMPEZA = {
    # Remove timestamps duplicados/quebrados
    r'\d{1,2}\]\s*Speaker': '[TIMESTAMP] Speaker',  # Temporário
    r'^\d{1,2}\]\s*': '',  # Remove números soltos no início
    r'\s+\d{1,2}\]\s*Speaker': ' [TIMESTAMP] Speaker',  # Temporário
    
    # Limpa espaços
    r'\s+': ' ',
    r'\s+([.,!?;:])': r'\1',
    r'([.,!?])([A-ZÁÉÍÓÚÂÊÔÃÕ])': r'\1 \2',
    
    # Limpa pontuação duplicada
    r'\.{2,}': '.',
    r'\?{2,}': '?',
    r'!{2,}': '!',
    r',{2,}': ',',
    
    # Remove espaços antes/depois de parênteses
    r'\s*\(\s*': ' (',
    r'\s*\)\s*': ') ',
}

# Padrões de timestamp válido
TIMESTAMP_PATTERN = r'\[(\d{1,2}):(\d{2}):(\d{2})\]'
TIMESTAMP_INVALIDO = r'(?<!\[)\d{1,2}\]\s*Speaker'
