# 🤖 AI DevOps Assistant

> A production-oriented, privacy-first AI DevOps assistant powered by a local **Qwen3.5-2B GGUF** model and **llama.cpp**.

The project is being built hands-on from local LLM inference to RAG, agentic workflows, MCP integrations, Kubernetes diagnostics, evaluation, observability, and production deployment.

## 🚧 Project Status

**Current phase: Phase 1 — Local LLM Incident Analyzer**

Implemented:

- Local Qwen3.5-2B GGUF inference
- CPU-only llama.cpp inference
- FastAPI REST API
- Structured incident-analysis output
- Pydantic request/response validation
- Evidence-focused root-cause prompting
- Request IDs and HTTP timing headers
- Health and readiness endpoints
- Application logging
- Docker container definition
- Initial automated tests

## 🏗️ Current Architecture

```text
Client
  │
  ▼
FastAPI
  │
  ▼
Incident Analyzer
  │
  ▼
llama.cpp
  │
  ▼
Qwen3.5-2B GGUF
  │
  ▼
Structured JSON
  │
  ▼
Pydantic Validation
```

## 🧪 Example

### Request

```json
{
  "service": "payment-service",
  "environment": "production",
  "description": "Payment pods are repeatedly restarting",
  "logs": "ERROR database connection timeout after 30 seconds\nERROR failed to connect to database"
}
```

### Response

```json
{
  "summary": "Payment service pods are experiencing repeated restarts due to database connection timeouts.",
  "severity": "HIGH",
  "root_cause": "Database connection failures are causing the application to restart.",
  "evidence": [
    "Database connection timeout is present in the logs",
    "Database connection failure is present in the logs"
  ],
  "recommended_actions": [
    "Verify database availability",
    "Check database connectivity from the workload",
    "Review database connection configuration"
  ],
  "confidence": 0.90,
  "processing_time_ms": 0.0
}
```

## 📁 Project Structure

```text
ai-devops-assistant/
├── app/
│   ├── core/
│   │   ├── config.py
│   │   └── logging.py
│   ├── schemas/
│   │   └── incident.py
│   ├── llm.py
│   ├── main.py
│   └── schemas.py
├── tests/
│   ├── test_health.py
│   └── test_schemas.py
├── models/                 # local GGUF files; not committed
├── .env.example
├── .gitignore
├── Dockerfile
├── requirements.txt
└── README.md
```

## ⚙️ Local Setup

### 1. Clone

```bash
git clone https://github.com/Madhumankatha/ai-devops-assistant.git
cd ai-devops-assistant
```

### 2. Create a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

For Windows CPU-only development, install a compatible pre-built `llama-cpp-python` wheel when available for your Python version, then install the remaining requirements:

```powershell
python -m pip install -r requirements.txt
```

> If pip attempts to compile `llama-cpp-python` and reports missing C/C++ build tools, use a compatible pre-built CPU wheel or install the required native build toolchain.

### 4. Add the model

Place your Qwen GGUF file under:

```text
models/
```

Configure `.env`:

```text
MODEL_PATH=./models/your-qwen3.5-2b-model.gguf
N_CTX=4096
N_THREADS=8
N_BATCH=256
LOG_LEVEL=INFO
```

The `.gguf` model is intentionally excluded from GitHub.

### 5. Run

```powershell
uvicorn app.main:app --reload
```

Open Swagger UI:

```text
http://127.0.0.1:8000/docs
```

Health:

```text
GET /health
```

Readiness:

```text
GET /ready
```

Incident analysis:

```text
POST /api/v1/analyze
```

### 6. Run tests

```powershell
pytest -q
```

## 🗺️ Roadmap

### Phase 1 — Local LLM ✅

- [x] Qwen3.5-2B GGUF
- [x] llama.cpp CPU inference
- [x] FastAPI
- [x] Structured output
- [x] Validation
- [x] Health/readiness
- [x] Logging
- [x] Initial tests

### Phase 2 — Tool Calling 🚧

- [ ] Tool abstraction
- [ ] Safe tool execution
- [ ] Kubernetes diagnostic tools
- [ ] Git repository tools
- [ ] Prometheus query tools
- [ ] Human approval for risky actions

### Phase 3 — Enterprise RAG

- [ ] Document ingestion
- [ ] Chunking
- [ ] Embeddings
- [ ] PostgreSQL + pgvector
- [ ] Hybrid retrieval
- [ ] Reranking
- [ ] Citations
- [ ] RBAC

### Phase 4 — Agentic AI

- [ ] LangGraph
- [ ] Stateful agents
- [ ] Memory
- [ ] Tool orchestration
- [ ] Agentic RAG
- [ ] Failure recovery

### Phase 5 — MCP

- [ ] MCP server architecture
- [ ] Kubernetes MCP integration
- [ ] Git/MCP integration
- [ ] Observability integrations

### Phase 6 — AI DevOps Investigation

```text
User
 ↓
AI DevOps Agent
 ↓
Kubernetes + Git + Prometheus
 ↓
Evidence Correlation
 ↓
Root Cause Analysis
 ↓
Fix Plan
 ↓
Human Approval
 ↓
Safe Remediation
```

### Phase 7 — Evaluation & Observability

- [ ] RAG evaluation
- [ ] Agent evaluation
- [ ] Hallucination checks
- [ ] LLM tracing
- [ ] Latency metrics
- [ ] Token/compute metrics
- [ ] Quality dashboards

### Phase 8 — Production

- [ ] Docker
- [ ] Kubernetes
- [ ] Helm
- [ ] Argo CD
- [ ] Security controls
- [ ] FDE case study

## 🎯 Portfolio Goal

The final system will demonstrate practical engineering across:

**Local LLM → Structured Generation → Tool Calling → RAG → Agents → MCP → Kubernetes → Observability → Evaluation → Production AI**

## License

MIT
