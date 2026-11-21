"""Módulo de deteção e gestão de layouts de teclado.

Responsável por:
- Identificar layouts XKB (US, US International, UK, Portuguese, Portuguese Brazil).
- Distinguir teclado físico da configuração lógica.
- Nunca afirmar detetado físico quando a informação não estiver disponível.
"""

import subprocess
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Mapeamento de layouts XKB disponíveis
XKB_LAYOUTS = {
    "us": "US (QWERTY)",
    "us_intl": "US International",
    "uk": "UK",
    "pt": "Portuguese",
    "pt_br": "Portuguese (Brazil)",
}

# Caracteres produzíveis via Modalidade A (teclas mortas) e Modalidade B (AltGr)
CHARACTER_MODALITIES = {
    "cedilla": {
        "name": "cedilla (ç Ç)",
        "altgr": "AltGr + ,",
        "dead_key": "dead_cedilla + c",
        "warning": "dead_cedilla pode produzir ć em alguns locales; prefira AltGr + ,",
    },
    "acute": {
        "name": "acento agudo (á Á é É í Í ó Ó ú Ú)",
        "altgr": None,
        "dead_key": "dead_acute + base_letter",
        "warning": "Compose en_US.UTF-8 produz ć em vez de cedilha; agudos exigem cuidado",
    },
    "tilde": {
        "name": "tilde (ã Ã õ Õ)",
        "altgr": None,
        "dead_key": "dead_tilde + n",
        "warning": "Verificar suporte do terminal",
    },
}

# Portuguese characters set
PORTUGUESE_CHARS = [
    "ç", "Ç",
    "á", "Á", "é", "É", "í", "Í", "ó", "Ó", "ú", "Ú",
    "ã", "Ã", "õ", "Õ",
    "â", "Â", "ê", "Ê", "ô", "Ô",
    "à", "À",
]


def is_us_layout(layout: str) -> bool:
    """Verifica se o layout é US (ou variantes)."""
    return layout.lower() in ("us", "us_intl", "us colemak", "dvorak")


def is_portuguese_layout(layout: str) -> bool:
    """Verifica se o layout é português."""
    return layout.lower() in ("pt", "pt_br")


def detect_physical_layout_hint() -> Optional[Dict[str, str]]:
    """Tenta obter uma dica sobre o layout físico do teclado.

    Nota: Nem sempre possível detetar automaticalmente. Quando não houver informação
    confiável, retorna None e a chamada deve reportar "não disponível" em vez de
    afirmar que o físico foi identificado.

    Returns dicionário com dicas ou None.
    """
    hint = None

    # Check if xkbmodel gives any physical clues
    try:
        result = subprocess.run(
            ["setxkbmap", "-query"],
            capture_output=True, text=True,
            timeout=5,
        )
        if result.returncode == 0:
            model = None
            for line in result.stdout.splitlines():
                if "model:" in line.lower():
                    model = line.split(":", 1)[1].strip()
            if model:
                hint = {"model": model, "source": "setxkbmap"}
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # Try xkbcomp to list available symbols
    if not hint:
        try:
            result = subprocess.run(
                ["xkbcomp", "-l", "0", ":0"],
                capture_output=True, text=True,
                timeout=5,
            )
            # Parse output for physical clues
            logger.debug("xkbcomp output: %s", result.stdout)
        except FileNotFoundError:
            pass
        except subprocess.TimeoutExpired:
            pass

    if not hint:
        logger.debug("Não foi possível detetar layout físico; retornando None")
        return None

    return hint


def get_available_xkb_layouts() -> List[str]:
    """Retorna lista de layouts XKB disponíveis no sistema.

    Tenta ler de /usr/share/xkb/symbols/ ou usar setxkbmap -list types.
    """
    layouts = []

    try:
        result = subprocess.run(
            ["setxkbmap", "-list", "types"],
            capture_output=True, text=True,
            timeout=5,
        )
        if result.returncode == 0:
            # Parse the output for available layouts
            lines = result.stdout.splitlines()
            for line in lines:
                if "group" in line.lower() or "layout" in line.lower():
                    # Simple parsing - may need refinement
                    pass
    except FileNotFoundError:
        logger.warning("setxkbmap não disponível para listar layouts")

    # Fallback: try xkbcomp to list symbols
    if not layouts:
        try:
            result = subprocess.run(
                ["find", "/usr/share/xkb/symbols", "-name", "*.lst"],
                capture_output=True, text=True,
                timeout=5,
            )
            if result.returncode == 0:
                layouts = result.stdout.splitlines()
        except FileNotFoundError:
            pass

    # Always include the known ones
    known = list(XKB_LAYOUTS.keys())
    for k in known:
        if k not in layouts:
            layouts.append(k)

    logger.info("Layouts XKB disponíveis: %s", layouts)
    return layouts


def detect_layout_with_modalities() -> Dict[str, Any]:
    """Deteta o layout atual e informa quais modalidades de caracteres estão disponíveis.

    Returns dicionário com layout, modalities disponíveis e recomendações.
    """
    layout_info = detect_keyboard_layout()
    current_layout = layout_info.get("layout", "unknown")

    result = {
        "current_layout": current_layout,
        "layout_name": XKB_LAYOUTS.get(current_layout, current_layout),
        "available_modalities": [],
        "recommendation": "",
        "physical_layout_hint": detect_physical_layout_hint(),
    }

    # Based on current layout, recommend modalities
    if is_us_layout(current_layout):
        result["available_modalities"] = ["altgr", "dead_keys"]
        result["recommendation"] = (
            "Layout US detetado. Recomenda-se Modalidade B (AltGr + , para ç). "
            "Modalidade A (teclas mortas) depende do ficheiro ~/.XCompose."
        )
    elif is_portuguese_layout(current_layout):
        result["available_modalities"] = ["default"]
        result["recommendation"] = (
            "Layout português detetado. Caracteres acentuados devem estar disponíveis "
            "nativamente."
        )
    else:
        result["available_modalities"] = ["altgr", "dead_keys"]
        result["recommendation"] = (
            "Layout desconhecido. A ferramenta pode reconfigurá-lo para Portuguese "
            "ou aplicar modalidades US International."
        )

    return result