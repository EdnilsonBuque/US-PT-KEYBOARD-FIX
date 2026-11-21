#!/usr/bin/env bash
#
# US-PT Keyboard Fix - Desinstalador
#

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

PROJECT_NAME="US-PT Keyboard Fix"

# Confirm uninstallation
echo "Isso removerá os ficheiros do projeto $PROJECT_NAME."
echo "Ficheiros do utilizador (.Xcompose, backups) serão preservados."
echo "Configurações gsettings terão de ser revertidas manualmente."
echo ""
read -p "Confirmar desinstalação? [s/N] " response

if [[ ! "$response" =~ ^[SsIi][YySs]$ ]]; then
    log_info "Desinstalação cancelada."
    exit 0
fi

# Remover wrapper se existir
WRAPPER_PATH="/usr/local/bin/uspt"
if [ -f "$WRAPPER_PATH" ]; then
    log_info "Removendo wrapper de $WRAPPER_PATH"
    rm -f "$WRAPPER_PATH"
fi

USER_LOCAL="$HOME/.local/bin/uspt"
if [ -f "$USER_LOCAL" ]; then
    log_info "Removendo wrapper de $USER_LOCAL"
    rm -f "$USER_LOCAL"
fi

# Remover diretório de instalação (opcional - o utilador pode querer manter)
# Descomentar a linha abaixo se quiser remover completamente
# rm -rf "$HOME/us-pt-keyboard-fix"

log_info "Desinstalação concluída."
log_info "As alterações gsettings foram documentadas para reverter manualmente."
log_info "Backups estão em ~/.local/share/uspt-backup/"

exit 0