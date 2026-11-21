"""Utilities gerais para o US-PT Keyboard Fix.

Funções auxiliares usadas em vários módulos:
- Formatação de cores para terminal.
- Helpers de subprocesso seguros.
- Formatação de data/hora.
- Logging helpers.
"""

import logging
import os
import sys
from typing import Any, Dict, List, Optional, Tuple

# Configuração de cores para terminal (se suportado)
USE_COLOR = os.isatty(sys.stdout.fileno()) if hasattr(sys.stdout, "fileno") else False

# ANSI color codes
COLORS = {
    "reset": "\033[0m",
    "bold": "\033[1m",
    "red": "\033[31m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "blue": "\033[34m",
    "magenta": "\033[35m",
    "cyan": "\033[36m",
    "white": "\033[37m",
}

# Severity colors
SEVERITY_COLORS = {
    "critical": "red",
    "high": "red",
    "medium": "yellow",
    "low": "green",
    "info": "blue",
}


def colorize(text: str, color: str) -> str:
    """Adiciona cor a um texto se o terminal suportar."""
    if not USE_COLOR:
        return text
    color_code = COLORS.get(color, "")
    return f"{color_code}{text}{COLORS['reset']}"


def format_severity(severity: str) -> str:
    """Formata um nível de severidade com cor."""
    color = SEVERITY_COLORS.get(severity, "white")
    return colorize(f"[{severity.upper()}]", color)


def run_subprocess_safe(
    args: List[str],
    description: str = "",
    timeout: int = 30,
    check: bool = True,
) -> subprocess.CompletedProcess:
    """Executa um subprocesso de forma segura (sem shell=True).

    Args:
        args: Lista de argumentos (nunca usar shell=True).
        description: Descrição para logs (opcional).
        timeout: Timeout em segundos.
        check: Se True, lança exception se returncode != 0.

    Returns:
        CompletedProcess result.
    """
    import subprocess as sp
    try:
        proc = sp.run(
            args,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if check and proc.returncode != 0:
            logger.error(
                "Comando falhou (%d): %s\nstdout: %s\nstderr: %s",
                proc.returncode, description, proc.stdout, proc.stderr
            )
            if check:
                raise subprocess.CalledProcessError(
                    proc.returncode, args
                )
        return proc
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError) as e:
        logger.error("Erro ao executar subprocesso: %s", str(e))
        raise


def detect_terminal_width() -> int:
    """Tenta detectar a largura do terminal."""
    try:
        import fcntl
        import termios
        cr = struct = None
        # Simple attempt
        return 80  # Default
    except ImportError:
        return 80


def truncate_text(text: str, max_len: int, end: str = "...") -> str:
    """Trunca um texto para o comprimento máximo especificado."""
    if len(text) <= max_len:
        return text
    return text[: max_len - len(end)] + end


def escape_pipe(text: str) -> str:
    """Escape a pipe character for safe use in formatted output."""
    return text.replace("|", " ")


def format_table_row(*cells: str, colors: List[str] = None) -> str:
    """Formata uma linha de tabela com separadores seguros."""
    pipe = "|"
    cells = [str(c) for c in cells]
    
    # If any cell contains a pipe, escape it
    cells = [escape_pipe(c) for c in cells]
    
    # Pad cells to similar width if needed
    max_width = max(len(c) for c in cells) if cells else 0
    
    formatted_cells = []
    for i, cell in enumerate(cells):
        color = colors[i] if colors and i < len(colors) else None
        if color:
            cell = colorize(cell, color)
        formatted_cells.append(cell.ljust(max_width + 2))
    
    return pipe + pipe.join(formatted_cells) + pipe


def log_context(**context: Any) -> None:
    """Logger com contexto adicional.

    Args:
        **context: Chaves e valores a incluir no log.
    """
    logger = logging.getLogger("uspt.utils")
    # Create a simple dict to add to log record
    extra = {}
    for k, v in context.items():
        extra[k] = v
    logger.info("Contexto: %s", extra)


def safe_filename(name: str) -> str:
    """Remove/invalida caracteres de um nome para ser usado como nome de ficheiro."""
    # Remove control characters and problematic chars
    import re
    # Keep alphanumeric, hyphen, underscore, dot
    safe = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', name)
    # Limit length
    if len(safe) > 100:
        safe = safe[:100]
    return safe