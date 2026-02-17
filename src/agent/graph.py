from langgraph.graph import StateGraph, END
from .state import AgentState
from .nodes import monitor_node, diagnose_node, plan_node, approve_node, execute_node, verify_node
from ..core.config import config
from ..core.event_bus import log


def should_monitor_end(state: AgentState):
    if not state.get("current_error"):
        return "end"
    return "continue"


def should_approve_continue(state: AgentState):
    status = state.get("approval_status")
    if status == "REJECTED":
        log("graph", "Comando rechazado. Escalando.")
        return "escalate"
    elif status == "WAITING_APPROVAL":
        log("graph", "Esperando aprobacion manual. Pausando.")
        return "end"
    return "execute"


def should_verify_end(state: AgentState):
    if not state.get("current_error"):
        log("graph", "Servicio recuperado. Finalizando.")
        return "end"
    retry_count = state.get("retry_count", 0)
    if retry_count >= config.MAX_RETRIES:
        log("graph", f"Limite de reintentos alcanzado ({config.MAX_RETRIES}). Escalando.")
        return "escalate"
    log("graph", f"Reintentando ({retry_count}/{config.MAX_RETRIES}).")
    return "retry"


def report_node(state: AgentState):
    service = state.get("affected_service", "desconocido")
    error = state.get("current_error")
    command = state.get("candidate_plan", "N/A")
    attempts = state.get("retry_count", 0) + 1

    if not error:
        log("report", f"EXITO: Servicio '{service}' recuperado en {attempts} intento(s).")
        log("report", f"Solucion aplicada: {command}")
    return {"current_step": "report"}


def escalation_node(state: AgentState):
    service = state.get("affected_service", "desconocido")
    reason = state.get("escalation_reason") or "Limite de reintentos alcanzado."
    
    log("escalation", f"FALLA CRITICA en '{service}': {reason}")
    log("escalation", "Se requiere intervencion humana.")
    return {"current_step": "escalation", "escalation_reason": reason}


workflow = StateGraph(AgentState)

workflow.add_node("monitor", monitor_node)
workflow.add_node("diagnose", diagnose_node)
workflow.add_node("plan", plan_node)
workflow.add_node("approval", approve_node)
workflow.add_node("execute", execute_node)
workflow.add_node("verify", verify_node)
workflow.add_node("report", report_node)
workflow.add_node("escalation", escalation_node)

workflow.set_entry_point("monitor")

workflow.add_conditional_edges("monitor", should_monitor_end, {"end": END, "continue": "diagnose"})
workflow.add_edge("diagnose", "plan")
workflow.add_edge("plan", "approval")
workflow.add_conditional_edges("approval", should_approve_continue, {"execute": "execute", "escalate": "escalation", "end": END})
workflow.add_edge("execute", "verify")
workflow.add_conditional_edges("verify", should_verify_end, {"end": "report", "retry": "diagnose", "escalate": "escalation"})
workflow.add_edge("report", END)
workflow.add_edge("escalation", END)

app = workflow.compile()

resume_workflow = StateGraph(AgentState)

resume_workflow.add_node("monitor", monitor_node)
resume_workflow.add_node("diagnose", diagnose_node)
resume_workflow.add_node("plan", plan_node)
resume_workflow.add_node("approval", approve_node)
resume_workflow.add_node("execute", execute_node)
resume_workflow.add_node("verify", verify_node)
resume_workflow.add_node("report", report_node)
resume_workflow.add_node("escalation", escalation_node)

resume_workflow.set_entry_point("execute")

resume_workflow.add_conditional_edges("monitor", should_monitor_end, {"end": END, "continue": "diagnose"})
resume_workflow.add_edge("diagnose", "plan")
resume_workflow.add_edge("plan", "approval")
resume_workflow.add_conditional_edges("approval", should_approve_continue, {"execute": "execute", "escalate": "escalation", "end": END})
resume_workflow.add_edge("execute", "verify")
resume_workflow.add_conditional_edges("verify", should_verify_end, {"end": "report", "retry": "diagnose", "escalate": "escalation"})
resume_workflow.add_edge("report", END)
resume_workflow.add_edge("escalation", END)

resume_app = resume_workflow.compile()
