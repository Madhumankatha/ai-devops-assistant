# 🤖 AI DevOps Assistant

> A privacy-first, production-oriented AI DevOps investigation assistant powered by a local **Qwen GGUF** model and **llama.cpp**.

The current MVP combines a local LLM agent loop with safe read-only Kubernetes diagnostics, mock Prometheus telemetry, evidence correlation, and local runbook retrieval. It is designed to demonstrate practical **Agentic AI + DevOps + RAG** engineering without requiring a live Kubernetes cluster.

## 🚀 Current Status

**Phase 1 + Agentic Investigation MVP — working**

Implemented and tested:

- Local Qwen GGUF inference through llama.cpp
- FastAPI REST API
- Structured JSON incident analysis
- Pydantic request/response validation
- Controlled agentic investigation loop
- Tool registry with allow-listed tools
- Read-only Kubernetes diagnostic tools using mock data
- Mock Prometheus service metrics, error rate, and latency
- Evidence accumulation and early-stop sufficiency checks
- Evidence normalization for stable API responses
- Local runbook retrieval and RCA guidance
- RCA synthesis from collected evidence
- Request IDs, HTTP timing, health/readiness endpoints, and logging
- Automated test coverage

> **Important:** Kubernetes and Prometheus data are currently mock/demo data. A live Kubernetes cluster is not required for the current MVP.

## 🧠 What the Agent Does

Given a service, namespace, and incident question, the agent follows a controlled loop:

```text
User Incident
     │
     ▼
 FastAPI API
     │
     ▼
 DevOps Agent
     │
     ├──► Tool Registry
     │      ├── Pod Status
     │      ├── Pod Logs
     │      ├── K8s Events
     │      ├── Deployment Status
     │      ├── Service Metrics
     │      ├── Error Rate
     │      └── P95 Latency
     │
     ▼
 Evidence Collection
     │
     ├── Kubernetes state
     ├── Logs
     ├── Events
     └── Telemetry
     │
     ▼
 Evidence Sufficiency Check
     │
     ▼
 Local Runbook Retrieval
     │
     ▼
 LLM RCA Synthesis
     │
     ▼
 Structured RCA JSON
```

### Safety boundary

The agent is intentionally restricted to diagnostic operations. It does **not** restart, delete, scale, modify, or otherwise mutate Kubernetes resources.

## 🔍 Example Investigation

### Request

```json
{
  "service": "payment-service",
  "namespace": "production",
  "question": "Why is payment-service failing and correlate the Kubernetes state with error rate and latency?"
}
```

### Example RCA

```json
{
  "summary": "The payment-service is experiencing critical failures with high error rate, high latency, and a crashing pod caused by database connection failure.",
  "root_cause": "The payment-service pod cannot establish a database connection during startup, causing application startup failure and CrashLoopBackOff.",
  "evidence": [
    "[get_service_metrics] CPU utilization is 87.5% and memory utilization is 91.2%.",
    "[get_pod_status] payment-service-7d9f8c6f7d-x2k9p is in CrashLoopBackOff with 12 restarts.",
    "[get_pod_logs] Logs contain database connection timeout and failed-to-connect errors.",
    "[get_kubernetes_events] Events show BackOff restarting failed container and readiness probe failure.",
    "[get_error_rate] Error rate is 18.7%.",
    "[get_latency] P95 latency is 1850ms."
  ],
  "recommended_actions": [
    "Verify database availability and connectivity.",
    "Validate database connection configuration and credentials.",
    "Check network connectivity between the service and database.",
    "Restart the deployment only after the underlying configuration or dependency issue is corrected."
  ],
  "confidence": 0.95
}
```

## 🛠️ Tooling

The current registry exposes seven diagnostic tools:

| Tool | Purpose |
|---|---|
| `get_pod_status` | Inspect pod health and restart state |
| `get_pod_logs` | Inspect recent application logs |
| `get_kubernetes_events` | Inspect Kubernetes events |
| `get_deployment_status` | Inspect deployment readiness |
| `get_service_metrics` | CPU, memory, request rate, error rate, latency |
| `get_error_rate` | Service error rate |
| `get_latency` | Service P95 latency |

All tools are registered through a central `ToolRegistry`, giving the agent an explicit allow-list for execution.

## 📁 Project Structure

