#!/usr/bin/env bash
#
# US-PT Keyboard Fix - Instalador
# Verifica dependências e instala a ferramenta.
#

set -euo pipefail

PROJECT_NAME="US-PT Keyboard Fix"
VERSION="0.1.0"

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Verificar se estamos como root (opcional, mas bom saber)
if [ "${EUID:-$(id -u)}" = "0" ]; then
    log_warn "A ferramenta não precisa de ser executada como root. Alguns comandos podem ser necessários."
fi

# Atualizar índice de pacotes
log_info "Atualizando índice de pacotes..."
if ! apt-get update 2>/dev/null; then
    log_error "Falha ao atualizar índice de pacotes."
    exit 1
fi

# Instalar dependências Python e ferramentas Linux
log_info "Instalando dependências..."
PACKAGES="python3-pip git"

if ! apt-get install -y $PACKAGES 2>/dev/null; then
    log_error "Falha ao instalar pacotes básicos."
    exit 1
fi

# Instalar dependências Python do projeto
log_info "Instalando dependências Python..."
if [ -f "requirements.txt" ]; then
    if ! pip3 install -r requirements.txt 2>/dev/null; then
        log_warn "Não foi possível instalar requirements.txt. Continuando mesmo assim."
    fi
fi

# Criar diretório de instalação
INSTALL_DIR="${HOME}/us-pt-keyboard-fix"
if [ ! -d "$INSTALL_DIR" ]; then
    log_info "Criando diretório de instalação em $INSTALL_DIR"
    mkdir -p "$INSTALL_DIR"
fi

# Copiar ficheiros do projeto
log_info "Instalando ficheiros do projeto..."
cp -r src/ "$INSTALL_DIR"/ 2>/dev/null || true
cp -r scripts/ "$INSTALL_DIR"/scripts/ 2>/dev/null || true
cp -r config/ "$INSTALL_DIR"/config/ 2>/dev/null || true
cp -r docs/ "$INSTALL_DIR"/docs/ 2>/dev/null || true
cp README.md "$INSTALL_DIR"/ 2>/dev/null || true
cp LICENSE "$INSTALL_DIR"/ 2>/dev/null || true
cp requirements.txt "$INSTALL_DIR"/ 2>/dev/null || true
cp pyproject.toml "$INSTALL_DIR"/ 2>/dev/null || true

# Tornar o script principal executável
chmod +x "$INSTALL_DIR"/src/uspt/main.py 2>/dev/null || true
chmod +x "$INSTALL_DIR"/scripts/*.sh 2>/dev/null || true

# Criar wrapper script no /usr/local/bin ou ~/.local/bin
WRAPPER_PATH="/usr/local/bin/uspt"
if [ -d "/usr/local/bin" ]; then
    log_info "Criando wrapper em $WRAPPER_PATH"
    cat > "$WRAPPER_PATH" << 'WRAPPER_EOF'
#!/usr/bin/env python3
from uspt.main import main
main()
WRAPPER_EOF
    chmod +x "$WRAPPER_PATH"
elif [ -d "$HOME/.local/bin" ]; then
    log_info "Criando wrapper em ~/.local/bin/uspt"
    mkdir -p "$HOME/.local/bin"
    cat > "$HOME/.local/bin/uspt" << 'WRAPPER_EOF'
#!/usr/bin/env python3
from uspt.main import main
main()
WRAPPER_EOF
    chmod +x "$HOME/.local/bin/uspt"
else
    log_warn "Não foi possível criar wrapper em /usr/local/bin ou ~/.local/bin."
    log_warn "Execute a ferramenta diretamente: python3 $INSTALL_DIR/src/uspt/main.py"
fi

# Final
log_info "Instalação do $PROJECT_NAME $VERSION concluída."
log_info "Execute 'uspt' para iniciar a ferramenta."
log_info "Ou execute 'uspt --help' para ver os comandos disponíveis."

exit 0