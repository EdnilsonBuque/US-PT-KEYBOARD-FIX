"""Ponto de entrada principal do US-PT Keyboard Fix.

Orquestra os módulos do projeto e fornece a interface de linha de comando
através do entry point `uspt`.

Responsável por:
- Coordenar deteção → diagnóstico → configuração → backup → restauração.
- Garantir fluxo adequado entre módulos.
- Tratamento global de erros.
"""

import logging
import sys
from typing import Any, Dict, List, Optional

from .detector import full_detection
from .configurator import diagnose_and_configure
from .diagnostic import run_full_diagnostic
from .backup import create_backup, restore_latest, verify_recent
from .altgr import diagnose_altgr_state, apply_altgr_portuguese, remove_altgr_config
from .compose import write_xcompose_file, get_compose_awareness, detect_compose_key
from .validator import (
    validate_modality, validate_session_for_config,
    validate_layout_string, validate_gsettings_schema,
)
from .utils import colorize, format_severity, run_subprocess_safe

logger = logging.getLogger(__name__)


def setup_logging(level: str = "INFO") -> None:
    """Configura o sistema de logging do projeto."""
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def print_header() -> None:
    """Imprime o cabeçalho da aplicação."""
    if USE_COLOR:
        header = colorize("========================================\n", "cyan")
        header += colorize("US-PT KEYBOARD FIX\n", "bold", "magenta")
        header += colorize("========================================", "cyan")
        print(header)
    else:
        print("========================================")
        print("US-PT Keyboard Fix")
        print("========================================")


def print_version() -> None:
    """Imprime a versão da aplicação."""
    from . import __version__
    print(f"Versão {__version__}")


def print_help() -> None:
    """Imprime a ajuda disponível."""
    print("""
Comandos disponíveis:

  uspt detect       - Detetar sistema, ambiente e layout do teclado
  uspt diagnose     - Diagnosticar problemas de configuração
  uspt configure    - Configurar teclado para português
  uspt install      - Instalar/verificar dependências
  uspt backup       - Fazer backup das configurações atuais
  uspt restore      - Restaurar última configuração
  uspt status       - Consultar estado atual
  uspt uninstall    - Desinstalar a ferramenta
  uspt compose      - Gerir ficheiro XCompose
  uspt altgr        - Configurar/com remover AltGr
  uspt --version    - Versão da aplicação
  uspt --help       - Esta ajuda

Utilize 'uspt {comando} --help' para mais detalhes sobre cada comando.
""")


def cmd_detect(args: List[str]) -> int:
    """Executar comando uspt detect."""
    # Simple detect and print
    detection = full_detection()

    if USE_COLOR:
        print(colorize("Detetou o seguinte:\n", "bold"))

    # Distribution
    dist = detection["distribution"]
    print(f"  Distribuição: {dist.get('name', 'Desconhecido')} ({dist.get('id', 'unknown')}) {dist.get('version', 'unknown')}")

    # Desktop environment
    de = detection["desktop_environment"]
    print(f"  Ambiente gráfico: {de.get('de', 'desconhecido').upper()}")

    # Session type
    session = detection["session_type"]
    session_label = session.get('session', 'unknown')
    display = session.get('display_server', 'unknown')
    if display != 'unknown':
        session_label += f" ({display})"
    print(f"  Tipo de sessão: {session_label}")

    # Keyboard layout
    layout = detection["keyboard_layout"]
    print(f"  Layout de teclado: {layout.get('layout', 'desconhecido')}")
    if layout.get('variant'):
        print(f"    Variante: {layout.get('variant')}")

    # Available tools
    tools = detection["available_tools"]
    print("  Ferramentas disponíveis:")
    for tool, available in tools.items():
        status = "✓" if available else "✗"
        print(f"    {status} {tool}")

    return 0


def cmd_diagnose(args: List[str]) -> int:
    """Executar comando uspt diagnose."""
    diagnostic = run_full_diagnostic()

    if USE_COLOR:
        print(colorize("=== Diagnóstico do Sistema ===\n", "bold"))

    status_color = {
        "ok": "green",
        "warning": "yellow", 
        "critical": "red",
        "unsupported_environment": "red",
    }.get(diagnostic["overall_status"], "white")

    print(f"  Status geral: {colorize(diagnostic['overall_status'].upper(), status_color)}")
    print(f"  Ambiente: {diagnostic['system']['desktop_environment']}")
    print(f"  Sessão: {diagnostic['system']['session_type']}")
    print(f"  Layout: {diagnostic['system']['keyboard_layout']}")

    # Issues
    issues = diagnostic.get("issues", [])
    if issues:
        print(f"\n  Problemas ({len(issues)}):")
        for issue in issues:
            severity = issue.get("severity", "medium")
            fmt_severity = format_severity(severity)
            cat = issue.get("category", "general")
            desc = issue.get("description", "")
            print(f"    {fmt_severity} [{cat}] {desc}")
    else:
        print("\n  Nenhum problema detetado.")

    # Recommendations
    recs = diagnostic.get("recommendations", [])
    if recs:
        print("\n  Recomendações:")
        for rec in recs:
            cat = rec.get("category", "general")
            desc = rec.get("description", "")
            action = rec.get("action", "")
            if action:
                print(f"    [{cat}] {desc} → {action}")
            else:
                print(f"    [{cat}] {desc}")

    return 0


