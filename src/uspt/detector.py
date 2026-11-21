"""Módulo de deteção de sistema, ambiente gráfico e layout de teclado.

Responsável por responder às perguntas fundamentais:
- Que distribuição estamos?
- Que ambiente gráfico (GNOME, KDE, etc.)?
- Wayland ou X11?
- Layout atual?
- Quais as ferramentas disponíveis?
"""

import subprocess
import json
import logging
from typing import Any, Dict, Optional, List

logger = logging.getLogger(__name__)


def detect_distribution() -> Dict[str, str]:
    """Deteta a distribuição Linux e versão.

    Returns um dicionário com 'id', 'name' e 'version'.
    """
    distro = {"id": "unknown", "name": "Unknown", "version": "unknown"}

    try:
        with open("/etc/os-release") as f:
            content = f.read()
        # Parse simple os-release fields
        for line in content.splitlines():
            line = line.strip()
            if line.startswith("ID="):
                distro["id"] = line.split("=", 1)[1].strip('"').strip("'")
            elif line.startswith("NAME="):
                distro["name"] = line.split("=", 1)[1].strip('"').strip("'")
            elif line.startswith("VERSION_ID="):
                distro["version"] = line.split("=", 1)[1].strip('"').strip("'")
            elif line.startswith("VERSION="):
                # Extract version string before any parenthesis
                import re
                match = re.search(r'VERSION="?([^"\n]+)"?', line)
                if match:
                    distro["version"] = match.group(1).strip()
    except FileNotFoundError:
        logger.warning("/etc/os-release não encontrado")

    # Also try lsb_release for some distros
    if distro["id"] == "unknown":
        try:
            result = subprocess.run(
                ["lsb_release", "-a"],
                capture_output=True, text=True,
            )
            if result.returncode == 0:
                for line in result.stdout.splitlines():
                    if "Description:" in line:
                        desc = line.split("Description:", 1)[1].strip()
                        # Try to parse
                        pass
        except FileNotFoundError:
            pass

    logger.info("Distribuição detetada: %s %s", distro["id"], distro["version"])
    return distro


def detect_desktop_environment() -> Dict[str, str]:
    """Deteta o ambiente gráfico ativo.

    Returns um dicionário com 'de' (desktop environment) e 'wm' (window manager).
    """
    env = {"de": "unknown", "wm": "unknown"}

    # Check XDG_CURRENT_DESKTOP first
    xdg = __import__("os").environ.get("XDG_CURRENT_DESKTOP", "")
    if xdg:
        if "GNOME" in xdg.upper():
            env["de"] = "gnome"
        elif "KDE" in xdg.upper() or "PLASMA" in xdg.upper():
            env["de"] = "kde"
        elif "XFCE" in xdg.upper():
            env["de"] = "xfce"
        else:
            env["de"] = xdg

    # Fallback: check individual variables
    if env["de"] == "unknown":
        for var in ["DESKTOP_SESSION", "GNOME_SESSION"]:
            val = __import__("os").environ.get(var, "")
            if val:
                if "gnome" in val.lower():
                    env["de"] = "gnome"
                    break
                elif "kde" in val.lower() or "plasma" in val.lower():
                    env["de"] = "kde"
                    break
                elif "xfce" in val.lower():
                    env["de"] = "xfce"
                    break

    # Try to detect window manager
    wm = __import__("os").environ.get("WINDOW_MANAGER", "")
    if wm:
        env["wm"] = wm

    logger.info("Ambiente gráfico detetado: %s", env["de"])
    return env


def detect_session_type() -> Dict[str, str]:
    """Deteta se estamos em Wayland ou X11.

    Returns um dicionário com 'session' e 'display_server'.
    """
    session = {"session": "unknown", "display_server": "unknown"}

    # XDG_SESSION_TYPE is set by most modern desktop environments
    session_type = __import__("os").environ.get("XDG_SESSION_TYPE", "")
    display = __import__("os").environ.get("WAYLAND_DISPLAY", "")

    if session_type:
        session["session"] = session_type.lower()
    if display:
        session["display_server"] = "wayland"
    elif not display:
        # Could be X11
        if session["session"] == "x11" or session["session"] == "unknown":
            # Check for XDG_VT1 or just default to trying xset
            session["display_server"] = "x11"

    logger.info("Tipo de sessão detetado: %s (display: %s)", session["session"], session["display_server"])
    return session


def detect_keyboard_layout() -> Dict[str, Any]:
    """Deteta o layout de teclado atual do sistema.

    Tenta usar localectl primeiro, depois setxkbmap -query.
    """
    layout = {"layout": "unknown", "model": "unknown", "variant": "unknown", "options": []}

    # Try localectl (systemd)
    try:
        result = subprocess.run(
            ["localectl", "status"],
            capture_output=True, text=True,
            timeout=5,
        )
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                if "X11 Keyboard" in line:
                    # Parse something like: X11 Keyboard Layout: us
                    parts = line.split(":")
                    if len(parts) >= 2:
                        layout["layout"] = parts[1].strip()
                elif "Model:" in line:
                    layout["model"] = line.split(":", 1)[1].strip()
                elif "Variant:" in line:
                    layout["variant"] = line.split(":", 1)[1].strip()
                elif "Options:" in line:
                    opts = line.split(":", 1)[1].strip()
                    layout["options"] = [o.strip() for o in opts.split(",") if o.strip()]
    except (FileNotFoundError, subprocess.TimeoutExpired):
        logger.warning("localectl falhou ou não disponível")

    # Fallback: setxkbmap -query (only makes sense in X11, but try)
    if layout["layout"] == "unknown":
        try:
            result = subprocess.run(
                ["setxkbmap", "-query"],
                capture_output=True, text=True,
                timeout=5,
            )
            if result.returncode == 0:
                for line in result.stdout.splitlines():
                    if "layout:" in line.lower():
                        layout["layout"] = line.split(":", 1)[1].strip()
                    if "model:" in line.lower():
                        layout["model"] = line.split(":", 1)[1].strip()
                    if "variant:" in line.lower():
                        layout["variant"] = line.split(":", 1)[1].strip()
                    if "options:" in line.lower():
                        opts = line.split(":", 1)[1].strip()
                        layout["options"] = [o.strip() for o in opts.split(",") if o.strip()]
        except FileNotFoundError:
            logger.warning("setxkbmap não disponível")

    logger.info("Layout de teclado detetado: %s (variant: %s)", layout["layout"], layout["variant"])
    return layout


def detect_available_tools() -> Dict[str, bool]:
    """Deteta quais ferramentas Linux estão disponíveis.

    Returns dicionário com a disponibilidade de cada ferramenta.
    """
    tools = {
        "localectl": False,
        "setxkbmap": False,
        "gsettings": False,
        "xfconf-query": False,
        "kwriteconfig": False,
        "xkbcomp": False,
    }

    for tool in tools:
        try:
            subprocess.run(
                [tool, "--version"],
                capture_output=True, text=True,
                timeout=3,
            )
            tools[tool] = True
        except FileNotFoundError:
            pass

    logger.info("Ferramentas disponíveis: %s", tools)
    return tools


def full_detection() -> Dict[str, Any]:
    """Executa deteção completa e retorna tudo em um dicionário estruturado."""
    return {
        "distribution": detect_distribution(),
        "desktop_environment": detect_desktop_environment(),
        "session_type": detect_session_type(),
        "keyboard_layout": detect_keyboard_layout(),
        "available_tools": detect_available_tools(),
    }