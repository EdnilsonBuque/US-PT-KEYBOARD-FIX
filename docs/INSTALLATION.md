# Instalação do US-PT Keyboard Fix

## Requisitos prévios

Sistema operacional: Linux (Ubuntu, Debian, Linux Mint, Fedora com GNOME).

Dependências de sistema:
- `python3` (versão 3.8 ou superior)
- `pip3` (instalador de pacotes Python)
- `gsettings` (parte do `desktop-base` em ambientes GNOME)

Dependências Python:
- `uspt` instala automaticamente as dependências listadas em `requirements.txt` e `pyproject.toml`.

## Método recomendado (via instalador)

```bash
sudo apt update
sudo apt install git python3 -y
git clone https://github.com/SEU-USUARIO/us-pt-keyboard-fix.git
cd us-pt-keyboard-fix
chmod +x scripts/install.sh
./scripts/install.sh
```

O instalador:
1. Atualiza o índice de pacotes `apt`.
2. Instala `python3-pip` e `git` se não estiverem presentes.
3. Instala as dependências Python listadas em `requirements.txt`.
4. Copia todos os ficheiros do projeto para `~/us-pt-keyboard-fix/`.
5. Cria um wrapper `uspt` em `/usr/local/bin/uspt` (ou `~/.local/bin/uspt`).
6. Torna o wrapper executável.

## Método alternativo (manual)

```bash
# Clonar o repositório
git clone https://github.com/SEU-USUARIO/us-pt-keyboard-fix.git
cd us-pt-keyboard-fix

# Tornar o wrapper executável e disponível
chmod +x scripts/install.sh

# Ou instalar manualmente com pip
pip3 install -e .
```

## Verificar instalação

```bash
uspt --help
```

Deve listar os comandos disponíveis.

ou

```bash
python3 -m uspt.main --help
```

## Primeiros passos após instalação

1. Execute `uspt detect` para ver o seu sistema, ambiente gráfico e layout.
2. Execute `uspt diagnose` para verificar se há problemas de configuração.
3. Execute `uspt configure` para configurar caracteres portugueses.

## Problemas conhecidos durante instalação

- Se `setxkbmap` mostrar `WARNING: Running setxkbmap against an Xwayland server`, isso é normal em sessões Wayland. A ferramenta usará `gsettings` em vez disso.
- Se `gcommands` não estiver disponível, verifique se está num ambiente GNOME. Esta versão (v1) suporta apenas GNOME.