def cmd_configure(args: List[str]) -> int:
    """Executar comando uspt configure."""
    # Parse modality option
    modality = "altgr"  # default

    # Simple arg parsing
    i = 0
    while i < len(args):
        if args[i] in ("--modalidade", "-m") and i + 1 < len(args):
            modality = args[i + 1]
            i += 2
        else:
            i += 1

    # Validate modality
    val = validate_modality(modality)
    if not val["valid"]:
        print(f"Erro: modalidade inválida '{modality}'.")
        print(f"Opções: {', '.join(val.get('errors', ['altgr', 'dead_keys']))}")
        return 1

    # First, do full detection
    detection = full_detection()
    de = detection["desktop_environment"]["de"]
    session = detection["session_type"]["session"]

    # Validate session
    sess_val = validate_session_for_config(session, de)
    if not sess_val["valid"]:
        print(f"Erro: este ambiente não é suportado na v1.")
        for err in sess_val.get("errors", []):
            print(f"  - {err}")
        return 1

    # Print warnings
    for warn in sess_val.get("warnings", []):
        print(f"Aviso: {warn}")

    # Create backup before configuring
    print("A fazer backup antes da configuração...")
    backup = create_backup(description="Before Portuguese config")
    if backup["success"]:
        print(f"  ✓ Backup criado: {backup['snapshot_id']}")
    else:
        print(f"  ! Aviso: backup falhou: {backup.get('warnings', ['unknown error'])}")

    # Apply configuration
    print(f"Configurar caracteres portugueses (modalidade: {val['normalized']})...")
    config_result = diagnose_and_configure(modalidade=val["normalized"])

    # Report results
    if config_result["success"]:
        print("  ✓ Configuração aplicada com sucesso.")
    else:
        warnings = config_result.get("diagnostic", {}).get("configuration_warnings", [])
        print("  ⚠ Configuração com avisos:")
        for w in warnings:
            print(f"    - {w}")

    # Configuration details
    config = config_result.get("configuration", {})
    applied = config.get("applied", [])
    if applied:
        print("  Aplicado:")
        for a in applied:
            print(f"    ✓ {a}")

    warnings = config.get("warnings", [])
    if warnings:
        print("  Avisos:")
        for w in warnings:
            print(f"    ! {w}")

    # Undo info
    undo_info = config.get("undo_info")
    if undo_info:
        print("  (Para restaurar: execute uspt restore)")

    return 0


def cmd_status(args: List[str]) -> int:
    """Executar comando uspt status."""
    detection = full_detection()

    if USE_COLOR:
        print(colorize("=== Estado Atual ===\n", "bold"))

    dist = detection["distribution"]
    print(f"Distribuição: {dist.get('name', 'Desconhecido')} ({dist.get('id', 'unknown')}) {dist.get('version', 'unknown')}")

    de = detection["desktop_environment"]
    print(f"Ambiente gráfico: {de.get('de', 'desconhecido').upper()}")

    session = detection["session_type"]
    session_label = session.get('session', 'unknown')
    display = session.get('display_server', 'unknown')
    if display != 'unknown':
        session_label += f" ({display})"
    print(f"Tipo de sessão: {session_label}")

    layout = detection["keyboard_layout"]
    print(f"Layout de teclado: {layout.get('layout', 'desconhecido')}")
    if layout.get('variant'):
        print(f"  Variante: {layout.get('variant')}")

    # gsettings state
    print("\nConfiguração gsettings:")
    sources = detection.get("sources", None)
    # We'll just note the known state
    print("  (use 'uspt diagnose' para análise detalhada)")

    # Available tools
    tools = detection["available_tools"]
    print("\nFerramentas:")
    for tool, available in tools.items():
        status = "✓" if available else "✗"
        print(f"  {status} {tool}")

    return 0


