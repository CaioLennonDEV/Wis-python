# Como Instalar o FFmpeg

O Whisper precisa do FFmpeg para processar arquivos de vídeo. Siga uma das opções abaixo:

## Opção 1: Usando Chocolatey (Recomendado)

Se você tem o Chocolatey instalado:

```powershell
choco install ffmpeg
```

## Opção 2: Usando Winget

```powershell
winget install ffmpeg
```

Quando solicitado, digite `Y` para aceitar os termos.

## Opção 3: Download Manual

1. Acesse: https://www.gyan.dev/ffmpeg/builds/
2. Baixe a versão "ffmpeg-release-essentials.zip"
3. Extraia o arquivo
4. Adicione a pasta `bin` ao PATH do sistema:
   - Pressione `Win + R`, digite `sysdm.cpl` e pressione Enter
   - Vá em "Avançado" > "Variáveis de Ambiente"
   - Em "Variáveis do sistema", encontre "Path" e clique em "Editar"
   - Clique em "Novo" e adicione o caminho da pasta `bin` do ffmpeg
   - Clique em "OK" em todas as janelas
5. Reinicie o terminal/PowerShell

## Verificar Instalação

Após instalar, verifique se funcionou:

```powershell
ffmpeg -version
```

Se mostrar a versão do ffmpeg, está tudo certo!

