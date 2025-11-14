"""
PIPELINE COMPLETO - Transcrição profissional em um comando
"""
import sys
import os
from transcrever_profissional import transcrever_profissional
from limpar_profissional import limpar_profissional

def pipeline_completo(
    caminho_video: str,
    modelo: str = "small",
    usar_pyannote: bool = True,
    hf_token: str = None,
    modo_limpeza: str = "medio"
):
    """
    Pipeline completo: transcrição + pós-processamento
    """
    print("="*70)
    print("🚀 PIPELINE COMPLETO")
    print("="*70)
    print()
    print(f"📁 Arquivo: {os.path.basename(caminho_video)}")
    print(f"🤖 Modelo: {modelo}")
    print(f"🎤 PyAnnote: {'Sim' if usar_pyannote else 'Não'}")
    print(f"🔧 Limpeza: {modo_limpeza}")
    print()
    print("="*70)
    print()
    
    # ETAPA 1: Transcrição
    print("📍 ETAPA 1/2: TRANSCRIÇÃO")
    print()
    
    arquivo_bruto = transcrever_profissional(
        caminho_video,
        modelo=modelo,
        usar_pyannote=usar_pyannote,
        hf_token=hf_token
    )
    
    if not arquivo_bruto:
        print("\n❌ Transcrição falhou")
        return None
    
    print()
    print("="*70)
    print()
    
    # ETAPA 2: Limpeza profissional
    print("📍 ETAPA 2/2: LIMPEZA PROFISSIONAL")
    print()
    
    arquivo_limpo = limpar_profissional(arquivo_bruto, modo_limpeza)
    
    if not arquivo_limpo:
        print("\n❌ Pós-processamento falhou")
        return None
    
    print()
    print("="*70)
    print("🎉 PIPELINE COMPLETO CONCLUÍDO")
    print("="*70)
    print()
    print("📄 Arquivos gerados:")
    print(f"   1. Bruto: {arquivo_bruto}")
    print(f"   2. Limpo: {arquivo_limpo}")
    print()
    print("✅ Transcrição profissional pronta!")
    print("="*70)
    
    return arquivo_limpo

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("="*70)
        print("🚀 PIPELINE COMPLETO")
        print("="*70)
        print("\nTranscrição profissional em um comando!")
        print("\nUso: python pipeline_completo.py <arquivo> [opções]")
        print("\nOpções:")
        print("  [modelo]           - tiny, base, small, medium, large (padrão: small)")
        print("  --sem-pyannote     - Desabilita PyAnnote")
        print("  --hf-token TOKEN   - Token HuggingFace")
        print("  --limpeza MODO     - leve, medio, agressivo (padrão: medio)")
        print("\nExemplos:")
        print('  python pipeline_completo.py "video.mp4"')
        print('  python pipeline_completo.py "video.mp4" small --limpeza agressivo')
        print('  python pipeline_completo.py "video.mp4" --hf-token hf_...')
        print('  python pipeline_completo.py "video.mp4" --sem-pyannote')
        print("\n⚡ Recomendado:")
        print('  python pipeline_completo.py "video.mp4" small')
        sys.exit(1)
    
    caminho = sys.argv[1].strip('"\'')
    modelo = "small"
    usar_pyannote = True
    hf_token = None
    modo_limpeza = "medio"
    
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
        elif arg == '--limpeza' and i + 1 < len(sys.argv):
            modo_limpeza = sys.argv[i + 1]
            i += 1
        i += 1
    
    pipeline_completo(caminho, modelo, usar_pyannote, hf_token, modo_limpeza)