def cmd_compose(args: List[str]) -> int:
    """Executar comando uspt compose."""
    # Parse action
    action = "status"  # default
    i = 0
    while i < len(args):
        if args[i] in ("--create", "-c") and i + 1 < len(args):
            # Would need a date, use current
            i += 1
        elif args[i] in ("--remove", "-r"):
            action = "remove"
        elif args[i] in ("--info", "-i"):
            action = "info"
        else:
            i += 1

    if action == "info":
        awareness = get_compose_awareness()
        if USE_COLOR:
            print(colorize("=== Informação XCompose ===\n", "bold"))
        print("Compatibilidade do ficheiro ~/.Xcompose:")
        for lim in awareness.get("limitations", []):
            print(f"  ! {lim}")
        for sup in awareness.get("xcompose_file_supported", []):
            print(f"  ✓ {sup}")
        print(f"\n  {awareness.get('recommendation', '')}")

    elif action == "create":
        import datetime
        date_str = datetime.datetime.now().strftime("%Y-%m-%d")
        result = write_xcompose_file(date_str=date_str)
        if result["success"]:
            print(f"✓ Ficheiro XCompose criado em: {result['path']}")
            if result.get("backup_created"):
                print(f"  Backup do existente: {result['backup_created']}")
        else:
            print(f"✗ Falha ao criar XCompose: {result.get('warnings', ['unknown'])}")

    elif action == "remove":
        # Ask for confirmation or just remove last
        from .backup import BackupManager
        import os
        backup_mgr = BackupManager()
        # List snapshots first
        snapshots = backup_mgr.list_available_snapshots()
        if snapshots["total_snapshots"] > 0:
            print(f"Encontrados {snapshots['total_snapshots']} snapshots.")
            # Restore the XCompose from latest
            restore_result = restore_latest()
            if restore_result["success"] and ".Xcompose" in restore_result.get("restored", []):
                print("✓ .Xcompose restaurado do último backup.")
            else:
                print("ℹ Nenhum .Xcompose encontrado nos backups.")
        else:
            print("Não há backups disponíveis.")

    # Default: show status
    else:
        result = write_xcompose_file()  # Just check existence
        if os.path.exists(result["path"] if "path" in result else "~/.Xcompose"):
            print("✓ Ficheiro ~/.Xcompose existe.")
        else:
            print("ℹ Ficheiro ~/.Xcompose não existe.")
            # Offer to create
            print("Use 'uspt compose --create' para o criar.")

    return 0


def cmd_altgr(args: List[str]) -> int:
    """Executar comando uspt altgr."""
    action = "status"  # default
    i = 0
    while i < len(args):
        if args[i] in ("--enable", "-e"):
            action = "enable"
        elif args[i] in ("--disable", "-d"):
            action = "disable"
        else:
            i += 1

    if action == "enable":
        print("A aplicar configuração AltGr para caracteres portugueses...")
        result = apply_altgr_portuguese()
        if result["success"]:
            print("✓ AltGr configurado com sucesso.")
            # Show what was applied
            applied = result.get("applied", [])
            for a in applied:
                print(f"  - {a}")
            warnings = result.get("warnings", [])
            for w in warnings[:2]:  # Show first 2
                print(f"  ! {w}")
        else:
            print(f"✗ Falha ao configurar AltGr: {result.get('warnings', ['unknown'])}")

    elif action == "disable":
        print("A remover configuração AltGr...")
        result = remove_altgr_config()
        if result["undone"] or result["success"]:
            print("✓ Configuração AltGr removida.")
            if result.get("warnings"):
                for w in result["warnings"][:2]:
                    print(f"  ! {w}")
        else:
            print(f"✗ Falha ao remover AltGr: {result.get('warnings', ['unknown'])}")

    else:  # status
        state = diagnose_altgr_state()
        if USE_COLOR:
            print(colorize("=== Estado AltGr ===\n", "bold"))
        print(f"AltGr funcional: {'✓' if state['altgr_functional'] else '✗'}")
        print(f"Pode produzir cedilha (ç/Ç): {'✓' if state['can_produce_cedilla'] else '✗'}")
        print(f"Opções atuais: {', '.join(state.get('current_options', []))}")
        diag = state.get("diagnostic", "")
        if diag:
            print(f"Diagnóstico: {diag}")

    return 0


def cmd_install(args: List[str]) -> int:
    """Executar comando uspt install."""
    if USE_COLOR:
        print(colorize("=== Instalação ===\n", "bold"))

    print("Verificar dependências...")
    # Check critical dependencies
    from .detector import detect_available_tools
    tools = detect_available_tools()

    critical = ["gsettings"]
    optional = ["localectl", "setxkbmap", "xfconf-query", "kwriteconfig"]

    all_ok = True

    # Critical
    for tool in critical:
        available = tools.get(tool, False)
        if available:
            print(f"  ✓ {tool}")
        else:
            print(f"  ✗ {tool} (crítico)")
            all_ok = False

    # Optional
    print("\nFerramentas opcionais:")
    for tool in optional:
        available = tools.get(tool, False)
        if available:
            print(f"  ✓ {tool}")
        else:
            print(f"  - {tool} (opcional)")

    if not all_ok:
        print("\nAlgumas dependências críticas estão ausentes.")
        print("Tente: sudo apt update && sudo apt install gsettings-backend")
        return 1

    print("\nDependências verificadas com sucesso.")
    return 0


