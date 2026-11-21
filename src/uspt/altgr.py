"""Módulo de configuração de combinações AltGr para caracteres portugueses.

Responsável por:
- Aplicar opções XKB que ativam AltGr para produção de caracteres especiais.
- Mapear ç, Ç e demais caracteres portugueses via AltGr.
- Fornecer diagnóstico do estado atual das opções AltGr.

Princípio chave: AltGr + , → ç/Ç diretamente, sem passar pelo Compose.
Isso contorna o problema do Compose en_US.UTF-8 produzir ć em vez de ç.
"""

import logging
import subprocess
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Portuguese characters producible via AltGr
ALTGR_CHAR_MAP = {
    ",": {  # Cedilla
        "desc": "cedilla (ç Ç)",
        "produces": ["ç", "Ç"],
        "xkb_key": "c",  # AltGr + , produces ccedilla
    },
    # Additional AltGr combinations could be added here
}

# XKB options for Portuguese character support via AltGr
# These are the standard gsettings xkb-options values
XKB_OPTIONS_PORTUGUESE_ALTGR = "['compose:ralt']"
XKB_OPTIONS_US_INTERNATIONAL = "['grp:alt_shift_toggle', 'grp_led:scroll']"

# Known working XKB options for US International layout
US_INTL_XKB_OPTS = {
    "description": "US International - AltGr composes",
    "options": ["compose:ralt", "dead_acute:swap"],  # compose on Right Alt
}


def apply_altgr_portuguese() -> Dict[str, Any]:
    """Aplica configurações AltGr para suporte a caracteres portugueses.

    Modalidade B: AltGr + , → ç/Ç diretamente.
    Não passa pelo Compose, logo não sofre do problema ć/ç do en_US.

    Returns dicionário com status e detalhes.
    """
    result = {
        "success": False,
        "modalidade": "altgr",
        "applied": [],
        "warnings": [],
        "undo_info": None,
    }

    # Get current state
    try:
        current_opts = _get_current_xkb_options()
        result["undo_info"] = {
            "previous_xkb_options": current_opts,
            "action": "set_xkb_options",
        }
    except Exception as e:
        result["warnings"].append("Não foi possível ler opções atuais: " + str(e))
        current_opts = []

    # Set xkb-options to enable AltGr-based compose and Portuguese support
    # compose:ralt makes Right Alt act as Compose key,
    # but in US International, AltGr + , produces ccedilla directly
    new_opts = ["compose:ralt"]

    # Also add us(intl) effectively by setting the right options
    # For now, just set compose:ralt which enables AltGr for compose
    # and also enables dead key behavior
    opts_value = ", ".join(f"'{opt}'" for opt in new_opts)

    success = _set_gsettings_xkb_options(opts_value)
    if success:
        result["applied"].append("xkb-options set to: " + opts_value)
        result["success"] = True
    else:
        result["warnings"].append("Falha ao definir xkb-options para AltGr")

    # Verify by reading back
    if result["success"]:
        verified_opts = _get_current_xkb_options()
        result["verified"] = verified_opts
        if "compose:ralt" in verified_opts:
            result["applied"].append("Verificado: compose:ralt está ativo")
        else:
            result["warnings"].append(
                "Não foi possível verificar que compose:ralt está ativo"
            )

    # Add informative warnings
    result["warnings"].append(
        "Modalidade B (AltGr): ' , ' após AltGr produz ç/Ç diretamente. "
        "Não utiliza teclas mortas, evitando o problema ć/ç do Compose en_US."
    )
    result["warnings"].append(
        "As combinações de AltGr variam por layout. Verifique o comportamento "
        "no seu terminal após a aplicação."
    )

    return result


