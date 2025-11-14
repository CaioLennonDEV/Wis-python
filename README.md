# 🎙️ Whisper com Separação de Speakers

Transcrição de áudio/vídeo com identificação automática de quem está falando.

## 📋 Requisitos

```bash
pip install -r requirements.txt
```

## 🚀 Scripts Disponíveis

### 1. 🚀 `whisper_avancado.py` - **VERSÃO FINAL** ⭐⭐⭐

**Versão mais completa com TODAS as melhorias implementadas:**
- ✅ **Diarização separada** (PyAnnote antes do Whisper) - resolve 80% dos erros de speakers
- ✅ **Segmentação por tópicos** - organiza por contexto (Problema, Solução, Benefícios, etc.)
- ✅ **Limpeza de vícios de fala** - remove "né", "tá", "enfim"
- ✅ **Normalização robusta** - corrige termos técnicos automaticamente
- ✅ **Pós-correção semântica** - opcional com LLM (ChatGPT)
- ✅ **Organização em blocos temáticos** - transcrição estruturada como livro

```bash
# Uso básico (recomendado)
python whisper_avancado.py "seu_arquivo.mp4"

# Com opções
python whisper_avancado.py "video.mp4" large-v3 medio

# Com PyAnnote (melhor diarização - requer token)
python whisper_avancado.py "video.mp4" --pyannote-token SEU_TOKEN

# Com LLM para pós-correção (requer API key)
python whisper_avancado.py "video.mp4" --llm --llm-key sk-...

# Sem PyAnnote (usa diarização simplificada)
python whisper_avancado.py "video.mp4" --sem-pyannote
```

**Modos de limpeza:**
- `leve` - Apenas limpeza básica
- `medio` - Remove vícios de fala comuns ⭐ **RECOMENDADO**
- `agressivo` - Limpeza completa + ajustes de fluidez

### 2. 🎯 `whisper_melhorado.py` - Versão Intermediária

Versão melhorada com otimizações básicas:
- ✅ Modelo **large-v3** (máxima acurácia)
- ✅ **Correção semântica** pós-processamento
- ✅ **Glossário de termos técnicos** (pitch, MVP, Storytelling, etc.)
- ✅ **Diarização melhorada** (algoritmo aprimorado)
- ✅ **Post-processamento estruturado**

```bash
# Uso básico (recomendado)
python whisper_melhorado.py "seu_arquivo.mp4"

# Com opções
python whisper_melhorado.py "video.mp4" large-v3 medio

# Com glossário personalizado
python whisper_melhorado.py "video.mp4" large-v3 medio glossario_exemplo.json

# Preservar texto original (sem correções)
python whisper_melhorado.py "video.mp4" large-v3 medio --preservar
```

**Modos de correção:**
- `leve` - Apenas correções básicas
- `medio` - Correções básicas + termos técnicos ⭐ **RECOMENDADO**
- `agressivo` - Todas as correções + ajustes de concordância

### 2. 🎙️ `whisper_com_speakers.py`

Versão com separação de speakers (modelo large padrão)

```bash
python whisper_com_speakers.py "seu_arquivo.mp4"
```

### 3. ⚡ `whisper_rapido.py`

Versão otimizada para velocidade (modelo small)

```bash
python whisper_rapido.py "seu_arquivo.mp4"
```

### 4. 🔧 `corrigir_transcricao.py`

Corrige transcrições já geradas (aplica correções semânticas)

```bash
python corrigir_transcricao.py "transcricao.txt" medio
```

### 5. 📑 `organizar_transcricao.py`

Organiza transcrições existentes por tópicos e aplica todas as melhorias

```bash
python organizar_transcricao.py "transcricao.txt" medio
```

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

## ⚡ Melhorias Implementadas

### 🚀 Versão Avançada (`whisper_avancado.py`)

#### 🎤 Diarização Separada (PyAnnote)
- ✅ **Diarização ANTES do Whisper** - resolve 80% dos erros de speakers
- ✅ Identifica speakers corretamente usando modelo dedicado
- ✅ Transcreve cada segmento diarizado separadamente
- ✅ Fallback para diarização simplificada se PyAnnote não disponível

#### 📑 Segmentação por Tópicos
- ✅ **Organização automática por contexto:**
  - Apresentação, Problema, Solução, Benefícios
  - Diferencial, Time, Próximos Passos
  - Call to Action, Avaliação, Regras, Exemplo
  - Logística, Finalização
- ✅ Identifica tópicos por palavras-chave
- ✅ Divide blocos grandes automaticamente
- ✅ Transcrição estruturada como livro

#### 🧹 Limpeza de Vícios de Fala
- ✅ Remove "né", "tá", "enfim" automaticamente
- ✅ Limpa repetições e vícios comuns
- ✅ Ajusta fluidez e concordância (modo agressivo)

#### 🔧 Normalização Robusta
- ✅ Dicionário completo de correções
- ✅ Normaliza termos técnicos automaticamente
- ✅ Corrige variações comuns (ex: "bit" → "pitch")

#### 🤖 Pós-correção Semântica (LLM)
- ✅ Opcional: usa ChatGPT/LLM para correção final
- ✅ Corrige concordância e gramática
- ✅ Melhora fluidez mantendo sentido original
- ✅ Não resume - mantém conteúdo completo

### 🎯 Versão Melhorada (`whisper_melhorado.py`)

#### 🎯 Reconhecimento de Palavras
- ✅ Correção automática de palavras distorcidas
- ✅ Glossário de termos técnicos (pitch, MVP, Storytelling, etc.)
- ✅ Correção de variações comuns (ex: "bit" → "pitch")

#### 🔧 Correção Semântica
- ✅ Dicionário de correções automáticas
- ✅ Correção de termos técnicos
- ✅ Ajustes de concordância e fluidez (modo agressivo)

#### 🎤 Diarização Melhorada
- ✅ Algoritmo aprimorado de detecção de speakers
- ✅ Considera duração mínima de fala
- ✅ Analisa padrões de energia/volume
- ✅ Agrupamento inteligente de falas

#### 📝 Post-processamento
- ✅ Estruturação por timestamps
- ✅ Organização por speakers
- ✅ Preservação opcional do texto original

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
