from typing import Dict, Any
from ..state import AgentState
from ...tools.ssh import SSHClient
from ...core.config import config
from ...core.event_bus import log


def get_ssh_client():
    return SSHClient(
        hostname=config.SSH_HOST,
        port=config.SSH_PORT,
        username=config.SSH_USER,
        password=config.SSH_PASS
    )


def verify_node(state: AgentState) -> Dict[str, Any]:
    log("verify", "Comprobando si el servicio se recupero...")
    service = state.get("affected_service", "")
    service_cfg = config.SERVICES.get(service, {})

    if not service_cfg:
        log("error", f"Servicio '{service}' no encontrado en configuracion.")
        return {
            "current_step": "verify",
            "current_error": f"Servicio '{service}' sin configuracion de verificacion.",
            "retry_count": state.get("retry_count", 0) + 1
        }

    ssh = get_ssh_client()
    try:
        code, out, err = ssh.execute_command(service_cfg["check_command"])
        ssh.close()

        if service_cfg["running_indicator"] in out:
            log("verify", f"Servicio '{service}' RECUPERADO.")
            return {"current_step": "verify", "current_error": None}
        else:
            retry = state.get("retry_count", 0) + 1
            log("warning", f"Servicio '{service}' sigue caido. Intento {retry}.")
            return {
                "current_step": "verify",
                "current_error": state.get("current_error"),
                "retry_count": retry
            }
    except Exception as e:
        log("error", f"Error en verificacion: {e}")
        return {
            "current_step": "verify",
            "current_error": str(e),
            "retry_count": state.get("retry_count", 0) + 1
        }
