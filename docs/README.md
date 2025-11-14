# 🎙️ Whisper com Separação de Speakers

Transcrição de áudio/vídeo com identificação automática de quem está falando.

## 📋 Requisitos

```bash
pip install -r requirements.txt
```

## 🚀 Scripts Disponíveis

### 1. 🎙️ `transcrever.py` - **APENAS TRANSCREVE**

**Transcrição com Whisper - gera arquivo bruto:**
- ✅ Transcrição com Whisper (modelo large-v3)
- ✅ Diarização opcional com PyAnnote
- ✅ Gera arquivo TXT bruto (sem correções)

```bash
# Uso básico
python transcrever.py "seu_arquivo.mp4"

# Com modelo específico
python transcrever.py "video.mp4" large-v3

# Com PyAnnote (melhor diarização - requer token)
python transcrever.py "video.mp4" --pyannote-token SEU_TOKEN

# Sem PyAnnote (usa diarização simplificada)
python transcrever.py "video.mp4" --sem-pyannote
```

**Saída:** `output/video_transcricao_bruta.txt`

### 2. 🔧 `corrigir.py` - **APENAS CORRIGE**

**Corrige transcrição bruta - gera arquivo corrigido:**
- ✅ Normaliza termos técnicos
- ✅ Remove vícios de fala ("né", "tá", "enfim")
- ✅ Gera arquivo TXT corrigido

```bash
# Uso básico
python corrigir.py "output/video_transcricao_bruta.txt"

# Com modo específico
python corrigir.py "output/video_transcricao_bruta.txt" medio
```

**Modos de limpeza:**
- `leve` - Apenas limpeza básica
- `medio` - Remove vícios de fala comuns ⭐ **RECOMENDADO**
- `agressivo` - Limpeza completa + ajustes de fluidez

**Saída:** `output/video_corrigido.txt`

### 3. 📑 `organizar.py` - **APENAS ORGANIZA**

**Organiza transcrição corrigida por tópicos:**
- ✅ Segmenta por tópicos (Problema, Solução, Benefícios, etc.)
- ✅ Organiza em blocos temáticos
- ✅ Gera arquivo TXT organizado

```bash
# Uso básico
python organizar.py "output/video_corrigido.txt"
```

**Saída:** `output/video_organizado.txt`

## 📋 Fluxo de Trabalho

### Processo Completo (3 Etapas):

```bash
# ETAPA 1: Transcrever
python transcrever.py "video.mp4"
# → Gera: output/video_transcricao_bruta.txt

# ETAPA 2: Corrigir
python corrigir.py "output/video_transcricao_bruta.txt"
# → Gera: output/video_corrigido.txt

# ETAPA 3: Organizar
python organizar.py "output/video_corrigido.txt"
# → Gera: output/video_organizado.txt
```

### Vantagens da Separação:

✅ **Mais rápido** - Transcreve sem processar correções  
✅ **Flexível** - Pode reexecutar apenas correção ou organização  
✅ **Testável** - Vê resultado bruto antes de corrigir  
✅ **Modular** - Cada script faz uma coisa bem feita

## 📊 Modelos Disponíveis

- `tiny` - Muito rápido (~30s-1min para 60MB) - qualidade básica
- `base` - Rápido (~1-2 min para 60MB) - boa qualidade
- `small` - Balanceado (~2-4 min para 60MB) - ótima qualidade
- `medium` - Lento (~4-8 min para 60MB) - excelente qualidade
- `large` - Muito lento (~6-12 min para 60MB) - máxima qualidade
- `large-v3` - Muito lento (~6-12 min para 60MB) - **máxima qualidade** ⭐

## 📤 Saída

Gera arquivo `nome_do_arquivo_melhorado.txt` com:
- Timestamps precisos de cada fala
- Identificação de speakers (Speaker 1, Speaker 2, etc.)
- Texto corrigido semanticamente
- Estatísticas detalhadas por speaker
- Informações sobre correções aplicadas

## ⚡ Funcionalidades por Script

### 🎙️ `transcrever.py` - Transcrição

#### 🎤 Diarização (PyAnnote opcional)
- ✅ Diarização ANTES do Whisper - resolve 80% dos erros de speakers
- ✅ Identifica speakers corretamente usando modelo dedicado
- ✅ Transcreve cada segmento diarizado separadamente
- ✅ Fallback para diarização simplificada se PyAnnote não disponível

#### 📝 Transcrição Whisper
- ✅ Modelo large-v3 (máxima acurácia)
- ✅ Glossário de termos técnicos para melhor reconhecimento
- ✅ Word timestamps para precisão
- ✅ Gera arquivo bruto sem processamento

### 🔧 `corrigir.py` - Correção

#### 🔧 Normalização de Termos
- ✅ Dicionário completo de correções
- ✅ Normaliza termos técnicos automaticamente
- ✅ Corrige variações comuns (ex: "bit" → "pitch")

#### 🧹 Limpeza de Vícios de Fala
- ✅ Remove "né", "tá", "enfim" automaticamente
- ✅ Limpa repetições e vícios comuns
- ✅ Ajusta fluidez e concordância (modo agressivo)

### 📑 `organizar.py` - Organização

#### 📑 Segmentação por Tópicos
- ✅ **Organização automática por contexto:**
  - Apresentação, Problema, Solução, Benefícios
  - Diferencial, Time, Próximos Passos
  - Call to Action, Avaliação, Regras, Exemplo
  - Logística, Finalização
- ✅ Identifica tópicos por palavras-chave
- ✅ Divide blocos grandes automaticamente
- ✅ Transcrição estruturada como livro

## 📚 Glossário Personalizado

Crie um arquivo JSON com termos específicos do seu contexto:

```json
{
  "termos": [
    "pitch",
    "MVP",
    "Storytelling",
    "termo1",
    "termo2"
  ]
}
```

Use: `python whisper_melhorado.py "video.mp4" large-v3 medio glossario.json`

## 🔍 Exemplos de Correções

O script corrige automaticamente erros comuns:

- "bit" → "pitch"
- "chat IPT" → "ChatGPT"
- "exides" → "slides"
- "story télia" → "Storytelling"
- "Impulsionian" → "Impulsione"
- "estrocesse" → "trouxessem"

## ⚙️ Recursos Técnicos

- ✅ Detecção automática de mudança de speaker
- ✅ Agrupamento inteligente de falas
- ✅ Suporte a GPU (CUDA) para processamento rápido
- ✅ Timestamps precisos
- ✅ Estatísticas detalhadas por speaker
- ✅ Backup automático ao corrigir transcrições existentes
