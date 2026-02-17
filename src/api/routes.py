from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime
import asyncio

from ..core.config import config
from ..core.memory import memory
from ..core import knowledge
from ..tools.ssh import SSHClient
from ..core.event_bus import bus, log
from ..agent.graph import app as agent_graph

router = APIRouter()

class ChatRequest(BaseModel):
    query: str

class ChatResponse(BaseModel):
    response: str

class ServiceRequest(BaseModel):
    name: str
    check_command: str
    running_indicator: str
    type: str = "custom"

@router.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket):
    await websocket.accept()
    queue = await bus.subscribe()
    try:
        while True:
            data = await queue.get()
            await websocket.send_json(data)
    except WebSocketDisconnect:
        bus.unsubscribe(queue)
    except Exception as e:
        log("error", f"WebSocket error: {e}")
        bus.unsubscribe(queue)

def run_agent_task():
    from .state import AGENT_STATE
    
    if AGENT_STATE["status"] == "running":
        return

    AGENT_STATE["status"] = "running"
    AGENT_STATE["stop_requested"] = False
    AGENT_STATE["last_run"] = datetime.now().isoformat()
    log("system", "Ejecutando ciclo de analisis bajo demanda...")

    try:
        initial_state = {
            "current_step": "monitor",
            "current_error": None,
            "affected_service": None,
            "retry_count": 0,
            "diagnosis_log": [],
            "security_flags": []
        }
        
        final_state = agent_graph.invoke(initial_state)
        
        for key, value in final_state.items():
            AGENT_STATE[key] = value

        if final_state.get("approval_status") == "WAITING_APPROVAL":
             AGENT_STATE["status"] = "waiting"
             AGENT_STATE["approval_status"] = "WAITING_APPROVAL"
             log("system", "Agente pausado esperando aprobacion.")
        elif AGENT_STATE.get("stop_requested"):
             AGENT_STATE["status"] = "idle"
             log("system", "Agente detenido por el usuario.")
        else:
             AGENT_STATE["status"] = "idle"
             log("system", "Ciclo de analisis completado.")
        
    except RuntimeError as e:
        if str(e) == "Agent stopped by user":
            AGENT_STATE["status"] = "idle"
            log("system", "Agente detenido manualmente.")
        else:
             AGENT_STATE["status"] = "error"
             log("error", f"Error runtime: {e}")
    except Exception as e:
        AGENT_STATE["status"] = "error"
        log("error", f"Error critico durante la ejecucion del agente: {e}")

@router.post("/agent/run")
def run_agent(background_tasks: BackgroundTasks):
    from .state import AGENT_STATE
    if AGENT_STATE["status"] == "running":
        raise HTTPException(status_code=409, detail="Agent is already running")
    
    background_tasks.add_task(run_agent_task)
    return {"status": "started", "message": "Agent execution triggered"}

@router.post("/agent/stop")
def stop_agent():
    from .state import AGENT_STATE
    if AGENT_STATE["status"] != "running":
        raise HTTPException(status_code=400, detail="Agent is not running")
    
    AGENT_STATE["stop_requested"] = True
    log("system", "Solicitud de parada recibida. Deteniendo agente...")
    return {"status": "stopping", "message": "Stop signal sent to agent"}

def resume_agent_task():
    from .state import AGENT_STATE
    try:
        agent_graph.invoke(AGENT_STATE)
    except Exception as e:
        log("error", f"Error resuming agent: {e}")

