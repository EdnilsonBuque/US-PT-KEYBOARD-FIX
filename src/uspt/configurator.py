"""Módulo de configuração de layout e opções de teclado.

Responsável por aplicar alterações de configuração de teclado de forma segura.

Princípios:
- Nunca usar setxkbmap em sessões Wayland (é no-op, afeta só Xwayland).
- Usar gsettings org.gnome.desktop.input-sources como mecanismo primário em GNOME.
- Snapshot automático antes de qualquer escrita (ver módulo backup.py).
- Preservar layouts existentes do utilizador (acrescentar, nunca substituir).
- Validar que a sessão está consciente das alterações antes de aplicar.
"""

import subprocess
import logging
import json
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Caminho do schema GNOME
GNOME_INPUT_SOURCES_SCHEMA = "org.gnome.desktop.input-sources"

# Opções XKB padrão para português (Modalidade B - AltGr)
DEFAULT_XKB_OPTIONS_PORTUGUESE = "['compose:ralt']"
# Alternativa: dead keys
DEFAULT_XKB_OPTIONS_DEAD_KEYS = "['compose:caps']"

# Opções para layouts US International
US_INTL_OPTIONS = "['grp:alt_shift_toggle', 'grp_led:scroll']"


def _run_gsettings_get(schema: str, key: str) -> Optional[str]:
    """Obtém um valor de gsettings de forma segura.

    Usa lista de argumentos, sem shell=True.
    """
    try:
        result = subprocess.run(
            ["gsettings", "get", schema, key],
            capture_output=True, text=True,
            timeout=10,
        )
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            logger.warning("gsettings get falhou: %s", result.stderr)
            return None
    except FileNotFoundError:
        logger.warning("gsettings não encontrado")
        return None
    except subprocess.TimeoutExpired:
        logger.warning("gsettings timeout")
        return None


def _run_gsettings_set(schema: str, key: str, value: str) -> bool:
    """Define um valor de gsettings de forma segura.

    Usa lista de argumentos, sem shell=True.
    """
    try:
        result = subprocess.run(
            ["gsettings", "set", schema, key, value],
            capture_output=True, text=True,
            timeout=10,
        )
        if result.returncode == 0:
            logger.info("gsettings set concluído: %s = %s", key, value)
            return True
        else:
            logger.error("gsettings set falhou: %s", result.stderr)
            return False
    except FileNotFoundError:
        logger.warning("gsettings não encontrado")
        return False
    except subprocess.TimeoutExpired:
        logger.warning("gsettings timeout a definir %s", key)
        return False


def _parse_sources_value(value: str) -> List[Tuple[str, ...]]:
    """Analisa o valor string do gsettings sources.

    O formato é como: [('xkb', 'us')]
    Returns lista de tuplas.
    """
    try:
        # O gsettings retorna uma representação Python-like
        parsed = json.loads(value.replace("'", '"').replace("True", "true").replace("False", "false"))
        if isinstance(parsed, list):
            return [tuple(item) if isinstance(item, list) else (item,) for item in parsed]
    except json.JSONDecodeError:
        pass

    # Fallback: parsing manual mais simples
    # Formato: [('xkb', 'us')]
    result = []
    import re
    # Procurar por ('key', 'value') patterns
    matches = re.findall(r"\(\s*'([^']*)'\s*,\s*'([^']*)'\s*\)", value)
    for m in matches:
        result.append((m[0], m[1]))

    return result


def get_current_sources() -> List[Tuple[str, ...]]:
    """Obtém as fontes de entrada atuais do utilizador.

    Returns lista de tuplas (font, layout/variant).
    """
    value = _run_gsettings_get(GNOME_INPUT_SOURCES_SCHEMA, "sources")
    if value is None:
        return []

    sources = _parse_sources_value(value)
    logger.info("Fontes atuais: %s", sources)
    return sources


def get_current_xkb_options() -> List[str]:
    """Obtém as opções XKB atuais.

    Returns lista de strings de opções.
    """
    value = _run_gsettings_get(GNOME_INPUT_SOURCES_SCHEMA, "xkb-options")
    if value is None:
        return []

    # Value might be a comma-separated list or single string
    opts = [o.strip().strip("'").strip('"') for o in value.split(",") if o.strip()]
    logger.info("Opções XKB atuais: %s", opts)
    return opts


