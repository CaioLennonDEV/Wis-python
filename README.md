# 🎙️ Sistema de Transcrição Profissional

Sistema completo de transcrição com Whisper + limpeza profissional.

## 📦 Instalação

```bash
pip install openai-whisper torch
pip install pyannote-audio  # Opcional, para diarização real
```

## 🚀 Uso Rápido

### Opção 1: Pipeline Completo (Recomendado)
```bash
python pipeline_completo.py "video.mp4" small
```

### Opção 2: Passo a Passo
```bash
# 1. Transcrever
python transcrever_profissional.py "video.mp4" small

# 2. Limpar
python limpar_profissional.py "output/video_transcricao_bruta.txt"
```

## 📁 Arquivos

- **`pipeline_completo.py`** - Faz tudo em um comando ⭐
- **`transcrever_profissional.py`** - Transcrição com Whisper
- **`limpar_profissional.py`** - Limpeza e normalização
- **`dicionario_normalizacao.py`** - Termos técnicos (personalizável)

## 🎯 Modelos Recomendados

| Modelo | Velocidade (1h) | Qualidade |
|--------|----------------|-----------|
| base   | ~5-8 min       | Boa       |
| **small** | **~8-12 min** | **Ótima ⭐** |
| medium | ~15-20 min     | Excelente |

## 💡 Dicas

1. Use **small** para 90% dos casos
2. PyAnnote só se precisar de múltiplos speakers
3. Personalize o dicionário com seus termos

## 📝 Saída

```
output/
├── video_transcricao_bruta.txt    # Transcrição bruta
└── video_PROFISSIONAL.txt         # Transcrição limpa ✨
```