@router.post("/agent/approve")
def approve_agent(action: str, background_tasks: BackgroundTasks):
    from .state import AGENT_STATE
    from ..agent.graph import resume_app
    
    if AGENT_STATE.get("status") != "waiting":
        raise HTTPException(status_code=400, detail="Agent is not waiting for approval")

    if action not in ["approve", "reject"]:
        raise HTTPException(status_code=400, detail="Invalid action")

    AGENT_STATE["approval_status"] = "APPROVED" if action == "approve" else "REJECTED"
    AGENT_STATE["status"] = "running"
    
    msg = "Aprobacion recibida. Reanudando..." if action == "approve" else "Rechazado. Escalando..."
    log("system", msg)
    
    def _resume_task():
        try:
            final_state = resume_app.invoke(AGENT_STATE)
            
            for key, value in final_state.items():
                AGENT_STATE[key] = value
            
            if AGENT_STATE.get("stop_requested"):
                 AGENT_STATE["status"] = "idle"
            elif AGENT_STATE.get("approval_status") == "WAITING_APPROVAL":
                 AGENT_STATE["status"] = "waiting"
                 log("system", "Agente pausado esperando aprobacion (ciclo reanudado).")
            else:
                 AGENT_STATE["status"] = "idle"
                 log("system", "Ciclo reanudado completado.")
        except Exception as e:
             AGENT_STATE["status"] = "error"
             log("error", f"Error en reanudacion: {e}")

    background_tasks.add_task(_resume_task)
    return {"status": "resuming", "message": msg}

@router.get("/agent/state")
def get_agent_state():
    from .state import AGENT_STATE
    return AGENT_STATE

@router.get("/status")
def get_status():
    services_status = {}
    
    ssh = None
    try:
        ssh = SSHClient(
            hostname=config.SSH_HOST,
            port=config.SSH_PORT,
            username=config.SSH_USER,
            password=config.SSH_PASS
        )
    except Exception as e:
        for name, cfg in config.SERVICES.items():
            services_status[name] = {
                "status": "error",
                "details": f"SSH unavailable: {str(e)}",
                "type": cfg["type"]
            }
        return services_status
    
    try:
        for name, cfg in config.SERVICES.items():
            try:
                code, out, err = ssh.execute_command(cfg["check_command"])
                is_running = cfg["running_indicator"] in out
                services_status[name] = {
                    "status": "running" if is_running else "stopped",
                    "details": out.strip() if not is_running else "Service is active",
                    "type": cfg["type"]
                }
            except Exception as e:
                 services_status[name] = {
                    "status": "error",
                    "details": str(e),
                    "type": cfg["type"]
                }
    finally:
        if ssh:
            ssh.close()
        
    return services_status

@router.get("/services")
def list_services():
    return config.SERVICES

@router.post("/services")
def add_service(service: ServiceRequest):
    config.add_service(
        service.name, 
        service.check_command, 
        service.running_indicator, 
        service.type
    )
    log("config", f"Servicio '{service.name}' agregado al monitoreo.")
    return {"status": "ok", "message": f"Service {service.name} added"}

@router.delete("/services/{name}")
def delete_service(name: str):
    if name not in config.SERVICES:
        raise HTTPException(status_code=404, detail="Service not found")
    
    config.remove_service(name)
    log("config", f"Servicio '{name}' eliminado del monitoreo.")
    return {"status": "ok", "message": f"Service {name} removed"}

@router.get("/memory")
def get_memory():
    return memory.get_episodes()

from fastapi.responses import StreamingResponse
import json

@router.post("/chat")
def chat(request: ChatRequest):
    if not knowledge.kb:
        # Si aun esta cargando, intentamos inicializarlo al vuelo (opcional pero lento)
        raise HTTPException(status_code=503, detail="Knowledge base is initializing. Please try again in a few seconds.")
    
    def event_stream():
        try:
            for event in knowledge.kb.stream_query(request.query):
                yield f"event: {event['event']}\ndata: {json.dumps(event['data'])}\n\n"
        except Exception as e:
            error_data = json.dumps({"error": str(e)})
            yield f"event: error\ndata: {error_data}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")

@router.get("/config")
def get_config():
    return {
        "services": list(config.SERVICES.keys()),
        "interval": config.MONITOR_INTERVAL,
        "max_retries": config.MAX_RETRIES,
        "mode": "on-demand"
    }
