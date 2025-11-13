"""
Script para testar o Whisper - Transcrição de Áudio e Vídeo
Usa a biblioteca openai-whisper para transcrever arquivos de áudio e vídeo

Formatos suportados:
- Áudio: MP3, WAV, M4A, FLAC, OGG, AAC, etc.
- Vídeo: MP4, AVI, MKV, MOV, WebM, etc. (extrai o áudio automaticamente)
"""

import whisper
import os
import sys
import subprocess
import time
import threading
import warnings
from pathlib import Path
from datetime import datetime
import re

# Suprime o aviso sobre FP16 não ser suportado na CPU
# O Whisper automaticamente usa FP32 quando detecta CPU
warnings.filterwarnings("ignore", message="FP16 is not supported on CPU; using FP32 instead")


def pos_processar_texto(texto: str) -> str:
    """
    Aplica pós-processamento básico para melhorar a formatação do texto
    
    Args:
        texto: Texto transcrito bruto
    
    Returns:
        Texto formatado e melhorado
    """
    if not texto:
        return texto
    
    # Remove espaços múltiplos
    texto = re.sub(r'\s+', ' ', texto)
    
    # Corrige espaçamento antes de pontuação
    texto = re.sub(r'\s+([,.!?;:])', r'\1', texto)
    
    # Adiciona espaço após pontuação se não houver
    texto = re.sub(r'([,.!?;:])([^\s])', r'\1 \2', texto)
    
    # Capitaliza primeira letra do texto
    if texto:
        texto = texto[0].upper() + texto[1:] if len(texto) > 1 else texto.upper()
    
    # Capitaliza primeira letra após ponto, exclamação ou interrogação seguidos de espaço
    def capitalizar_apos_pontuacao(match):
        return match.group(1) + match.group(2).upper()
    
    texto = re.sub(r'([.!?]\s+)([a-záàâãéêíóôõúçü])', 
                   capitalizar_apos_pontuacao, texto, flags=re.IGNORECASE)
    
    # Remove espaços no início e fim
    texto = texto.strip()
    
    return texto


