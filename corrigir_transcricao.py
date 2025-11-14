"""
Script para corrigir transcrições existentes
Aplica correções semânticas em arquivos de transcrição já gerados
"""
import sys
import os
import re
import json
from pathlib import Path
from whisper_melhorado import (
    CORRECOES_AUTOMATICAS,
    GLOSSARIO_TERMOS,
    aplicar_correcao_semantica,
    corrigir_termos_tecnicos,
    corrigir_palavras_distorcidas
)

def processar_arquivo_transcricao(caminho_arquivo: str, 
                                   modo_correcao: str = "medio",
                                   salvar_backup: bool = True):
    """
    Processa arquivo de transcrição existente e aplica correções
    
    Args:
        caminho_arquivo: Caminho do arquivo .txt de transcrição
        modo_correcao: "leve", "medio" ou "agressivo"
        salvar_backup: Se True, cria backup do arquivo original
    """
    if not os.path.exists(caminho_arquivo):
        print(f"❌ Arquivo não encontrado: {caminho_arquivo}")
        return None
    
    print("="*70)
    print("🔧 CORREÇÃO DE TRANSCRIÇÃO EXISTENTE")
    print("="*70)
    print()
    print(f"📁 Arquivo: {caminho_arquivo}")
    print(f"🔧 Modo: {modo_correcao}")
    print()
    
    # Lê arquivo original
    with open(caminho_arquivo, 'r', encoding='utf-8') as f:
        conteudo_original = f.read()
    
    # Cria backup se solicitado
    if salvar_backup:
        backup_path = f"{caminho_arquivo}.backup"
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(conteudo_original)
        print(f"💾 Backup criado: {backup_path}")
    
    # Processa linha por linha
    linhas = conteudo_original.split('\n')
    linhas_corrigidas = []
    correcoes_aplicadas = 0
    
    for linha in linhas:
        linha_original = linha
        
        # Detecta se é linha de texto (não timestamp ou header)
        if linha.strip() and not linha.strip().startswith('[') and not linha.strip().startswith('='):
            # Aplica correções
            linha_corrigida = aplicar_correcao_semantica(linha, modo_correcao)
            
            if linha_corrigida != linha_original:
                correcoes_aplicadas += 1
                # Opcional: mostra correção
                if correcoes_aplicadas <= 10:  # Mostra primeiras 10
                    print(f"  ✓ Corrigido: '{linha_original[:60]}...' → '{linha_corrigida[:60]}...'")
            
            linhas_corrigidas.append(linha_corrigida)
        else:
            linhas_corrigidas.append(linha)
    
    # Salva arquivo corrigido
    caminho_saida = caminho_arquivo.replace('.txt', '_corrigido.txt')
    with open(caminho_saida, 'w', encoding='utf-8') as f:
        f.write('\n'.join(linhas_corrigidas))
    
    print()
    print("="*70)
    print("✅ CORREÇÃO CONCLUÍDA")
    print("="*70)
    print(f"📝 Correções aplicadas: {correcoes_aplicadas}")
    print(f"💾 Arquivo salvo: {caminho_saida}")
    print("="*70)
    
    return caminho_saida

if __name__ == "__main__":
    import os
    
    if len(sys.argv) < 2:
        print("="*70)
        print("🔧 CORREÇÃO DE TRANSCRIÇÃO EXISTENTE")
        print("="*70)
        print("\nUso: python corrigir_transcricao.py <arquivo.txt> [modo]")
        print("\nModos:")
        print("  leve      - Apenas correções básicas")
        print("  medio     - Correções básicas + termos técnicos (RECOMENDADO)")
        print("  agressivo - Todas as correções + ajustes de concordância")
        print("\nExemplos:")
        print('  python corrigir_transcricao.py "transcricao.txt"')
        print('  python corrigir_transcricao.py "transcricao.txt" agressivo')
        sys.exit(1)
    
    arquivo = sys.argv[1].strip('"\'')
    modo = sys.argv[2] if len(sys.argv) > 2 else "medio"
    
    processar_arquivo_transcricao(arquivo, modo)

