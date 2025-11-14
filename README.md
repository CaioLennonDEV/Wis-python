# 🎙️ Whisper com Separação de Speakers

Transcrição de áudio/vídeo com identificação automática de quem está falando.

## 📋 Requisitos

```bash
pip install -r requirements.txt
```

## 🚀 Uso

```bash
python whisper_com_speakers.py "seu_arquivo.mp4"
```

### Modelos disponíveis:

- `tiny` - Rápido (~1-2 min para 60MB)
- `base` - Balanceado (~2-3 min para 60MB)
- `small` - Bom (~4-6 min para 60MB)
- `medium` - Ótimo (~8-12 min para 60MB)
- `large` - Máximo (~15-20 min para 60MB) ⭐ **RECOMENDADO**

### Exemplos:

```bash
# Usando modelo padrão (large)
python whisper_com_speakers.py "reuniao.mp4"

# Especificando modelo
python whisper_com_speakers.py "reuniao.mp4" medium
```

## 📤 Saída

Gera arquivo `nome_do_arquivo_com_speakers.txt` com:
- Timestamps de cada fala
- Identificação de speakers (Speaker 1, Speaker 2, etc.)
- Opção de renomear speakers durante o processo
- Estatísticas de participação

## ⚡ Recursos

- ✅ Detecção automática de mudança de speaker
- ✅ Agrupamento inteligente de falas
- ✅ Renomeação interativa de speakers
- ✅ Estatísticas detalhadas por speaker
- ✅ Suporte a GPU (CUDA)
- ✅ Timestamps precisos
