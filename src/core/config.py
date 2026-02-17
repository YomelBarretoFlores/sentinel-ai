import os
import json
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()


class Config:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    MODEL_NAME = "gpt-4o"
    TEMPERATURE = 0

    PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
    PINECONE_INDEX = "sentinel-ai-index"
    PINECONE_INDEX_NAME = PINECONE_INDEX

    LLAMA_CLOUD_API_KEY = os.getenv("LLAMA_CLOUD_API_KEY")
    EMBED_MODEL = "text-embedding-3-small"
    EMBEDDING_MODEL = EMBED_MODEL
    EMBEDDING_DIM = 1536

    SSH_HOST = os.getenv("SSH_HOST", "localhost")
    SSH_PORT = int(os.getenv("SSH_PORT", 2222))
    SSH_USER = os.getenv("SSH_USER", "sentinel")
    SSH_PASS = os.getenv("SSH_PASS", "securepassword123")

    DATA_DIR = "data"
    MANUALS_DIR = os.path.join(DATA_DIR, "manuals")
    MEMORY_DIR = os.path.join(DATA_DIR, "memory")
    SERVICES_FILE = os.path.join(DATA_DIR, "services.json")

    MONITOR_INTERVAL = 30
    MAX_RETRIES = 5
    
    # Default Services
    DEFAULT_SERVICES = {
        "nginx": {
            "check_command": "service nginx status",
            "running_indicator": "is running",
            "type": "web_server"
        },
        "postgresql": {
            "check_command": "service postgresql status",
            "running_indicator": "online",
            "type": "database"
        },
        "ssh": {
            "check_command": "service ssh status",
            "running_indicator": "is running",
            "type": "system"
        }
    }

    def __init__(self):
        self.SERVICES = self.load_services()

    def load_services(self):
        if os.path.exists(self.SERVICES_FILE):
            try:
                with open(self.SERVICES_FILE, "r") as f:
                    return json.load(f)
            except Exception:
                return self.DEFAULT_SERVICES.copy()
        return self.DEFAULT_SERVICES.copy()

    def save_services(self):
        Path(self.DATA_DIR).mkdir(parents=True, exist_ok=True)
        with open(self.SERVICES_FILE, "w") as f:
            json.dump(self.SERVICES, f, indent=4)

    def add_service(self, name, check_cmd, indicator, service_type):
        self.SERVICES[name] = {
            "check_command": check_cmd,
            "running_indicator": indicator,
            "type": service_type
        }
        self.save_services()

    def remove_service(self, name):
        if name in self.SERVICES:
            del self.SERVICES[name]
            self.save_services()


config = Config()