def preserve_existing_layouts(sources: List[Tuple[str, ...]]) -> List[Tuple[str, ...]]:
    """Garante que os layouts existentes do utilizador são preservados.

    Em vez de substituir sources, acrescenta o layout português se ainda não estiver lá.

    Returns nova lista de sources com layouts preservados/acrescentados.
    """
    # Start with existing
    new_sources = list(sources)

    # Check if Portuguese is already present
    pt_found = False
    for src in sources:
        src_str = str(src).lower()
        if "pt" in src_str or "portuguese" in src_str:
            pt_found = True
            logger.info("Layout português já presente: %s", src)
            break

    if not pt_found:
        # Add Portuguese (prefer Portuguese over US if currently on US)
        current_layout = "us"  # default
        for src in sources:
            src_str = str(src).lower()
            if "us" in src_str:
                current_layout = "us"
                break

        # Add Portuguese after existing
        if current_layout == "us":
            # Add pt after us
            new_sources.append(("xkb", "pt"))
        else:
            # Just add pt at the end
            new_sources.append(("xkb", "pt"))

        logger.info("Adicionado layout português às sources: %s", new_sources)

    return new_sources


def set_layout_portuguese(modalidade: str = "altgr") -> Dict[str, Any]:
    """Configura o layout para português com a modalidade especificada.

    modalidade: "altgr" (padrão) ou "dead_keys"
    - "altgr": Usa AltGr + , para ç, configura via xkb-options.
    - "dead_keys": Usa teclas mortas via compose:caps ou .Xcompose.

    Returns dicionário com status, detalhes e eventuais avisos.
    """
    result = {
        "success": False,
        "modalidade": modalidade,
        "applied": [],
        "warnings": [],
        "undo_info": None,
    }

    # Step 1: Get current state
    current_sources = get_current_sources()
    current_opts = get_current_xkb_options()

    # Step 2: Preserve existing layouts
    new_sources = preserve_existing_layouts(current_sources)

    # Step 3: Apply based on modalidade
    if modalidade == "altgr":
        # Modalidade B: AltGr + , → ç
        # Set xkb-options to include compose:ralt (Right Alt as compose)
        # This enables AltGr for special characters including ç

        # Build the options list - keep existing + add compose:ralt
        existing_opts = current_opts if current_opts else []
        new_opts = list(existing_opts)

        # Add compose:ralt if not already present
        if "compose:ralt" not in new_opts:
            new_opts.append("compose:ralt")
            result["applied"].append("compose:ralt added")

        # Also ensure Portuguese layout is in sources
        pt_added = False
        for src in new_sources:
            if str(src).lower().startswith("('xkb', 'pt'") or str(src).lower().startswith('("xkb", "pt"'):
                pt_added = True
                break

        if not pt_added:
            # Add Portuguese after current layout
            # Find current layout and add pt after
            new_sources = add_portuguese_after_current(new_sources)

        # Set the xkb-options
        opts_value = ", ".join(f"'{opt}'" for opt in new_opts)
        success = _run_gsettings_set(
            GNOME_INPUT_SOURCES_SCHEMA, "xkb-options", opts_value
        )
        if success:
            result["applied"].append("xkb-options set to: " + opts_value)
            result["success"] = True
        else:
            result["warnings"].append("Falha ao definir xkb-options")

        # Set sources with Portuguese
        sources_value = sources_value_from_tuples(new_sources)
        success2 = _run_gsettings_set(
            GNOME_INPUT_SOURCES_SCHEMA, "sources", sources_value
        )
        if success2:
            result["applied"].append("sources updated to include Portuguese")
        else:
            result["warnings"].append("Falha ao atualizar sources")

        # Undo info
        result["undo_info"] = {
            "type": "gsettings",
            "action": "set",
            "schema": GNOME_INPUT_SOURCES_SCHEMA,
            "keys": ["sources", "xkb-options"],
            "previous_values": {
                "sources": _run_gsettings_get(GNOME_INPUT_SOURCES_SCHEMA, "sources"),
                "xkb-options": _run_gsettings_get(GNOME_INPUT_SOURCES_SCHEMA, "xkb-options"),
            },
        }

    elif modalidade == "dead_keys":
        # Modalidade A: teclas mortas
        # Set compose:caps option
        # WARNING: This may not work well in all applications on Wayland

        new_opts = list(current_opts) if current_opts else []
        if "compose:caps" not in new_opts:
            new_opts.append("compose:caps")
            result["applied"].append("compose:caps added")

        opts_value = ", ".join(f"'{opt}'" for opt in new_opts)
        success = _run_gsettings_set(
            GNOME_INPUT_SOURCES_SCHEMA, "xkb-options", opts_value
        )
        if success:
            result["applied"].append("xkb-options set to: " + opts_value)

        # Add warning about limitations
        result["warnings"].append(
            "Modalidade A (teclas mortas): Verifique se o seu terminal/aplicações "
            "respectam ~/.Xcompose. Em GTK4+ e Chromium/Electron Wayland nativo, "
            "pode não funcionar. Considere a Modalidade B em vez disso."
        )

        result["success"] = success

        result["undo_info"] = {
            "type": "gsettings",
            "action": "set",
            "schema": GNOME_INPUT_SOURCES_SCHEMA,
            "keys": ["xkb-options"],
            "previous_values": {
                "xkb-options": _run_gsettings_get(GNOME_INPUT_SOURCES_SCHEMA, "xkb-options"),
            },
        }

    return result


