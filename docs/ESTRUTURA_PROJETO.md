# 📁 Estrutura do Projeto

## Organização de Pastas

```
Wis python/
├── docs/                    # 📚 Documentação
│   ├── README.md           # Documentação principal
│   ├── GUIA_MELHORIAS_FINAIS.md
│   ├── MELHORIAS_IMPLEMENTADAS.md
│   └── ESTRUTURA_PROJETO.md
│
├── backups/                 # 💾 Backups automáticos
│   └── *.backup            # Backups de transcrições
│
├── output/                 # 📤 Arquivos processados
│   ├── *_transcricao_bruta.txt    # Transcrições brutas (etapa 1)
│   ├── *_corrigido.txt            # Transcrições corrigidas (etapa 2)
│   └── *_organizado.txt           # Transcrições organizadas (etapa 3)
│
├── transcrever.py          # 🎙️ Script 1: Apenas transcreve
├── corrigir.py             # 🔧 Script 2: Apenas corrige
├── organizar.py            # 📑 Script 3: Apenas organiza
├── utils.py                # ⚙️ Funções auxiliares compartilhadas
│
├── glossario_exemplo.json  # 📚 Exemplo de glossário
├── requirements.txt        # 📦 Dependências
└── .gitignore             # 🚫 Arquivos ignorados pelo Git
```

## Scripts Principais

### 1. 🎙️ `transcrever.py` - APENAS TRANSCREVE
**Função:** Transcreve vídeo/áudio com Whisper  
**Entrada:** Arquivo de vídeo/áudio (`.mp4`, `.mp3`, etc.)  
**Saída:** `output/video_transcricao_bruta.txt`

```bash
python transcrever.py "video.mp4"
```

### 2. 🔧 `corrigir.py` - APENAS CORRIGE
**Função:** Corrige transcrição bruta  
**Entrada:** Arquivo TXT bruto (`*_transcricao_bruta.txt`)  
**Saída:** `output/video_corrigido.txt`

```bash
python corrigir.py "output/video_transcricao_bruta.txt"
```

### 3. 📑 `organizar.py` - APENAS ORGANIZA
**Função:** Organiza transcrição corrigida por tópicos  
**Entrada:** Arquivo TXT corrigido (`*_corrigido.txt`)  
**Saída:** `output/video_organizado.txt`

```bash
python organizar.py "output/video_corrigido.txt"
```

## Fluxo de Trabalho

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

## Vantagens da Separação

✅ **Mais rápido** - Transcreve sem processar correções  
✅ **Flexível** - Pode reexecutar apenas correção ou organização  
✅ **Testável** - Vê resultado bruto antes de corrigir  
✅ **Modular** - Cada script faz uma coisa bem feita  
✅ **Reutilizável** - Pode corrigir/organizar arquivos antigos

## Arquivos por Etapa

### Etapa 1 (Transcrever):
- **Entrada:** `video.mp4`
- **Saída:** `output/video_transcricao_bruta.txt`
- **Conteúdo:** Transcrição bruta sem correções

### Etapa 2 (Corrigir):
- **Entrada:** `output/video_transcricao_bruta.txt`
- **Saída:** `output/video_corrigido.txt`
- **Conteúdo:** Transcrição com termos normalizados e vícios removidos

### Etapa 3 (Organizar):
- **Entrada:** `output/video_corrigido.txt`
- **Saída:** `output/video_organizado.txt`
- **Conteúdo:** Transcrição organizada por tópicos (Problema, Solução, etc.)

## Módulo Compartilhado

### `utils.py`
Contém funções auxiliares usadas por todos os scripts:
- `normalizar_termos()` - Normaliza termos técnicos
- `limpar_vicios_fala()` - Remove vícios de fala
- `identificar_topico()` - Identifica tópico por palavras-chave
- `segmentar_por_topicos()` - Segmenta por tópicos
- `organizar_por_topicos()` - Organiza em dicionário por tópico
- `formatar_timestamp()` - Formata timestamps
