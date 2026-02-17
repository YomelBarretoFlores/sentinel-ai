from typing import Dict, Any
from ..state import AgentState
from ...core.security import validate_command, is_critical
from ...core.event_bus import log


def approve_node(state: AgentState) -> Dict[str, Any]:
    log("approve", "Evaluando seguridad de comandos...")
    plan = state.get("candidate_plan", "")
    service = state.get("affected_service", "desconocido")

    commands = [cmd.strip() for cmd in plan.split("\n") if cmd.strip()]
    security_flags = []
    has_critical = False

    for cmd in commands:
        is_valid, reason = validate_command(cmd)
        if not is_valid:
            log("security", f"BLOQUEADO: {cmd} -> {reason}")
            security_flags.append(f"BLOQUEADO: {reason}")
            return {
                "current_step": "approval",
                "approval_status": "REJECTED",
                "security_flags": security_flags,
                "escalation_reason": reason
            }

        if is_critical(cmd):
            has_critical = True
            security_flags.append(f"CRITICO: {cmd}")

    if has_critical:
        log("warning", "Comandos criticos detectados. Solicitando aprobacion manual.")
        return {
            "current_step": "approval",
            "approval_status": "WAITING_APPROVAL",
            "security_flags": security_flags
        }
    else:
        log("approve", "Comandos seguros. Ejecucion automatica.")
        
    return {
        "current_step": "approval",
        "approval_status": "APPROVED",
        "security_flags": security_flags
    }
