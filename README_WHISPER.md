# Teste do Whisper - Transcrição de Áudio

Script Python simples para testar o Whisper, modelo de transcrição de áudio da OpenAI.

## Instalação

1. Instale as dependências:

```bash
pip install -r requirements.txt
```

Ou instale diretamente:

```bash
pip install openai-whisper
```

**Nota:** O Whisper requer PyTorch. Se você não tiver uma GPU NVIDIA, o PyTorch será instalado automaticamente na versão CPU.

## Uso

### Modo Interativo

Execute o script sem argumentos:

```bash
python test_whisper.py
```

O script irá solicitar:
- Caminho do arquivo de áudio ou vídeo
- Modelo a ser usado (tiny, base, small, medium, large)
- Idioma do áudio (pt, en, es, etc.)

### Modo com Argumentos

Passe o caminho do arquivo como argumento:

```bash
# Arquivo de áudio
python test_whisper.py caminho/para/audio.mp3

# Arquivo de vídeo
python test_whisper.py caminho/para/video.mp4
```

## Modelos Disponíveis

- **tiny**: Mais rápido, menos preciso (~39M parâmetros)
- **base**: Equilíbrio entre velocidade e precisão (~74M parâmetros)
- **small**: Mais preciso, mais lento (~244M parâmetros) ⭐ **RECOMENDADO**
- **medium**: Ainda mais preciso (~769M parâmetros)
- **large**: Mais preciso, mais lento (~1550M parâmetros)

**Dica:** Para melhor precisão e comparação com serviços profissionais, use o modelo **small** ou **medium** com o modo **alta precisão**.

## Modos de Transcrição

O script oferece dois modos de transcrição:

### Modo Alta Precisão (Recomendado)
- **Temperature**: 0.0 (determinístico)
- **Beam Size**: 5 (mais candidatos avaliados)
- **Best Of**: 5 (melhor resultado entre 5 tentativas)
- **Word Timestamps**: Ativado (melhor segmentação)
- **Condition on Previous Text**: Ativado (usa contexto anterior)
- **Initial Prompt**: Contexto em português brasileiro

**Ideal para:** Uso profissional, transcrições acadêmicas, reuniões importantes

### Modo Rápido
- Configurações otimizadas para velocidade
- Menor uso de recursos
- Resultado mais rápido

**Ideal para:** Testes rápidos, arquivos grandes, quando a velocidade é prioridade

## Formatos Suportados

O Whisper suporta vários formatos de **áudio e vídeo**:

### Formatos de Áudio:
- **MP3** ✅
- WAV
- M4A
- FLAC
- OGG
- AAC
- E outros formatos comuns

### Formatos de Vídeo:
- **MP4** ✅ (extrai o áudio automaticamente)
- AVI
- MKV
- MOV
- WebM
- E outros formatos comuns

**Nota:** Para processar arquivos de vídeo (como MP4), o **ffmpeg** é necessário. O Whisper extrai automaticamente a trilha de áudio do vídeo antes de transcrever.

## Melhorias de Precisão

O script inclui várias melhorias para aumentar a precisão da transcrição:

1. **Configurações Avançadas de Decodificação**
   - Beam search otimizado
   - Múltiplas tentativas (best_of)
   - Uso de contexto anterior

2. **Pós-processamento Inteligente**
   - Formatação automática de pontuação
   - Capitalização de frases
   - Correção de espaçamento
   - Melhoria na legibilidade

3. **Estatísticas de Qualidade**
   - Confiança média da transcrição
   - Número de segmentos processados
   - Métricas de qualidade

4. **Initial Prompt**
   - Contexto em português brasileiro para melhor reconhecimento

## Saída

O script irá:
1. Exibir estatísticas detalhadas (duração, velocidade, confiança)
2. Exibir a transcrição formatada no terminal
3. Salvar a transcrição formatada em um arquivo `.txt` com o mesmo nome do arquivo de áudio
4. Incluir metadados (modelo usado, modo, segmentos, etc.)

## Exemplo

```bash
python test_whisper.py audio_exemplo.mp3
```

Saída:
```
==================================================
TESTE DO WHISPER - TRANSCRIÇÃO DE ÁUDIO
==================================================

Carregando modelo Whisper: base...
Transcrevendo áudio: audio_exemplo.mp3...

==================================================
TRANSCRIÇÃO:
==================================================
Olá, este é um teste de transcrição usando o Whisper...

==================================================
Transcrição salva em: audio_exemplo_transcricao.txt
```

## Requisitos

- Python 3.8 ou superior
- **ffmpeg** (necessário para processar arquivos de vídeo)
  - Instale via: `winget install ffmpeg` ou `choco install ffmpeg`
  - Ou baixe manualmente: https://ffmpeg.org/download.html
- ~2-3 GB de espaço em disco (para o modelo base)
- ~10 GB de espaço em disco (para o modelo large)

