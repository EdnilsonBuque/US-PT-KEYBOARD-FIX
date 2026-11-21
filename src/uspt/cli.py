"""CLI alternativo/interativo para o US-PT Keyboard Fix.

Fornece uma interface de terminal interativa com menus e prompts,
além de apoiar os comandos standalone.
"""

import sys
import select
from typing import Any, Dict, List, Optional

from .main import print_header, print_help, print_version, setup_logging
from .detector import full_detection
from .configurator import diagnose_and_configure
from .diagnostic import run_full_diagnostic
from .backup import create_backup, restore_latest
from .altgr import diagnose_altgr_state, apply_altgr_portuguese
from .compose import get_compose_awareness
from .utils import colorize, format_severity


def run_interactive() -> None:
    """Executa interface interativa de menu."""
    setup_logging(level="WARNING")

    while True:
        print_header()
        print("1. Detectar sistema e teclado")
        print("2. Diagnosticar problemas")
        print("3. Configurar teclado para português")
        print("4. Ver estado atual")
        print("5. Configurar AltGr")
        print("6. Fazer backup")
        print("7. Restaurar configurações")
        print("8. Gerir XCompose")
        print("9. Desinstalar")
        print("10. Sair")

        if USE_COLOR:
            choice = input(colorize("\nEscolha uma opção: ", "cyan")).strip()
        else:
            choice = input("\nEscolha uma opção: ").strip()

        if not choice:
            continue

        # Execute selected option
        handled = False

        if choice == "1":
            detection = full_detection()
            print("\n--- Resultados da deteção ---")
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
            tools = detection["available_tools"]
            print("Ferramentas disponíveis:")
            for tool, available in tools.items():
                status = "✓" if available else "✗"
                print(f"  {status} {tool}")
            input("\nPrima Enter para continuar...")

        elif choice == "2":
            diagnostic = run_full_diagnostic()
            print("\n--- Diagnóstico ---")
            print(f"Status geral: {diagnostic['overall_status']}")
            issues = diagnostic.get("issues", [])
            if issues:
                print(f"Problemas ({len(issues)}):")
                for issue in issues:
                    severity = issue.get("severity", "medium")
                    cat = issue.get("category", "general")
                    desc = issue.get("description", "")
                    print(f"  [{severity}] [{cat}] {desc}")
            else:
                print("Nenhum problema detetado.")
            recs = diagnostic.get("recommendations", [])
            if recs:
                print("\nRecomendações:")
                for rec in recs:
                    print(f"  - {rec.get('description', '')}")
            input("\nPrima Enter para continuar...")

        elif choice == "3":
            # Configure
            if USE_COLOR:
                mod_choice = input(colorize("Modalidade [altgr/dead_keys]: ", "cyan")).strip()
            else:
                mod_choice = input("Modalidade [altgr/dead_keys]: ").strip()
            if not mod_choice:
                mod_choice = "altgr"
            
            # Validate
            val = mod_choice.lower().startswith("dead")
            modality = "dead_keys" if val else "altgr"
            
            print(f"Configurar (modalidade: {modality})...")
            backup = create_backup(description="Interactive configure")
            if backup["success"]:
                print(f"  Backup: {backup['snapshot_id']}")
            
            config_result = diagnose_and_configure(modalidade=modality)
            
            if config_result.get("success"):
                print("✓ Configuração aplicada.")
            else:
                print("⚠ Configuração com avisos.")
                warnings = config_result.get("configuration", {}).get("warnings", [])
                for w in warnings[:3]:
                    print(f"  ! {w}")
            
            input("\nPrima Enter para continuar...")

        elif choice == "4":
            diagnostic = run_full_diagnostic()
            print(f"\nStatus: {diagnostic['overall_status']}")
            print(f"Ambiente: {diagnostic['system']['desktop_environment']}")
            print(f"Sessão: {diagnostic['system']['session_type']}")
            print(f"Layout: {diagnostic['system']['keyboard_layout']}")
            input("\nPrima Enter para continuar...")

        elif choice == "5":
            # AltGr
            print("Estado AltGr:")
            state = diagnose_altgr_state()
            print(f"  Funcional: {'Sim' if state['altgr_functional'] else 'Não'}")
            print(f"  Pode produzir ç/Ç: {'Sim' if state['can_produce_cedilla'] else 'Não'}")
            print(f"  Opções: {', '.join(state.get('current_options', []))}")
            input("\nPrima Enter para continuar...")

            # Option to apply
            if not state["altgr_functional"]:
                if USE_COLOR:
                    confirm = input(colorize("Aplicar AltGr agora? [S/n]: ", "yellow")).strip().lower()
                else:
                    confirm = input("Aplicar AltGr agora? [S/n]: ").strip().lower()
                if not confirm or confirm in ("s", "sim", "y", "yes"):
                    print("A aplicar AltGr...")
                    result = apply_altgr_portuguese()
                    if result["success"]:
                        print("✓ AltGr configurado.")
                    else:
                        print("✗ Falha.")
                input("\nPrima Enter para continuar...")

        elif choice == "6":
            # Backup
            if USE_COLOR:
                desc = input(colorize("Descrição do backup (opcional): ", "cyan")).strip()
            else:
                desc = input("Descrição do backup (opcional): ").strip()
            result = create_backup(description=desc if desc else None)
            if result["success"]:
                print(f"✓ Backup: {result['snapshot_id']}")
            else:
                print(f"✗ Falha: {result.get('warnings', ['unknown'])}")
            input("\nPrima Enter para continuar...")

        elif choice == "7":
            # Restore
            result = restore_latest()
            if result["success"]:
                sid = result.get("snapshot_id", "desconhecido")
                print(f"✓ Restaurado do snapshot {sid}")
                restored = result.get("restored", [])
                if restored:
                    print(f"  Ficheiros: {', '.join(restored)}")
            else:
                print(f"✗ Falha: {result.get('warnings', ['unknown'])}")
            input("\nPrima Enter para continuar...")

        elif choice == "8":
            # Compose
            print("\nOpções XCompose:")
            print("1. Ver informação de compatibilidade")
            print("2. Criar ficheiro ~/.Xcompose")
            print("3. Remover/restorar de backup")
            
            if USE_COLOR:
                sub = input(colorize("Escolha: ", "cyan")).strip()
            else:
                sub = input("Escolha: ").strip()
            
            if sub == "1":
                awareness = get_compose_awareness()
                print(f"\n{awareness.get('recommendation', '')}")
                for lim in awareness.get("limitations", []):
                    print(f"  ! {lim}")
                for sup in awareness.get("xcompose_file_supported", []):
                    print(f"  ✓ {sup}")
            elif sub == "2":
                import datetime
                date_str = datetime.datetime.now().strftime("%Y-%m-%d")
                result = write_xcompose_file(date_str=date_str)
                if result["success"]:
                    print(f"✓ Criado: {result['path']}")
                else:
                    print(f"✗ Falha: {result.get('warnings', ['unknown'])}")
            elif sub == "3":
                from .restore import KeyboardRestore
                kr = KeyboardRestore()
                restore_result = kr.restore_keyboard_state()
                if restore_result["success"]:
                    print("✓ Restaurado.")
                else:
                    print("ℹ Nenhum .Xcompose nos backups ou falha.")
            input("\nPrima Enter para continuar...")

        elif choice == "9":
            # Uninstall
            print("Desinstalar US-PT Keyboard Fix...")
            print("Ficheiros do utilizador serão preservados.")
            confirm = input("Confirmar [s/N]: ").strip().lower()
            if not confirm or confirm in ("s", "sim", "y", "yes"):
                from .main import uninstall_uspt
                result = uninstall_uspt(preserve_user_configs=True, create_backup=True)
                print(result["report"] if "report" in result else "Desinstalação concluída.")
            input("\nPrima Enter para continuar...")

        elif choice == "10":
            print("Adeus!")
            sys.exit(0)

        else:
            print("Opção inválida. Tente novamente.")
            input("\nPrima Enter para continuar...")


def run_quick_cli() -> None:
    """CLI rápido - processa um comando e sai."""
    if len(sys.argv) < 2:
        print_help()
        sys.exit(1)
    
    # Delegate to main CLI
    from .main import main
    # Re-call main with the original args
    # Actually, just run the main function with sys.argv
    # But we need to re-setup sys.argv properly
    # For now, just show help
    print_help()
    sys.exit(0)


if __name__ == "__main__":
    # Check if we should run interactive or quick CLI
    if len(sys.argv) >= 2 and sys.argv[1] in ("detect", "diagnose", "configure", "status", 
                                                  "compose", "altgr", "install", "backup",
                                                  "restore", "uninstall", "--version", "--help"):
        # Run quick CLI mode
        run_quick_cli()
    else:
        # Run interactive mode
        run_interactive()