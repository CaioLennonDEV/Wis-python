"""
LIMPEZA PROFISSIONAL - Corrige TODOS os problemas
Versão final e definitiva
"""
import sys
import os
import re
from pathlib import Path

# Dicionário completo
NORMALIZE = {
    "chat IPT": "ChatGPT", "chat ipt": "ChatGPT", "chatgpt": "ChatGPT",
    "story télia": "storytelling", "story intérprete": "storytelling",
    "pepit": "pré-pitch", "prepit": "pré-pitch", "prépit": "pré-pitch",
    "impusione": "Impulsione", "impulsionian": "Impulsione",
    "exágio": "exemplo", "distrinchar": "destrinchar",
    "provalidação": "pró-validação",
    "captaROInvestimento": "capta ROI investimento",
    "coletivo": "call-to-action",
}

# Vícios
VICIOS_AGRESSIVO = [
    r'\bné\b', r'\btá\b', r'\btipo\b', r'\bassim\b',
    r'\bsabe\b', r'\bentendeu\b', r'\bpois é\b',
    r'\bentão\b', r'\benfim\b', r'\bé\.\.\.+',
    r'\bah\b', r'\boh\b', r'\beh\b', r'\buh\b',
]

def formatar_timestamp(segundos):
    h = int(segundos // 3600)
    m = int((segundos % 3600) // 60)
    s = int(segundos % 60)
    return f"[{h}:{m:02d}:{s:02d}]"

def extrair_segmentos(arquivo):
    """Extrai segmentos do arquivo bruto"""
    with open(arquivo, 'r', encoding='utf-8') as f:
        linhas = f.readlines()
    
    segmentos = []
    seg_atual = None
    dentro = False
    
    for linha in linhas:
        l = linha.strip()
        
        # Detecta início
        if 'TRANSCRIÇÃO' in l:
            dentro = True
            continue
        
        if not dentro or not l or l.startswith('='):
            continue
        
        # Detecta [H:MM:SS] Speaker N:
        match = re.match(r'\[(\d{1,2}):(\d{2}):(\d{2})\]\s+(Speaker\s+\d+):', l)
        
        if match:
            # Salva anterior
            if seg_atual and seg_atual['text'].strip():
                segmentos.append(seg_atual)
            
            # Novo segmento
            h, m, s, speaker = match.groups()
            seg_atual = {
                'start': int(h)*3600 + int(m)*60 + int(s),
                'speaker': speaker,
                'text': ''
            }
        elif seg_atual:
            # Adiciona texto
            seg_atual['text'] += ' ' + l
    
    # Último segmento
    if seg_atual and seg_atual['text'].strip():
        segmentos.append(seg_atual)
    
    return segmentos

def limpar_profissional(arquivo, modo="agressivo"):
    """Limpeza profissional completa"""
    print("="*70)
    print("✨ LIMPEZA PROFISSIONAL")
    print("="*70)
    print()
    
    if not os.path.exists(arquivo):
        print(f"❌ Arquivo não encontrado")
        return None
    
    print(f"📁 {os.path.basename(arquivo)}")
    print(f"🔧 Modo: {modo}")
    print()
    
    # Extrai
    print("📖 Extraindo segmentos...")
    segs = extrair_segmentos(arquivo)
    print(f"✓ {len(segs)} segmentos")
    print()
    
    # Processa
    print("🔧 Processando...")
    
    # 1. Normaliza termos
    print("   1. Normalizando termos...")
    for s in segs:
        for errado, correto in NORMALIZE.items():
            s['text'] = re.sub(re.escape(errado), correto, s['text'], flags=re.IGNORECASE)
    
    # 2. Remove vícios
    print(f"   2. Removendo vícios ({modo})...")
    for s in segs:
        for vicio in VICIOS_AGRESSIVO:
            s['text'] = re.sub(vicio, '', s['text'], flags=re.IGNORECASE)
    
    # 3. Limpa
    print("   3. Limpando texto...")
    for s in segs:
        # Remove espaços múltiplos
        s['text'] = ' '.join(s['text'].split())
        # Capitaliza
        if s['text']:
            s['text'] = s['text'][0].upper() + s['text'][1:]
        # Adiciona ponto final
        if s['text'] and s['text'][-1] not in '.!?':
            s['text'] += '.'
    
    # 4. Agrupa speakers consecutivos
    print("   4. Agrupando speakers...")
    agrupados = []
    if segs:
        grupo = {'start': segs[0]['start'], 'speaker': segs[0]['speaker'], 'text': segs[0]['text']}
        
        for s in segs[1:]:
            if s['speaker'] == grupo['speaker']:
                grupo['text'] += ' ' + s['text']
            else:
                agrupados.append(grupo)
                grupo = {'start': s['start'], 'speaker': s['speaker'], 'text': s['text']}
        
        agrupados.append(grupo)
    
    segs = agrupados
    print(f"✓ {len(segs)} segmentos finais")
    print()
    
    # Salva
    nome = Path(arquivo).stem.replace('_transcricao_bruta', '').replace('_limpo', '')
    saida = f"output/{nome}_PROFISSIONAL.txt"
    
    with open(saida, 'w', encoding='utf-8') as f:
        f.write("="*70 + "\n")
        f.write("✨ TRANSCRIÇÃO PROFISSIONAL\n")
        f.write("="*70 + "\n\n")
        f.write(f"📁 Origem: {os.path.basename(arquivo)}\n")
        f.write(f"🔧 Limpeza: {modo}\n")
        f.write(f"📊 Segmentos: {len(segs)}\n")
        f.write(f"🎤 Speakers: {len(set(s['speaker'] for s in segs))}\n")
        f.write("\n" + "="*70 + "\n")
        f.write("TRANSCRIÇÃO\n")
        f.write("="*70 + "\n\n")
        
        speaker_ant = None
        for s in segs:
            if speaker_ant and speaker_ant != s['speaker']:
                f.write("\n" + "-"*70 + "\n\n")
            
            f.write(f"{formatar_timestamp(s['start'])} {s['speaker']}:\n")
            f.write(f"{s['text']}\n\n")
            
            speaker_ant = s['speaker']
    
    print("="*70)
    print("✅ LIMPEZA CONCLUÍDA")
    print("="*70)
    print(f"📄 {saida}")
    print(f"📊 {len(segs)} segmentos")
    print(f"🎤 {len(set(s['speaker'] for s in segs))} speakers")
    print("="*70)
    
    return saida

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python limpar_profissional.py <arquivo.txt> [modo]")
        print("Modos: leve, medio, agressivo (padrão: agressivo)")
        sys.exit(1)
    
    arquivo = sys.argv[1].strip('"\'')
    modo = sys.argv[2] if len(sys.argv) > 2 else "agressivo"
    
    limpar_profissional(arquivo, modo)
