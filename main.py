import time
from dotenv import load_dotenv

load_dotenv()

from src.agent.graph import app
from src.core.config import config
from src.core.event_bus import log


def run_cycle():
    initial_state = {
        "messages": [],
        "current_step": "start",
        "current_error": None,
        "affected_service": None,
        "diagnosis_log": [],
        "candidate_plan": None,
        "approval_status": "PENDING",
        "retry_count": 0,
        "memory_consulted": False,
        "security_flags": [],
        "escalation_reason": None
    }

    try:
        for event in app.stream(initial_state):
            for key, value in event.items():
                print(f"[GRAFO] Nodo completado: {key}")
    except Exception as e:
        log("error", f"Fallo en el ciclo: {e}")


def main():
    print("=" * 50)
    print("  Sentinel AI - Agente DevOps Autonomo")
    print("=" * 50)

    services = ", ".join(config.SERVICES.keys())
    print(f"[CONFIG] Servicios monitoreados: {services}")
    print(f"[CONFIG] Intervalo: cada {config.MONITOR_INTERVAL}s")
    print(f"[CONFIG] Max reintentos: {config.MAX_RETRIES}")

    print(f"[MONITOR] Presiona Ctrl+C para detener\n")

    try:
        while True:
            run_cycle()
            print(f"\n[MONITOR] Proximo chequeo en {config.MONITOR_INTERVAL}s...\n")
            time.sleep(config.MONITOR_INTERVAL)
    except KeyboardInterrupt:
        print("\n[MONITOR] Detenido por el operador.")

if __name__ == "__main__":
    main()


