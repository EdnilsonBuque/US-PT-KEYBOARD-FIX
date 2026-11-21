"""Sistema de diagnóstico automático para problemas de teclado.

Responsável por identificar:
- Layout incorreto.
- Ausência de configurações necessárias.
- Conflitos XCompose.
- Dependências ausentes.
- Problemas de permissões.
- Incompatibilidades do ambiente gráfico.

Apresenta soluções recomendadas.
"""

import logging
from typing import Any, Dict, List, Optional

from .detector import full_detection
from .configurator import get_current_sources, get_current_xkb_options, diagnose_and_configure
from .altgr import diagnose_altgr_state
from .compose import get_compose_awareness

logger = logging.getLogger(__name__)


def run_full_diagnostic() -> Dict[str, Any]:
    """Executa diagnóstico completo do sistema de teclado.

    Verifica todos osAspectos relevantes e retorna um relatório estruturado.

    Returns dicionário com diagnóstico completo e soluções recomendadas.
    """
    result = {
        "timestamp": __import__("datetime").datetime.now().isoformat(),
        "overall_status": "unknown",
        "issues": [],
        "recommendations": [],
        "actions": [],
    }

    # Step 1: System detection
    detection = full_detection()
    de = detection["desktop_environment"]["de"]
    session = detection["session_type"]["session"]
    layout = detection["keyboard_layout"]["layout"]
    tools = detection["available_tools"]

    result["system"] = {
        "desktop_environment": de,
        "session_type": session,
        "keyboard_layout": layout,
        "available_tools": tools,
    }

    # Check GNOME compatibility
    if de != "gnome":
        result["issues"].append({
            "severity": "high",
            "category": "environment",
            "description": (
                f"Ambiente {detected_env_name(de)} detetado. "
                "Esta versão (v1) suporta apenas GNOME. "
                "Outros ambientes exigem configuração manual ou atualização da ferramenta."
            ),
            "recommended_action": "Configure manualmente ou atualize para a versão futura com suporte a KDE/XFCE."
        })
        result["overall_status"] = "unsupported_environment"
        return result

    # Step 2: Session type issues
    if session == "wayland":
        result["issues"].append({
            "severity": "high",
            "category": "session",
            "description": "Sessão Wayland detetada. setxkbmap não persiste across reboots. "
                           "Use gsettings para configurações duradouras.",
            "recommended_action": "Use gsettings org.gnome.desktop.input-sources em vez de setxkbmap. "
                                  "As configurações persistirão através de reinícios."
        })
    elif session == "x11":
        result["recommendations"].append({
            "category": "info",
            "description": "Sessão X11 detetada. setxkbmap funciona mas não persiste across reboots "
                           "sem salvar em gsettings/dconf."
        })

    # Step 3: Current layout check
    layout_issues = _check_keyboard_layout(layout, session)
    result["issues"].extend(layout_issues)

    # Step 4: XCompose awareness
    compose_awareness = get_compose_awareness()
    if compose_awareness["limitations"]:
        result["issues"].append({
            "severity": "medium",
            "category": "compose",
            "description": "Problemas de compatibilidade XCompose detectados:",
            "details": compose_awareness["limitations"],
            "recommended_action": compose_awareness["recommendation"]
        })

    # Step 5: AltGr state
    altgr_state = diagnose_altgr_state()
    if not altgr_state["altgr_functional"]:
        result["issues"].append({
            "severity": "medium",
            "category": "altgr",
            "description": "AltGr não está configurado para caracteres portugueses.",
            "recommended_action": "Aplicar configuração AltGr (Modalidade B) via uspt configure."
        })
    else:
        result["recommendations"].append({
            "category": "info",
            "description": "AltGr já está configurado corretamente. ",
            "details": altgr_state["diagnostic"]
        })

    # Step 6: Available tools check
    missing_tools = _check_missing_tools(tools)
    if missing_tools:
        result["issues"].append({
            "severity": "high",
            "category": "dependencies",
            "description": "Ferramentas necessárias ausentes ou com funcionalidade limitada:",
            "missing": missing_tools,
            "recommended_action": "Instale as ferramentas faltantes via: sudo apt update && sudo apt install " + ", ".join(missing_tools)
        })

    # Step 7: Current sources evaluation
    current_sources = get_current_sources()
    pt_present = any("pt" in str(s).lower() for s in current_sources)
    if not pt_present:
        result["issues"].append({
            "severity": "medium",
            "category": "configuration",
            "description": "Layout português não está presente nas fontes de entrada atuais.",
            "recommended_action": "Executar uspt configure para adicionar layout português."
        })

    # Step 8: Overall status determination
    critical_issues = [i for i in result["issues"] if i.get("severity") == "high"]
    if critical_issues:
        result["overall_status"] = "critical"
    elif result["issues"]:
        result["overall_status"] = "warning"
    else:
        result["overall_status"] = "ok"

    # Generate recommendations summary
    all_recs = result.get("recommendations", []) + _generate_recommendations(result["issues"])
    result["recommendations"] = all_recs

    logger.info("Diagnóstico completo concluído: status=%s, issues=%d", result["overall_status"], len(result["issues"]))
    return result


