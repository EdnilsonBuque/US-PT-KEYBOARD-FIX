# US-PT Keyboard Fix

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/download/releases/3.8/)
[![Linux](https://img.shields.io/badge/OS-Linux-lightgrey.svg)](https://www.linux.org/)

## Ferramenta Open Source para diagnóstico e correção de layouts de teclado

### Problema

Utilizadores com teclados físicos americanos (US/QWERTY) encontram dificuldade ao escrever em português,
especialmente para produzir:
- `ç` e `Ç` (cedilha)
- `á`, `Á`, `é`, `É`, `í`, `Í`, `ó`, `Ó`, `ú`, `Ú` (acentos agudos)
- `ã`, `Ã`, `õ`, `Õ` (til)
- Outros caracteres portugueses

### Solução

O **US-PT Keyboard Fix** é uma ferramenta híbrida Python/Bash que identifica, diagnostica e corrige
problemas de configuração de teclados em sistemas Linux, focado no ambiente GNOME.

### Funcionalidades principais

| Módulo | Descrição |
|---|---|
| **Detecção** | Distribuição, ambiente gráfico, tipo de sessão (Wayland/X11), layout atual, ferramentas disponíveis. |
| **Configuração** | Modalidade A (teclas mortas via XCompose) e Modalidade B (AltGr). |
| **Diagnóstico** | Identifica problemas de layout, conflitos, dependências ausentes, permissões. |
| **Backup/Restauração** | Snapshot por alteração antes de modificar configurações. |
| **Desinstalador** | Remove apenas ficheiros do projeto, preserva configuração do utilizador. |

### Modais de caracteres

- **Modalidade B (AltGr — recomendada)**: `AltGr + ,` → `ç/Ç`. Funciona em todas as aplicações,
  incluindo Wayland. Não passa pelo Compose, evitando o problema `ć`/`ç` do `en_US.UTF-8`.

- **Modalidade A (Teclas mortas)**: `Compose + sequence → character`. Funciona em GTK3/QT6 via
  `~/.Xcompose`, mas NÃO em Chromium/Electron Wayland nem GTK4≥4.19.

### Sistemas suportados

- Ubuntu, Debian, Linux Mint (GNOME).
- Fedora (GNOME).

**v1 suporta apenas GNOME.** KDE Plasma e XFCE estão planeados para versão futura.

### Tecnologias utilizadas

- **Python 3**: Lógica principal, deteção, diagnóstico, gestão de configurações.
- **Bash**: Instalação, verificação de dependências.
- **GSettings/dconf**: Mecanismo primário de configuração em GNOME Wayland.
- **XKB**: Mapeamentos de teclado de baixo nível.
- **XCompose**: Mapeamento de teclas mortas (compatibilidade limitada).

### Instalação

```bash
sudo apt update
sudo apt install git python3 -y
git clone https://github.com/EdnilsonBuque/US-PT-KEYBOARD-FIX.git
cd us-pt-keyboard-fix
chmod +x scripts/install.sh
./scripts/install.sh
```

Após a instalação, execute:
```bash
uspt detect
uspt diagnose
uspt configure --modalidade altgr
```

### Comandos disponíveis

- `uspt detect` - Detetar sistema e teclado
- `uspt diagnose` - Diagnosticar problemas
- `uspt configure` - Configurar teclado português
- `uspt status` - Consultar estado
- `uspt backup` - Fazer backup
- `uspt restore` - Restaurar configuração
- `uspt compose` - Gerir XCompose
- `uspt altgr` - Configurar AltGr
- `uspt uninstall` - Desinstalar

### Licença

[MIT](LICENSE)

---

*Projeto Open Source. Sinta-se livre para fork, contribuir e melhorar.*