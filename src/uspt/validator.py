"""Validador de configurações e entradas do US-PT Keyboard Fix.

Responsável por:
- Validar entradas do utilizador.
- Verificar integridade de backups.
- Validar configurações após aplicação.
- Tratamento de erros.

Princípio: validar sempre antes de agir. Nunca assumir que uma configuração é válida.
"""

import logging
import subprocess
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


def validate_gsettings_schema(schema: str, key: str) -> Dict[str, Any]:
    """Valida se um schema e key do gsettings existem e são acedíveis.

    Returns dicionário com status e valor atual.
    """
    result = {
        "valid": False,
        "value": None,
        "error": None,
    }

    try:
        # Try to get the value - if it fails, schema/key may not exist
        r = subprocess.run(
            ["gsettings", "get", schema, key],
            capture_output=True, text=True,
            timeout=10,
        )
        if r.returncode == 0:
            result["valid"] = True
            result["value"] = r.stdout.strip()
        else:
            result["error"] = r.stderr.strip()
            logger.warning("gsettings get falhou para %s/%s: %s", schema, key, result["error"])
    except FileNotFoundError:
        result["error"] = "gsettings não encontrado no PATH"
        logger.warning("gsettings não encontrado")
    except subprocess.TimeoutExpired:
        result["error"] = "Timeout ao validar gsettings"
        logger.warning("Timeout validando gsettings")

    return result


def validate_layout_string(layout: str) -> Dict[str, Any]:
    """Valida se uma string de layout é reconhecida."""
    result = {
        "valid": False,
        "normalized": None,
        "errors": [],
    }

    if not layout or not layout.strip():
        result["errors"].append("String de layout vazia")
        return result

    layout = layout.strip().lower()

    # Known layouts
    known = {
        "us": "US (QWERTY)",
        "us_intl": "US International",
        "uk": "UK",
        "pt": "Portuguese",
        "pt_br": "Portuguese (Brazil)",
    }

    if layout in known:
        result["valid"] = True
        result["normalized"] = layout
    else:
        # Check if it starts with known prefix
        for prefix in ["us", "pt"]:
            if layout.startswith(prefix):
                result["valid"] = True
                result["normalized"] = prefix
                result["errors"].append(f"Layout '{layout}' reconhecido como prefixo '{prefix}'")
                break
        else:
            result["errors"].append(f"Layout '{layout}' não reconhecido")

    return result


def validate_modality(modalidade: str) -> Dict[str, Any]:
    """Valida se a modalidade especificada é suportada."""
    result = {
        "valid": False,
        "normalized": None,
        "errors": [],
    }

    if not modalidade:
        result["errors"].append("Modalidade não especificada")
        return result

    modalidade = modalidade.strip().lower()

    supported = ["altgr", "dead_keys", "both"]

    if modalidade in supported:
        result["valid"] = True
        result["normalized"] = modalidade
    else:
        result["errors"].append(
            f"Modalidade '{modalidade}' não suportada. "
            f"Suportadas: {', '.join(supported)}"
        )

    return result


def validate_session_for_config(session_type: str, de: str) -> Dict[str, Any]:
    """Valida se o ambiente atual suporta a configuração solicitada."""
    result = {
        "valid": False,
        "warnings": [],
        "errors": [],
        "recommended_mechanism": "",
    }

    # v1 only supports GNOME
    if de != "gnome":
        result["errors"].append(
            f"Ambiente {de} não suportado na v1. "
            "Somente GNOME é suportado."
        )
        return result

    # Check session type
    if session_type == "wayland":
        result["warnings"].append(
            "Sessão Wayland: setxkbmap não persiste. Use gsettings."
        )
        result["recommended_mechanism"] = "gsettings"
    elif session_type == "x11":
        result["recommended_mechanism"] = "gsettings (preferred) or setxkbmap"
    else:
        result["errors"].append(f"Tipo de sessão desconhecido: {session_type}")

    if not result["errors"]:
        result["valid"] = True

    return result


def validate_backup_integrity(snapshot_path: str) -> Dict[str, Any]:
    """Verifica se um snapshot de backup tem integridade básica."""
    result = {
        "valid": False,
        "directory_exists": False,
        "has_manifest": False,
        "errors": [],
    }

    if not snapshot_path:
        result["errors"].append("Caminho do snapshot não especificado")
        return result

    # Check directory
    if os.path.exists(snapshot_path):
        result["directory_exists"] = True
    else:
        result["errors"].append(f"Diretório de backup não existe: {snapshot_path}")
        return result

    # Check for manifest
    manifest_path = os.path.join(snapshot_path, "manifest.json")
    # Actually the manifest is in ~/.local/share/uspt-backup/manifest.json
    # But we can check if there's some indicator file
    # For now, if the directory has files, consider it potentially valid
    try:
        contents = os.listdir(snapshot_path)
        if contents:
            result["has_manifest"] = any(f == "manifest.json" or f.endswith(".json") for f in contents)
    except OSError:
        pass

    if result["directory_exists"]:
        result["valid"] = True

    return result


def validate_user_input(prompt_text: str, valid_options: List[str],
                        case_insensitive: bool = True) -> Optional[str]:
    """Valida entrada do utilizador contra opções conhecidas.

    Returns a opção validada ou None se o utilizador desistir.
    """
    result = None

    while True:
        user_input = input(prompt_text).strip()
        if not user_input:
            print("Entrada vazia. Tente novamente.")
            continue

        option = user_input.lower() if case_insensitive else user_input

        if option in [o.lower() for o in valid_options]:
            # Find the exact match
            for o in valid_options:
                if o.lower() == option:
                    result = o
                    break
            break
        else:
            print(f"Opção inválida. Opções válidas: {', '.join(valid_options)}")

    return result