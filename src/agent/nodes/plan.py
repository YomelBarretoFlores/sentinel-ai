from typing import Dict, Any
from ..state import AgentState
from ...core.memory import memory
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from ...core.config import config
from ...core.event_bus import log
from ...core.utils import check_stop

llm = ChatOpenAI(model=config.MODEL_NAME, temperature=config.TEMPERATURE)


def ensure_sudo(command: str) -> str:
    if command.startswith("sudo "):
        return command
    prefixes = ["service ", "kill ", "pkill ", "rm ", "chmod ", "chown ",
                "apt ", "dpkg ", "nginx", "systemctl ", "fuser ", "docker "]
    for prefix in prefixes:
        if command.strip().startswith(prefix):
            return f"sudo {command.strip()}"
    return command


def plan_node(state: AgentState) -> Dict[str, Any]:
    log("plan", "Generando plan de remediacion...")
    diagnosis = state.get("diagnosis_log", [])[-1] if state.get("diagnosis_log") else "Sin diagnostico"
    error = state.get("current_error", "desconocido")
    service = state.get("affected_service", "desconocido")
    retry_count = state.get("retry_count", 0)

    failed_commands = memory.get_failed_commands(error)
    failed_str = ""
    if failed_commands:
        failed_str = "\nCOMANDOS QUE YA FALLARON (PROHIBIDO repetirlos):\n"
        for cmd in failed_commands:
            failed_str += f"- {cmd}\n"

    messages = [
        SystemMessage(content=(
            "Eres un motor de automatizacion DevOps.\n"
            "Genera un plan de remediacion con 1 a 3 comandos de shell.\n\n"
            "CONTEXTO:\n"
            f"- Servicio afectado: {service}\n"
            "- Te conectas via SSH como usuario 'sentinel' (NO root)\n"
            "- TODOS los comandos de administracion necesitan 'sudo'\n"
            "- Este es un servidor Ubuntu dentro de Docker\n"
            "- Herramientas disponibles: ss, kill, pkill, ps, grep, cat, nginx, service\n"
            "- NO tiene: systemctl, lsof, fuser\n\n"
            "REGLAS:\n"
            "1. Genera entre 1 y 3 comandos, uno por linea.\n"
            "2. NO uses && ni || ni ; para encadenar.\n"
            "3. TODOS los comandos de admin llevan 'sudo'.\n"
            "4. Responde SOLO con los comandos, sin explicacion ni backticks.\n"
            "5. NUNCA repitas un comando que ya fallo.\n"
            "6. Basa tu solucion en el diagnostico proporcionado.\n"
            "7. Usa SIEMPRE la bandera '-y' o '--yes' en apt-get, yum, etc. para modo no interactivo.\n"
            "8. SI hay error de 'lock' o 'dpkg interrupted', sugiere 'sudo dpkg --configure -a'.\n"
            "9. PROHIBIDO usar: systemctl, lsof, fuser (no instalados).\n"
            f"{failed_str}"
        )),
        HumanMessage(content=(
            f"Error: {error}\n"
            f"Intento: {retry_count + 1}\n"
            f"Diagnostico: {diagnosis}"
        ))
    ]

    response = llm.invoke(messages)
    raw = response.content.strip().replace("`", "").replace("```", "")
    commands = [line.strip() for line in raw.split("\n")
                if line.strip() and not line.strip().startswith("#")]
    commands = [ensure_sudo(cmd) for cmd in commands]

    if not commands:
        commands = [f"sudo service {service} restart"]
        log("plan", "LLM no genero comandos validos. Usando fallback generico.")

    plan_str = " -> ".join(commands)
    log("plan", f"Comandos propuestos: {plan_str}")

    return {
        "current_step": "plan",
        "candidate_plan": "\n".join(commands),
        "approval_status": "PENDING"
    }