```text
ai-devops-assistant/
├── app/
│   ├── agent/
│   │   └── controller.py       # Agent loop, evidence checks, RCA synthesis
│   ├── core/                   # Configuration and logging
│   ├── rag/                    # Local runbook retrieval
│   ├── tools/
│   │   ├── kubernetes.py       # Mock K8s diagnostics
│   │   ├── prometheus.py       # Mock telemetry
│   │   └── registry.py         # Tool registry
│   ├── schemas/                # API/tool schemas
│   └── main.py                 # FastAPI application
├── tests/
├── models/                     # Local GGUF files; not committed
├── .agents/                    # Agent workspace guidance
├── .AGENTS.md                  # Repository-level AI engineering instructions
├── .env.example
├── .gitignore
├── Dockerfile
├── requirements.txt
└── README.md
```

## ⚙️ Local Setup

### 1. Clone

```powershell
git clone https://github.com/Madhumankatha/ai-devops-assistant.git
cd ai-devops-assistant
git checkout feature/agentic_ai
```

### 2. Create environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

For Windows CPU-only development, use a compatible pre-built `llama-cpp-python` wheel when available for your Python version. If pip tries to compile it, install the required native build tools or use a compatible wheel.

### 3. Add local model

Place the Qwen GGUF model under:

```text
models/
```

Configure `.env` using `.env.example`.

```text
MODEL_PATH=./models/your-qwen-model.gguf
N_CTX=4096
N_THREADS=8
N_BATCH=256
LOG_LEVEL=INFO
```

Model weights and secrets are intentionally excluded from Git.

### 4. Run

```powershell
uvicorn app.main:app --reload
```

Swagger UI:

```text
http://127.0.0.1:8000/docs
```

### 5. Run tests

```powershell
pytest -q
```

Current baseline: **13 tests passing**.

## 🎬 Demo Flow

A clean portfolio/demo walkthrough is:

### Step 1 — Start the application

```powershell
uvicorn app.main:app --reload
```

### Step 2 — Open Swagger

Open `/docs` and call the investigation endpoint.

### Step 3 — Investigate a realistic incident

Use:

```text
Service: payment-service
Namespace: production
Question: Why is payment-service failing? Correlate pod status, logs, Kubernetes events, error rate, and latency.
```

### Step 4 — Show the agent loop

The logs demonstrate the agent selecting tools, collecting evidence, checking evidence sufficiency, and synthesizing the RCA.

### Step 5 — Show the RCA

Highlight:

- CrashLoopBackOff
- Database connection timeout
- Kubernetes BackOff/readiness events
- 18.7% error rate
- 1850ms P95 latency
- Evidence-backed remediation steps

### Step 6 — Explain the safety model

The agent can diagnose, but it cannot perform destructive remediation. This creates a clear boundary between **AI investigation** and **human-approved operations**.

## 🧪 Test / Quality Gate

Before pushing changes:

```powershell
pytest -q
```

The current suite passes with 13 tests. The remaining Starlette/AnyIO message is a dependency deprecation warning and is not an application test failure.

## 🗺️ Roadmap

### Completed

- [x] Local LLM inference
- [x] FastAPI API
- [x] Structured output
- [x] Tool registry
- [x] Read-only diagnostic tools
- [x] Mock Kubernetes telemetry
- [x] Agentic investigation loop
- [x] Evidence sufficiency / early stopping
- [x] Runbook retrieval
- [x] Evidence-backed RCA synthesis
- [x] Automated tests

### Next — Production Integration

- [ ] Replace mock Kubernetes tools with Kubernetes API clients
- [ ] Replace mock Prometheus tools with Prometheus queries
- [ ] Add Git/CI-CD diagnostics
- [ ] Add authentication/RBAC
- [ ] Add approval workflow for any future write actions
- [ ] Add observability/tracing
- [ ] Containerize and deploy to Kubernetes

### Future — Enterprise AI DevOps

- [ ] PostgreSQL + pgvector RAG
- [ ] Hybrid retrieval and reranking
- [ ] Citations
- [ ] MCP integrations
- [ ] Agent evaluation and hallucination checks
- [ ] LLM/agent tracing
- [ ] Quality and latency dashboards
- [ ] GitOps deployment with Helm and Argo CD

## 🎯 Portfolio Story

This project demonstrates a practical progression:

**Local LLM → Structured Generation → Tool Calling → Agentic Investigation → Evidence Correlation → RAG/Runbooks → Kubernetes/Prometheus → Evaluation → Production AI**

The key engineering idea is simple: **the LLM proposes the investigation, tools provide the facts, and the final RCA is grounded in collected evidence.**

## License

MIT
