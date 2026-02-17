import uvicorn
import os

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    # En produccion, quitamos reload=True para evitar cuelgues
    uvicorn.run("src.api.server:app", host="0.0.0.0", port=port, reload=False)