def cmd_backup(args: List[str]) -> int:
    """Executar comando uspt backup."""
    if USE_COLOR:
        print(colorize("=== Fazer Backup ===\n", "bold"))

    # Parse optional description
    description = ""
    i = 0
    while i < len(args):
        if args[i] in ("--description", "-d") and i + 1 < len(args):
            description = args[i + 1]
            i += 2
        else:
            i += 1

    result = create_backup(description=description)

    if result["success"]:
        print(f"✓ Backup criado: {result['snapshot_id']}")
        print(f"  Ficheiros copiados: {result.get('files_backed_up', 0)}")
        if result.get("warnings"):
            print("  Avisos:")
            for w in result["warnings"]:
                print(f"    ! {w}")
    else:
        print(f"✗ Falha ao criar backup: {result.get('warnings', ['unknown error'])}")

    return 0


def cmd_restore(args: List[str]) -> int:
    """Executar comando uspt restore."""
    if USE_COLOR:
        print(colorize("=== Restaurar ===\n", "bold"))

    # Parse optional snapshot_id
    snapshot_id = None
    i = 0
    while i < len(args):
        if args[i] in ("--snapshot", "-s") and i + 1 < len(args):
            snapshot_id = args[i + 1]
            i += 2
        else:
            i += 1

    # If no snapshot_id, get latest
    if not snapshot_id:
        from .backup import restore_latest
        result = restore_latest()
        snapshot_id = result.get("snapshot_id")

    if snapshot_id:
        from .restore import KeyboardRestore
        kr = KeyboardRestore()
        result = kr.restore_keyboard_state(snapshot_id=snapshot_id)
    else:
        # Just get latest automatically
        result = restore_latest()

    if result["success"]:
        restored = result.get("restored", [])
        print(f"✓ Restauração concluída do snapshot {result.get('snapshot_id', 'desconhecido')}")
        if restored:
            print(f"  Ficheiros restaurados: {', '.join(restored)}")
        if result.get("warnings"):
            print("  Avisos:")
            for w in result["warnings"]:
                print(f"    ! {w}")
    else:
        print(f"✗ Falha na restauração: {result.get('warnings', ['unknown error'])}")

    return 0


def cmd_uninstall(args: List[str]) -> int:
    """Executar comando uspt uninstall."""
    if USE_COLOR:
        print(colorize("=== Desinstalar ===\n", "bold"))

    # Confirmation (simple - in real app would be more robust)
    print("Isso removerá os ficheiros do projeto US-PT Keyboard Fix.")
    print("Ficheiros do utilizador (.Xcompose, backups) serão preservados.")
    print("Configurações gsettings terão de ser revertidas manualmente.")
    print()

    # Quick yes/no
    response = input("Confirmar desinstalação? [s/N]: ").strip().lower()
    if response not in ("s", "sim", "y", "yes"):
        print("Desinstalação cancelada.")
        return 0

    result = uninstall_uspt(preserve_user_configs=True, create_backup=True)

    if result["success"]:
        print(result["report"])
    else:
        print("✗ Falha na desinstalação:")
        for w in result.get("warnings", []):
            print(f"  ! {w}")

    return 0


def main() -> None:
    """Função principal - entry point do CLI."""
    # Parse arguments
    if len(sys.argv) < 2:
        print_help()
        sys.exit(0)

    command = sys.argv[1]
    args = sys.argv[2:]

    # Setup basic logging
    setup_logging(level="WARNING")  # Reduce noise, CLI handles output

    # Route to command handler
    commands = {
        "detect": cmd_detect,
        "diagnose": cmd_diagnose,
        "configure": cmd_configure,
        "status": cmd_status,
        "compose": cmd_compose,
        "altgr": cmd_altgr,
        "install": cmd_install,
        "backup": cmd_backup,
        "restore": cmd_restore,
        "uninstall": cmd_uninstall,
        "--version": lambda _: (print_version(), sys.exit(0)),
        "--help": lambda _: (print_help(), sys.exit(0)),
    }

    if command in commands:
        try:
            exit_code = commands[command](args)
            sys.exit(exit_code)
        except KeyboardInterrupt:
            print("\nOperação cancelada pelo utilizador.")
            sys.exit(1)
        except Exception as e:
            print(f"Erro inesperado: {e}")
            logger.exception("Unexpected error in main")
            sys.exit(1)
    else:
        print(f"Comando desconhecido: {command}")
        print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()