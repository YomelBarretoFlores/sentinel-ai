from typing import Dict, Any
from ..state import AgentState
from ...tools.ssh import SSHClient
from ...core.config import config
from ...core.memory import memory
from ...core.event_bus import log
from ...core.utils import check_stop


def get_ssh_client():
    return SSHClient(
        hostname=config.SSH_HOST,
        port=config.SSH_PORT,
        username=config.SSH_USER,
        password=config.SSH_PASS
    )


def execute_node(state: AgentState) -> Dict[str, Any]:
    check_stop()
    log("execute", "Iniciando ejecucion de comandos...")
    plan = state.get("candidate_plan", "")

    if state.get("approval_status") != "APPROVED":
        log("warning", "Comando no aprobado. Saltando ejecucion.")
        return {"current_step": "execute"}

    commands = [cmd.strip() for cmd in plan.split("\n") if cmd.strip()]
    if not commands:
        log("warning", "No hay comandos para ejecutar.")
        return {"current_step": "execute"}

    ssh = get_ssh_client()
    all_results = []
    overall_success = True

    try:
        for i, command in enumerate(commands):
            needs_sudo = command.strip().startswith("sudo")
            clean = command.replace("sudo ", "", 1) if needs_sudo else command

            log("execute", f"[{i+1}/{len(commands)}] {command}")
            code, out, err = ssh.execute_command(clean, use_sudo=needs_sudo)

            result_str = f"[{command}] codigo:{code}"
            if out:
                result_str += f" salida:{out[:200]}"
                log("execute", f"Salida: {out[:100]}...")
            if err:
                result_str += f" error:{err[:200]}"
                log("error", f"Error: {err[:100]}...")

            all_results.append(result_str)

            if code != 0:
                overall_success = False
                log("error", f"Fallo en paso {i+1}. Exit code: {code}")

        ssh.close()

        error_text = state.get("current_error", "")
        diagnosis_text = state.get("diagnosis_log", [""])[-1] if state.get("diagnosis_log") else ""

        memory.save_episode(
            error=error_text,
            diagnosis=diagnosis_text,
            command=plan,
            result=" | ".join(all_results),
            success=overall_success
        )

        status = "exitoso" if overall_success else "parcial"
        log("execute", f"Episodio registrado: {status}")

        return {
            "current_step": "execute",
            "diagnosis_log": state.get("diagnosis_log", []) + [" | ".join(all_results)]
        }

    except Exception as e:
        log("error", f"Excepcion durante ejecucion: {e}")
        memory.save_episode(
            error=state.get("current_error", ""),
            diagnosis="",
            command=plan,
            result=f"Excepcion: {str(e)}",
            success=False
        )
        return {
            "current_step": "execute",
            "diagnosis_log": state.get("diagnosis_log", []) + [f"Excepcion: {str(e)}"]
        }
