from typing import Dict, Any
from ..state import AgentState
from ...core.knowledge import kb
from ...core.memory import memory
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from ...core.config import config
from ...core.event_bus import log
from ...core.utils import check_stop

llm = ChatOpenAI(model=config.MODEL_NAME, temperature=config.TEMPERATURE)


def diagnose_node(state: AgentState) -> Dict[str, Any]:
    check_stop()
    log("diagnose", "Analizando el problema...")
    error = state.get("current_error", "")
    service = state.get("affected_service", "desconocido")
    prior_logs = state.get("diagnosis_log", [])
    retry_count = state.get("retry_count", 0)

    memory_context = ""
    memory_consulted = False

    failed_commands = memory.get_failed_commands(error)
    if failed_commands:
        memory_consulted = True
        memory_context += "COMANDOS QUE YA FALLARON (NO repetir):\n"
        for cmd in failed_commands:
            memory_context += f"- {cmd}\n"
        log("diagnose", f"{len(failed_commands)} comandos fallidos previos identificados.")

    similar = memory.find_similar(error)
    if similar and similar["success"]:
        memory_consulted = True
        memory_context += f"\nSolucion exitosa previa: {similar['command']}\n"
        log("diagnose", "Solucion exitosa previa encontrada en memoria.")

    rag_context = ""
    if kb:
        log("diagnose", "Consultando base de conocimiento (RAG)...")
        rag_context = kb.query(f"How to fix: {error}")
    else:
        log("warning", "Base de conocimiento no disponible.")

    messages = [
        SystemMessage(content=(
            "Eres Sentinel AI, un agente DevOps autonomo.\n"
            "Analiza el error y proporciona un diagnostico BREVE (maximo 3 lineas).\n"
            "Indica la causa probable y la solucion recomendada.\n"
            f"\nServicio afectado: {service}\n"
            f"\nHistorial de intentos:\n{chr(10).join(prior_logs[-3:]) if prior_logs else 'Primer intento.'}\n"
            f"\n{memory_context}"
            f"\nDocumentacion tecnica:\n{rag_context[:1000]}\n"
            "\nREGLAS CRITICAS:"
            "\n1. NO sugieras comandos que ya fallaron (listados arriba)."
            "\n2. Si 'service' o 'apt-get' fallan, prueba alternativas como 'systemctl', 'dmesg', o verificar ficheros de log especificos."
        )),
        HumanMessage(content=f"Error: {error}")
    ]

    response = llm.invoke(messages)
    diagnosis = response.content.strip()
    log("diagnose", f"Diagnostico: {diagnosis[:200]}...")

    return {
        "current_step": "diagnose",
        "diagnosis_log": prior_logs + [diagnosis],
        "memory_consulted": memory_consulted
    }