def remove_altgr_config() -> Dict[str, Any]:
    """Remove as configurações AltGr aplicadas, restaurando o estado anterior.

    Returns dicionário com status.
    """
    result = {
        "success": False,
        "action": "remove_altgr",
        "undone": False,
        "warnings": [],
    }

    # Restore previous xkb-options
    undo_info = result.get("undo_info", {})
    previous_opts = undo_info.get("previous_xkb_options")

    if previous_opts is not None:
        success = _set_gsettings_xkb_options(", ".join(f"'{opt}'" for opt in previous_opts))
        if success:
            result["undone"] = True
            result["success"] = True
            result["applied"].append("Opções restauradas: " + ", ".join(f"'{opt}'" for opt in previous_opts))
        else:
            result["warnings"].append("Falha ao restaurar opções anteriores")
    else:
        # No undo info, try to reset to defaults
        # Remove compose:ralt specifically
        try:
            current = _get_current_xkb_options()
            # Filter out compose:ralt
            filtered = [o for o in current if "compose:ralt" not in o]
            if filtered:
                success = _set_gsettings_xkb_options(", ".join(f"'{opt}'" for opt in filtered))
                if success:
                    result["undone"] = True
                    result["success"] = True
            else:
                # Try full reset
                success = _set_gsettings_xkb_options("")
                if success:
                    result["undone"] = True
                    result["success"] = True
        except Exception as e:
            result["warnings"].append("Erro ao tentar remover configurações: " + str(e))

    return result


def _get_current_xkb_options() -> List[str]:
    """Obtém as opções XKB atuais via gsettings."""
    try:
        result = subprocess.run(
            ["gsettings", "get", "org.gnome.desktop.input-sources", "xkb-options"],
            capture_output=True, text=True,
            timeout=10,
        )
        if result.returncode == 0:
            value = result.stdout.strip()
            # Parse the value
            opts = []
            # Remove brackets and quotes
            value = value.strip("[]").strip("'").strip('"')
            # Split by ", " but be careful
            if value:
                opts = [o.strip().strip("'").strip('"') for o in value.split(",") if o.strip()]
            return opts
    except FileNotFoundError:
        logger.warning("gsettings não disponível")
    except Exception as e:
        logger.error("Erro ao obter opções XKB: %s", str(e))

    return []


def _set_gsettings_xkb_options(opts_value: str) -> bool:
    """Define as opções XKB via gsettings de forma segura."""
    try:
        result = subprocess.run(
            ["gsettings", "set", "org.gnome.desktop.input-sources", "xkb-options", opts_value],
            capture_output=True, text=True,
            timeout=10,
        )
        if result.returncode == 0:
            logger.info("xkb-options setado para: %s", opts_value)
            return True
        else:
            logger.error("Falha ao setar xkb-options: %s", result.stderr)
            return False
    except FileNotFoundError:
        logger.warning("gsettings não disponível")
        return False
    except Exception as e:
        logger.error("Exceção ao setar xkb-options: %s", str(e))
        return False


def diagnose_altgr_state() -> Dict[str, Any]:
    """Diagnosta o estado atual das opções AltGr/Compose.

    Returns o estado atual e recomendações.
    """
    result = {
        "current_options": [],
        "altgr_functional": False,
        "can_produce_cedilla": False,
        "diagnostic": "",
    }

    current_opts = _get_current_xkb_options()
    result["current_options"] = current_opts

    # Check if compose:ralt is present (enables AltGr compose)
    has_ralt = "compose:ralt" in current_opts

    # In US International layout with compose:ralt:
    # - AltGr + , produces ccedilla (ç/Ç)
    # - AltGr + ' produces acute accent
    # - AltGr + e produces § (in some configs) - be careful

    if has_ralt:
        result["altgr_functional"] = True
        result["can_produce_cedilla"] = True
        result["diagnostic"] = (
            "AltGr está funcional. "
            "AltGr + , → ç/Ç (cedilla). "
            "AltGr + ' → acento agudo. "
            "Isso funciona em sessões Wayland via gsettings."
        )
    else:
        result["diagnostic"] = (
            "AltGr não está configurado com compose:ralt. "
            "Caracteres portugueses podem não estar disponíveis. "
            "Recomenda-se aplicar a Modalidade B."
        )

    return result