def _check_keyboard_layout(layout: str, session: str) -> List[Dict[str, Any]]:
    """Verifica se o layout de teclado está corretamente configurado."""
    issues = []

    if not layout or layout == "unknown":
        issues.append({
            "severity": "high",
            "category": "layout_unknown",
            "description": "Não foi possível detetar o layout de teclado atual. "
                           "Isso pode indicar problemas de permissão ou ferramentas ausentes.",
            "recommended_action": "Verifique se localectl ou setxkbmap estão disponíveis e com permissões adequadas."
        })
        return issues

    # Check if Portuguese layout is present
    layout_lower = layout.lower()
    is_pt = layout_lower in ("pt", "pt_br")
    is_us = layout_lower in ("us", "us_intl")

    if is_pt:
        # Portuguese layout - should have characters available
        issues.append({
            "severity": "low",
            "category": "layout_ok",
            "description": "Layout português detetado. Caracteres acentuados devem estar disponíveis.",
            "recommended_action": "Nenhuma ação necessária se os caracteres funcionarem."
        })
    elif is_us or layout_lower.startswith("us"):
        # US layout - may need modalities
        issues.append({
            "severity": "medium",
            "category": "us_layout",
            "description": "Layout US detetado. Caracteres portugueses requerem configuração "
                           "adicional (Modalidade A ou B).",
            "recommended_action": "Execute uspt configure com a Modalidade B (AltGr) para ç/Ç, "
                                  "ou Modalidade A (teclas mortas) se preferir."
        })
    else:
        issues.append({
            "severity": "medium",
            "category": "unknown_layout",
            "description": f"Layout '{layout}' desconhecido. A ferramenta pode reconfigurá-lo.",
            "recommended_action": "Execute uspt diagnose para mais detalhes ou uspt configure para tentar auto-detectar e corrigir."
        })

    return issues


def _check_missing_tools(available: Dict[str, bool]) -> List[str]:
    """Verifica quais ferramentas esperadas estão ausentes."""
    missing = []
    # Critical tools for GNOME
    critical = ["gsettings"]
    # Tools that are nice-to-have
    nice = ["localectl", "setxkbmap", "xfconf-query", "kwriteconfig"]

    for tool in critical:
        if not available.get(tool, False):
            missing.append(tool)

    # Only check nice-to-have if we're on the right DE
    # For now, just report critical

    return missing


def _generate_recommendations(issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Gera recomendações baseadas nos issues encontrados."""
    recs = []

    # Map issues to recommendations
    for issue in issues:
        cat = issue.get("category", "")
        if cat == "session":
            recs.append({
                "category": "action",
                "description": "Aplicar configuração via gsettings",
                "action": "uspt configure --modalidade altgr"
            })
        elif cat == "altgr":
            recs.append({
                "category": "action",
                "description": "AltGr já configurado ou necessidade de configuração",
                "action": "Sem ação — AltGr já funcional" if issue.get("severity") == "low" else "uspt configure --modalidade altgr"
            })
        elif cat == "compose":
            recs.append({
                "category": "info",
                "description": "Considerar Modalidade B em vez de A",
                "action": "uspt configure --modalidade altgr (recomendado para Wayland)"
            })
        elif cat == "dependencies":
            recs.append({
                "category": "action",
                "description": "Instalar dependências faltantes",
                "action": "sudo apt update && sudo apt install " + issue.get("missing", ["gsettings"])[0]
            })
        elif cat == "environment":
            recs.append({
                "category": "limitations",
                "description": "Ambiente não suportado na v1",
                "action": "Aguardar versão futura ou configuração manual"
            })

    return recs


def diagnose_layout_issues() -> Dict[str, Any]:
    """Diagnosta problemas específicos de layout e retorna soluções.

    Returns dicionário focado em problemas de layout.
    """
    detection = full_detection()
    session = detection["session_type"]["session"]
    de = detection["desktop_environment"]["de"]
    layout = detection["keyboard_layout"]["layout"]

    result = {
        "desktop_environment": de,
        "session_type": session,
        "current_layout": layout,
        "issues": [],
        "solutions": [],
    }

    if de != "gnome":
        result["issues"].append("Ambiente não-GNOME — v1 limita-se a GNOME")
        result["solutions"].append("Atualize para versão futura com suporte multi-DE")
        return result

    # Layout-specific issues
    if not layout:
        result["issues"].append("Não foi possível detetar layout")
        result["solutions"].append("Verifique permissões; instale localectl/setxkbmap")
    elif layout.lower() in ("us", "us_intl"):
        result["issues"].append("Layout US — caracteres portugueses não disponíveis por defeito")
        # Solution depends on session
        if session == "wayland":
            result["solutions"].append("uspt configure --modalidade altgr (recomendado)")
            result["solutions"].append("Alternativa: uspt configure --modalidade dead_keys (pode não funcionar em todos os apps)")
        else:  # x11
            result["solutions"].append("uspt configure --modalidade altgr")
            result["solutions"].append("Alternativa: setxkbmap us intl (não persiste across reboots)")
    elif layout.lower() in ("pt", "pt_br"):
        result["issues"].append("Layout português — verifique se todos os caracteres funcionam")
        result["solutions"].append("Nenhuma mudança necessária se caracteres funcionarem")
        result["solutions"].append("Execute uspt diagnose para verificar configurações complementares")
    else:
        result["issues"].append(f"Layout desconhecido: {layout}")
        result["solutions"].append("uspt configure — tentativa de reconfiguração para Portuguese")

    return result