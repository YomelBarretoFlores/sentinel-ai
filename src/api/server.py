from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from .routes import router
from .state import AGENT_STATE
from ..core.event_bus import log
from ..core.knowledge import init_knowledge_base
import threading


@asynccontextmanager
async def lifespan(app: FastAPI):

    log("system", "Sentinel AI Iniciado (Modo API) 🚀")
    
    threading.Thread(target=init_knowledge_base, daemon=True).start()
    
    yield

    log("system", "Apagando Sentinel AI...")


app = FastAPI(title="Sentinel AI API", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

@app.get("/")
def root():
    return {
        "status": "ok", 
        "service": "Sentinel AI API", 
        "mode": "on-demand",
        "agent_status": AGENT_STATE["status"]
    }
