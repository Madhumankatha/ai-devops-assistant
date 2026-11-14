# 🤖 AI DevOps Assistant

> A completed, privacy-first Agentic AI DevOps investigation MVP powered by a local **Qwen GGUF** model and **llama.cpp**.

This project demonstrates an end-to-end incident investigation workflow using a local LLM, a controlled agent loop, read-only diagnostic tools, mock Kubernetes and Prometheus data, evidence correlation, local runbook retrieval, and structured root-cause analysis (RCA).

## 🎉 Project Status

<badge color="success">MVP Completed</badge>

**The defined AI DevOps Assistant MVP is complete.** The implemented scope is documented below and validated by the automated test suite (**13 tests passing**).

Completed capabilities:

- Local Qwen GGUF inference through llama.cpp (CPU)
- FastAPI REST API and Pydantic request/response validation
- Controlled agentic investigation loop
- Allow-listed tool registry with seven read-only diagnostic tools
- Mock Kubernetes pod, deployment, log, and event diagnostics
- Mock Prometheus service metrics, error rate, and latency
- Evidence accumulation, normalization, and sufficiency-based early stopping
- Local runbook retrieval and RCA guidance
- Evidence-grounded RCA synthesis
- Health/readiness endpoints, request IDs, timing headers, and logging
- Automated tests

> **Scope note:** Kubernetes and Prometheus integrations use mock/demo data. The completed project is a local, demonstrable MVP; it does not claim to connect to or operate a live Kubernetes cluster or Prometheus server.

## 🧠 What the Agent Does

Given a service, namespace, and incident question, the agent follows a controlled investigation flow:

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

The agent is restricted to diagnostic operations. It does **not** restart, delete, scale, modify, or otherwise mutate Kubernetes resources.

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
  "summary": "The payment-service is experiencing critical failures with high error rate, high latency, and a crashing pod associated with database connection failure.",
  "root_cause": "The payment-service pod cannot establish a database connection during startup, causing application startup failure and CrashLoopBackOff.",
  "evidence": [
    "[get_service_metrics] CPU utilization is 87.5% and memory utilization is 91.2%.",
    "[get_pod_status] The payment-service pod is in CrashLoopBackOff with 12 restarts.",
    "[get_pod_logs] Logs contain database connection timeout and failed-to-connect errors.",
    "[get_kubernetes_events] Events show BackOff restarting failed container and readiness probe failure.",
    "[get_error_rate] Error rate is 18.7%.",
    "[get_latency] P95 latency is 1850ms."
  ],
  "recommended_actions": [
    "Verify database availability and connectivity.",
    "Validate database connection configuration and credentials.",
    "Check network connectivity between the service and database."
  ],
  "confidence": 0.95
}
```

*The values above are illustrative mock incident data used for the project demo.*

## 🛠️ Diagnostic Tools

| Tool | Purpose |
|---|---|
| `get_pod_status` | Inspect pod health and restart state |
| `get_pod_logs` | Inspect recent application logs |
| `get_kubernetes_events` | Inspect Kubernetes events |
| `get_deployment_status` | Inspect deployment readiness |
| `get_service_metrics` | CPU, memory, request rate, error rate, and latency |
| `get_error_rate` | Service error rate |
| `get_latency` | Service P95 latency |

All tools are registered through a central `ToolRegistry`, providing an explicit allow-list for agent execution.

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

Place your Qwen GGUF model under:

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

### 4. Run the application

```powershell
uvicorn app.main:app --reload
```

Swagger UI: `http://127.0.0.1:8000/docs`

### 5. Run tests

```powershell
pytest -q
```

**Verified test baseline:** 13 passed. A dependency deprecation warning from Starlette/AnyIO may be displayed; it does not indicate a failing test.

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


## 🎯 Portfolio Story

This project demonstrates a practical progression:

**Local LLM → Structured Generation → Tool Calling → Agentic Investigation → Evidence Correlation → RAG/Runbooks → Kubernetes/Prometheus → Evaluation → Production AI**

The key engineering idea is simple: **the LLM proposes the investigation, tools provide the facts, and the final RCA is grounded in collected evidence.**

## License

MIT
