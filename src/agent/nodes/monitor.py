from typing import Dict, Any
from ..state import AgentState
from ...tools.ssh import SSHClient
from ...core.config import config
from ...core.event_bus import log
from ...core.utils import check_stop


def get_ssh_client():
    return SSHClient(
        hostname=config.SSH_HOST,
        port=config.SSH_PORT,
        username=config.SSH_USER,
        password=config.SSH_PASS
    )


def monitor_node(state: AgentState) -> Dict[str, Any]:
    check_stop()
    log("monitor", "Verificando estado de los servicios...")

    ssh = get_ssh_client()
    services_snapshot = {}
    any_failure = None
    failed_service = None
    
    try:
        for service_name, service_cfg in config.SERVICES.items():
            code, out, err = ssh.execute_command(service_cfg["check_command"])
            is_running = service_cfg["running_indicator"] in out
            
            status = "running" if is_running else "stopped"
            details = out.strip() if not is_running else "Service is active"
            
            services_snapshot[service_name] = {
                "status": status,
                "details": details,
                "type": service_cfg["type"]
            }

            if not is_running and not any_failure:
                any_failure = f"Servicio '{service_name}' no esta activo."
                failed_service = service_name
                log("monitor", f"{service_name} CAIDO: {out.strip()}")
            elif is_running:
                log("monitor", f"Servicio {service_name} OK")

        ssh.close()
        
        log("status_update", "Estado de servicios actualizado", services_snapshot)

        if any_failure:
            return {
                "current_step": "monitor",
                "current_error": any_failure,
                "affected_service": failed_service
            }
            
        log("monitor", "Todos los servicios activos.")
        return {"current_step": "monitor", "current_error": None, "affected_service": None}

    except Exception as e:
        error_msg = f"Fallo en la conexion SSH: {str(e)}"
        log("error", error_msg)
        
        error_snapshot = {
            name: {"status": "error", "details": "SSH Connect Fail", "type": cfg["type"]}
            for name, cfg in config.SERVICES.items()
        }
        log("status_update", "Error de conexion SSH", error_snapshot)
        
        return {
            "current_step": "monitor",
            "current_error": error_msg,
            "affected_service": "ssh"
        }
