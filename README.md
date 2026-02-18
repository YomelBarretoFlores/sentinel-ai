# 🛡️ Sentinel AI - Autonomous DevOps Agent

**Sentinel AI** es un agente autónomo de DevOps diseñado para monitorear, diagnosticar y reparar problemas en servidores Linux en tiempo real. Utiliza IA Generativa (LLMs) potenciada por un sistema RAG (Retrieval-Augmented Generation) para tomar decisiones informadas basadas en documentación técnica oficial.

![Sentinel AI Dashboard](/frontend/public/window.svg)

## 🚀 Características Principales

### 🧠 Cerebro Autónomo (LangGraph)

El agente opera mediante un grafo de decisiones inteligente:

1.  **Monitor:** Detecta servicios caídos o anomalías (Nginx, Docker, PostgreSQL).
2.  **Diagnose:** Analiza logs y errores usando RAG para encontrar la causa raíz.
3.  **Plan:** Genera un plan de reparación paso a paso.
4.  **Approve:** Solicita aprobación humana para comandos críticos (e.g., `rm`, `sudo`).
5.  **Execute:** Ejecuta comandos vía SSH de forma segura.
6.  **Verify:** Confirma que el problema se haya resuelto.

### 📚 Base de Conocimiento (RAG Avanzado)

No alucina soluciones. Consulta manuales técnicos reales indexados en **Pinecone**:

- **PostgreSQL 14** (Admin & Config)
- **Nginx** (Reverse Proxy & Security)
- **Docker** (Compose & Networking)
- **Linux** (Sysadmin protocols)
  Utiliza **Cohere Rerank** para asegurar que la información recuperada sea 100% relevante.

### 💻 Dashboard en Tiempo Real

Una interfaz moderna construida con **Next.js 14** y **Shadcn UI**:

- **Terminal en Vivo:** Ver los comandos y logs del agente mientras piensa y actúa.
- **Estado de Servicios:** Monitoreo visual (Running/Stopped/Error).
- **Chat Interactivo:** Pregúntale al agente sobre infraestructura o logs.
- **Control Total:** Botones para Iniciar/Detener el agente y Aprobar/Rechazar acciones.

### ⚡ Arquitectura On-Demand

Diseñado para la eficiencia y el despliegue en la nube (Render/Vercel):

- **Lazy Loading:** Los modelos de IA solo se cargan cuando son necesarios.
- **WebSocket:** Comunicación bidireccional para actualizaciones instantáneas.
- **Docker Ready:** Fácil despliegue con contenedores.

## 🛠️ Stack Tecnológico

**Backend (Python):**

- **FastAPI:** API REST y WebSockets.
- **LangGraph:** Orquestación del flujo del agente.
- **LlamaIndex:** Gestión de RAG e ingesta de datos.
- **Paramiko:** Cliente SSH seguro.
- **Pydantic:** Validación de datos estricta.

**Frontend (TypeScript):**

- **Next.js 14:** Framework de React (App Router).
- **Tailwind CSS:** Estilizado moderno y responsivo.
- **Shadcn UI:** Componentes de interfaz accesibles y elegantes.
- **Lucide React:** Iconografía consistente.
- **Axios/SWR:** Gestión de peticiones HTTP.

## 📦 Instalación y Uso

### Prerrequisitos

- Python 3.10+
- Node.js 18+
- Claves de API: OpenAI, Pinecone, Cohere.

### 1. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Configurar claves
python run_server.py
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Abra `http://localhost:3000` para acceder al dashboard.

## 🔒 Seguridad

- **Lista Blanca de Comandos:** Solo permite comandos seguros por defecto.
- **Human-in-the-Loop:** Intervención manual requerida para acciones destructivas.
- **SSH Key-based Auth:** Conexión segura a servidores remotos.

---