def verificar_ffmpeg():
    """Verifica se o ffmpeg está instalado e disponível"""
    try:
        subprocess.run(
            ["ffmpeg", "-version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


class IndicadorProgresso:
    """Classe para mostrar um indicador de progresso animado"""
    def __init__(self, mensagem="Processando"):
        self.mensagem = mensagem
        self.rodando = False
        self.thread = None
        self.spinner_chars = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        self.indice = 0
        self.erro_ocorrido = False
    
    def _animar(self):
        """Anima o spinner"""
        try:
            while self.rodando and not self.erro_ocorrido:
                try:
                    char = self.spinner_chars[self.indice % len(self.spinner_chars)]
                    # Usa sys.stdout.write para evitar problemas no Windows
                    sys.stdout.write(f'\r{char} {self.mensagem}...')
                    sys.stdout.flush()
                    self.indice += 1
                    time.sleep(0.2)  # Reduzido de 0.1 para 0.2 para menos sobrecarga
                except (OSError, IOError) as e:
                    # Se houver erro de I/O, para silenciosamente
                    self.erro_ocorrido = True
                    break
        except Exception:
            # Qualquer outro erro, para silenciosamente
            self.erro_ocorrido = True
    
    def iniciar(self):
        """Inicia o indicador de progresso"""
        try:
            self.rodando = True
            self.erro_ocorrido = False
            self.thread = threading.Thread(target=self._animar, daemon=True)
            self.thread.start()
        except Exception:
            # Se não conseguir iniciar, apenas continua sem indicador
            self.erro_ocorrido = True
    
    def parar(self, mensagem_final="Concluído!"):
        """Para o indicador de progresso"""
        self.rodando = False
        if self.thread:
            try:
                self.thread.join(timeout=1.0)
            except Exception:
                pass
        
        try:
            # Limpa a linha e mostra mensagem final
            sys.stdout.write(f'\r✓ {mensagem_final}' + ' ' * 50 + '\n')
            sys.stdout.flush()
        except Exception:
            # Se não conseguir escrever, apenas imprime normalmente
            print(f'✓ {mensagem_final}')


def transcrever_audio(
    caminho_audio: str, 
    modelo: str = "base", 
    idioma: str = "pt",
    modo_precisao: str = "alta"
):
    """
    Transcreve um arquivo de áudio usando o Whisper com opções avançadas
    
    Args:
        caminho_audio: Caminho para o arquivo de áudio
        modelo: Modelo do Whisper a ser usado (tiny, base, small, medium, large)
        idioma: Idioma do áudio (pt para português, en para inglês, etc.)
        modo_precisao: "alta" para máxima precisão, "rapida" para velocidade
    
    Returns:
        Dicionário com o texto transcrito e informações adicionais
    """
    # Normaliza o caminho para lidar com espaços e caracteres especiais
    caminho_audio = os.path.normpath(caminho_audio)
    
    # Verifica se o arquivo existe
    if not os.path.exists(caminho_audio):
        print(f"Erro: Arquivo não encontrado: {caminho_audio}")
        print(f"Caminho absoluto verificado: {os.path.abspath(caminho_audio)}")
        return None
    
    try:
        # Carregando modelo
        indicador = IndicadorProgresso("Carregando modelo Whisper")
        indicador.iniciar()
        inicio_carregamento = time.time()
        
        model = whisper.load_model(modelo)
        
        tempo_carregamento = time.time() - inicio_carregamento
        indicador.parar(f"Modelo '{modelo}' carregado ({tempo_carregamento:.1f}s)")
        
        # Estimativa de tempo baseada no tamanho do arquivo
        tamanho_mb = os.path.getsize(caminho_audio) / (1024 * 1024)
        tempo_estimado = tamanho_mb * 2  # Estimativa: ~2 segundos por MB (varia muito)
        
        print(f"\n📁 Arquivo: {os.path.basename(caminho_audio)}")
        print(f"📊 Tamanho: {tamanho_mb:.2f} MB")
        print(f"⏱️  Tempo estimado: ~{tempo_estimado/60:.1f} minutos")
        print(f"🕐 Iniciado em: {datetime.now().strftime('%H:%M:%S')}")
        print("\n" + "-"*50)
        
        # Configurações avançadas para melhor precisão
        if modo_precisao == "alta":
            # Configurações para máxima precisão
            opcoes_transcricao = {
                "language": idioma,
                "task": "transcribe",
                "temperature": 0.0,  # 0.0 = mais determinístico, menos criativo
                "beam_size": 5,  # Maior = mais preciso, mais lento
                "best_of": 5,  # Número de candidatos a considerar
                "patience": 1.0,  # Paciência para decodificação
                "length_penalty": 1.0,  # Penalidade de comprimento
                "suppress_tokens": "-1",  # Suprime tokens especiais
                "initial_prompt": "Esta é uma transcrição de uma reunião em português brasileiro." if idioma == "pt" else None,
                "word_timestamps": True,  # Timestamps por palavra para melhor segmentação
                "condition_on_previous_text": True,  # Usa contexto anterior
            }
            print("🔧 Modo: Alta Precisão (pode levar mais tempo)")
        else:
            # Configurações para velocidade
            opcoes_transcricao = {
                "language": idioma,
                "task": "transcribe",
                "temperature": 0.0,
                "beam_size": 3,
                "best_of": 3,
                "word_timestamps": False,
            }
            print("⚡ Modo: Rápido")
        
        # Transcrevendo
        indicador = IndicadorProgresso("Transcrevendo áudio")
        indicador.iniciar()
        inicio_transcricao = time.time()
        
        resultado = model.transcribe(caminho_audio, **opcoes_transcricao)
        
        tempo_transcricao = time.time() - inicio_transcricao
        indicador.parar(f"Transcrição concluída ({tempo_transcricao/60:.1f} minutos)")
        
        # Estatísticas
        duracao_audio = resultado.get('duration', 0)
        texto_bruto = resultado.get('text', '')
        
        # Pós-processamento básico para melhorar a formatação
        texto_formatado = pos_processar_texto(texto_bruto)
        
        num_palavras = len(texto_formatado.split()) if texto_formatado else 0
        
        # Estatísticas de qualidade
        segments = resultado.get('segments', [])
        num_segmentos = len(segments)
        confianca_media = sum(s.get('no_speech_prob', 0) for s in segments) / num_segmentos if num_segmentos > 0 else 0
        confianca_media = (1 - confianca_media) * 100  # Converte para porcentagem de confiança
        
        print("\n" + "="*50)
        print("📈 ESTATÍSTICAS")
        print("="*50)
        print(f"Duração do áudio: {duracao_audio/60:.1f} minutos")
        print(f"Tempo de processamento: {tempo_transcricao/60:.1f} minutos")
        print(f"Velocidade: {duracao_audio/tempo_transcricao:.2f}x (tempo real)")
        print(f"Palavras transcritas: {num_palavras}")
        print(f"Segmentos: {num_segmentos}")
        print(f"Confiança média: {confianca_media:.1f}%")
        print(f"Idioma detectado: {resultado.get('language', 'N/A')}")
        
        print("\n" + "="*50)
        print("📝 TRANSCRIÇÃO (FORMATADA):")
        print("="*50)
        print(texto_formatado)
        print("="*50)
        
        # Atualiza o resultado com texto formatado
        resultado['text'] = texto_formatado
        resultado['text_raw'] = texto_bruto
        
        return resultado
        
    except FileNotFoundError as e:
        print(f"\n❌ Erro: Arquivo não encontrado: {caminho_audio}")
        print(f"Detalhes: {str(e)}")
        return None
    except Exception as e:
        print(f"\n❌ Erro ao transcrever: {str(e)}")
        print(f"Tipo de erro: {type(e).__name__}")
        if "ffmpeg" in str(e).lower():
            print("\n💡 Dica: O Whisper precisa do ffmpeg para processar arquivos de vídeo.")
            print("Instale o ffmpeg: https://ffmpeg.org/download.html")
        return None


def main():
    """Função principal"""
    print("="*50)
    print("TESTE DO WHISPER - TRANSCRIÇÃO DE ÁUDIO E VÍDEO")
    print("="*50)
    print()
    
    # Verifica se o ffmpeg está disponível
    if not verificar_ffmpeg():
        print("AVISO: ffmpeg não encontrado!")
        print("O ffmpeg é necessário para processar arquivos de vídeo.")
        print("Baixe em: https://ffmpeg.org/download.html")
        print("Ou instale via: winget install ffmpeg")
        resposta = input("\nDeseja continuar mesmo assim? (s/n): ").strip().lower()
        if resposta != 's':
            return
        print()
    
    # Verifica se foi passado um arquivo como argumento
    if len(sys.argv) > 1:
        caminho_audio = sys.argv[1]
    else:
        # Solicita o caminho do arquivo
        caminho_audio = input("Digite o caminho do arquivo de áudio ou vídeo: ").strip()
    
    # Remove aspas se houver
    caminho_audio = caminho_audio.strip('"\'')
    
    # Tenta converter para caminho absoluto
    if not os.path.isabs(caminho_audio):
        caminho_audio = os.path.abspath(caminho_audio)
    else:
        caminho_audio = os.path.normpath(caminho_audio)
    
    # Verifica se o arquivo existe
    if not os.path.exists(caminho_audio):
        print(f"Erro: Arquivo não encontrado: {caminho_audio}")
        print(f"Caminho absoluto verificado: {os.path.abspath(caminho_audio)}")
        print("\nDica: Verifique se o caminho está correto e se o arquivo existe.")
        return
    
    print(f"✓ Arquivo encontrado: {os.path.basename(caminho_audio)}")
    tamanho_mb = os.path.getsize(caminho_audio) / (1024 * 1024)
    print(f"📦 Tamanho: {tamanho_mb:.2f} MB")
    
    # Opções de modelo
    print("\nModelos disponíveis:")
    print("  - tiny: Mais rápido, menos preciso (~39M parâmetros)")
    print("  - base: Equilíbrio entre velocidade e precisão (~74M parâmetros)")
    print("  - small: Mais preciso, mais lento (~244M parâmetros) ⭐ RECOMENDADO")
    print("  - medium: Ainda mais preciso (~769M parâmetros)")
    print("  - large: Mais preciso, mais lento (~1550M parâmetros)")
    
    modelo = input("\nEscolha o modelo (padrão: small): ").strip() or "small"
    
    # Idioma
    idioma = input("Idioma do áudio (pt/en/es, padrão: pt): ").strip() or "pt"
    
    # Modo de precisão
    print("\nModos de transcrição:")
    print("  - alta: Máxima precisão (recomendado para uso profissional)")
    print("  - rapida: Velocidade otimizada")
    
    modo_precisao = input("Escolha o modo (padrão: alta): ").strip().lower() or "alta"
    if modo_precisao not in ["alta", "rapida"]:
        modo_precisao = "alta"
    
    # Transcreve o áudio
    resultado = transcrever_audio(caminho_audio, modelo, idioma, modo_precisao)
    
    if resultado:
        # Salva o resultado em um arquivo de texto
        arquivo_saida = Path(caminho_audio).stem + "_transcricao.txt"
        with open(arquivo_saida, "w", encoding="utf-8") as f:
            f.write("TRANSCRIÇÃO DO ÁUDIO/VÍDEO\n")
            f.write("="*50 + "\n\n")
            f.write(resultado["text"])
            f.write("\n\n" + "="*50 + "\n")
            f.write("DETALHES:\n")
            f.write(f"Idioma detectado: {resultado.get('language', 'N/A')}\n")
            f.write(f"Duração: {resultado.get('duration', 'N/A')} segundos\n")
            f.write(f"Modelo usado: {modelo}\n")
            f.write(f"Modo: {modo_precisao}\n")
            if 'segments' in resultado:
                f.write(f"Segmentos: {len(resultado['segments'])}\n")
        
        print(f"\n💾 Transcrição salva em: {arquivo_saida}")
        print(f"🕐 Concluído em: {datetime.now().strftime('%H:%M:%S')}")
        print("\n✅ Teste concluído com sucesso!")


if __name__ == "__main__":
    main()