def add_portuguese_after_current(new_sources: List[Tuple[str, ...]]) -> List[Tuple[str, ...]]:
    """Adiciona layout português após o layout atual nas sources."""
    # Find the first xkb layout and add pt after it
    for i, src in enumerate(new_sources):
        src_str = str(src).lower()
        if "xkb" in src_str:
            # Insert Portuguese after this one
            new_sources.insert(i + 1, ("xkb", "pt"))
            break
    else:
        # No xkb found, append at end
        new_sources.append(("xkb", "pt"))

    return new_sources


def sources_value_from_tuples(sources: List[Tuple[str, ...]]) -> str:
    """Converte uma lista de tuplas para o formato de string do gsettings.

    Exemplo: [('xkb', 'pt'), ('xkb', 'us')]
    Returns: "[('xkb', 'pt'), ('xkb', 'us')]"
    """
    items = []
    for src in sources:
        if len(src) == 2:
            items.append(f"('{src[0]}', '{src[1]}')")
        elif len(src) == 1:
            items.append(f"('{src[0]},')")
        else:
            items.append(str(src))
    return "[" + ", ".join(items) + "]"


def diagnose_and_configure(modalidade: str = "altgr") -> Dict[str, Any]:
    """Diagnostica o estado atual e aplica configuração se necessário.

    Esta é a função principal que combina diagnóstico + configuração em um único passo.

    Returns dicionário completo com diagnóstico e resultado.
    """
    result = {
        "diagnostic": {},
        "configuration": {},
        "success": False,
    }

    # Step 1: Diagnostic
    from .detector import full_detection
    detection = full_detection()

    session_type = detection["session_type"]["session"]
    de = detection["desktop_environment"]["de"]
    layout = detection["keyboard_layout"]["layout"]

    result["diagnostic"] = {
        "desktop_environment": de,
        "session_type": session_type,
        "current_keyboard_layout": layout,
        "available_tools": detection["available_tools"],
    }

    # Step 2: Check if configuration is needed/possible
    # GNOME only for v1
    if de != "gnome":
        result["diagnostic"]["note"] = (
            "Ambiente não-GNOME detetado. "
            "Esta versão (v1) suporta apenas GNOME. "
            "Configure manualmente o seu ambiente."
        )
        return result

    # Wayland check - warn about setxkbmap
    if session_type == "wayland":
        result["diagnostic"]["wayland_warning"] = (
            "Sessão Wayland detetada. "
            "setxkbmap afeta apenas o Xwayland e não persiste across reboots. "
            "Usando gsettings (mecanismo recomendado)."
        )

    # Step 3: Apply configuration
    config_result = set_layout_portuguese(modalidade=modalidade)
    result["configuration"] = config_result

    # Step 4: Combine success
    if config_result["success"]:
        result["success"] = True
    else:
        result["diagnostic"]["configuration_warnings"] = config_result["warnings"]

    return result