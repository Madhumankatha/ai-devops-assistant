

Frontend
────────
React / Next.js

Backend
───────
Python + FastAPI
or
Java + Spring Boot

AI
──
OpenAI / Anthropic / open-source LLMs

Agent
─────
LangGraph

RAG
───
PostgreSQL + pgvector
Qdrant

Retrieval
─────────
BM25 + Vector Search
+ Reranker

MCP
───
MCP Servers

DevOps
──────
Kubernetes
Helm
Argo CD
Jenkins
Prometheus
Grafana

Security
────────
Vault
RBAC
Istio/mTLS
OPA

Observability
─────────────
OpenTelemetry
Prometheus
Grafana

Evaluation
──────────
RAG/Agent evaluation framework
+ custom evaluation datasets

Portfolio projects

We’ll build these progressively:

LLM Engineering Lab — prompts, structured outputs, function calling
Enterprise RAG Platform ⭐ — production-grade RAG
Agentic Knowledge Assistant — LangGraph + tools + memory
AI DevOps Assistant ⭐⭐⭐ — Kubernetes + Prometheus + Helm + Git + MCP
AI Evaluation & Observability Platform
FDE Production Case Study — turn one project into a customer-ready solution

Project: llm-engineering-lab

llm-engineering-lab/
├── README.md
├── src/
│   ├── prompting/
│   ├── structured_output/
│   ├── function_calling/
│   ├── streaming/
│   └── model_routing/
├── tests/
├── examples/
├── requirements.txt
└── .env.example


Hands-on tasks

Build:

Prompt templates
Zero-shot prompts
Few-shot prompts
Structured JSON output
Function calling
Streaming responses
Retry/fallback
Token/cost tracking
Model routing
Final mini-project

Build:

1 AI Incident Summarizer

Input:

Kubernetes logs
+
deployment information
+
incident description

Output:

{
  "summary": "...",
  "severity": "HIGH",
  "probable_cause": "...",
  "evidence": [],
  "recommended_actions": [],
  "confidence": 0.91
}


                         ┌──────────────────┐
                         │   React / UI     │
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │     FastAPI      │
                         └────────┬─────────┘
                                  │
                                  ▼
                    ┌─────────────────────────┐
                    │     AI Orchestrator     │
                    └────────────┬────────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              │                  │                  │
              ▼                  ▼                  ▼
        Prompt Engine        RAG Engine        Agent Engine
              │                  │                  │
              │                  ▼                  ▼
              │             pgvector/Qdrant     Tools/MCP
              │                  │                  │
              └──────────────────┼──────────────────┘
                                 ▼
                         ┌──────────────────┐
                         │ Qwen3.5-2B GGUF  │
                         │   UD-Q4_K_XL     │
                         └────────┬─────────┘
                                  │
                                  ▼
                         Structured Response

Recommended local stack

| Layer                 | Technology                           |
| --------------------- | ------------------------------------ |
| LLM                   | **Qwen3.5-2B-GGUF UD-Q4_K_XL**       |
| Inference             | **llama.cpp / llama-cpp-python**     |
| API                   | FastAPI                              |
| RAG                   | LlamaIndex or custom Python          |
| Vector DB             | PostgreSQL + pgvector                |
| Alternative Vector DB | Qdrant                               |
| Embeddings            | Dedicated embedding model            |
| Reranker              | Dedicated reranker model             |
| Agents                | LangGraph                            |
| MCP                   | MCP Python SDK                       |
| Database              | PostgreSQL                           |
| Cache                 | Redis                                |
| Observability         | OpenTelemetry + Prometheus + Grafana |
| Container             | Docker                               |
| Deployment            | Kubernetes                           |
| GitOps                | Argo CD                              |


2 RAG Fundamentals

enterprise-rag-platform

Documents
   ↓
Loader
   ↓
Chunker
   ↓
Embeddings
   ↓
pgvector
   ↓
Retriever
   ↓
LLM
   ↓
Answer

Support:

PDF
Markdown
TXT
DOCX
HTML

Build a CLI first:

python -m app ingest ./documents
python -m app query "What is the deployment process?"

Then build an API.

POST /documents
POST /query
GET  /documents
DELETE /documents/{id}

3 Advanced RAG

Now make your RAG system actually production-grade.

Implement:

Retrieval

User Query
    ↓
Query preprocessing
    ↓
 ┌───────────────┐
 │ Vector Search │
 └───────┬───────┘
         +
 ┌───────────────┐
 │  BM25 Search  │
 └───────┬───────┘
         ↓
   Hybrid Ranking
         ↓
      Reranker
         ↓
   Context Builder
         ↓
        LLM

Learn and implement:

Hybrid search
Metadata filtering
Reranking
Query rewriting
Parent/child chunks
Context compression
Citation generation

Important

Your answer should show:

Answer

The deployment requires approval from the platform team...

Sources:
[1] deployment-process.md
[2] platform-handbook.pdf
[3] production-runbook.md


Enterprise RAG

                 API Gateway
                      │
                      ↓
               Authentication
                      │
                      ↓
                    RBAC
                      │
                      ↓
               RAG Orchestrator
                      │
          ┌───────────┼───────────┐
          ↓           ↓           ↓
       Vector       BM25       Metadata
          │           │           │
          └───────────┼───────────┘
                      ↓
                   Reranker
                      ↓
                     LLM
                      ↓
             Answer + Citations


Add:

JWT authentication
RBAC
User/tenant isolation
Document permissions
Audit logs
Rate limiting
API versioning
Docker
PostgreSQL
pgvector
Qdrant comparison

GitHub README should contain
Architecture
Installation
Configuration
API documentation
Database schema
RAG pipeline
Security model
Evaluation
Performance
Screenshots
Demo video
Future improvements


5 — Agentic AI

Project

agentic-knowledge-assistant

Use LangGraph.

Architecture

                   User
                    │
                    ↓
                  Agent
                    │
              ┌─────┴─────┐
              ↓           ↓
           Retriever     Tools
              │           │
              ↓           ↓
             RAG       External APIs
              │           │
              └─────┬─────┘
                    ↓
                  Agent
                    ↓
              Final Answer


Build tools such as:

search_documents()
get_document()
search_web()
calculate()
get_system_status()

Then add:

State
Memory
Tool calling
Conditional routing
Human approval
Checkpoints
Error handling


6 — ⭐ AI DevOps Assistant

Repository:

ai-devops-assistant/

Architecture

                         User
                           │
                           ↓
                    AI DevOps Agent
                           │
                       LangGraph
                           │
          ┌────────────────┼────────────────┐
          ↓                ↓                ↓
     Kubernetes          Git            Prometheus
        Tool             Tool              Tool
          │                │                │
          ↓                ↓                ↓
       Cluster           Repo            Metrics
          │                │                │
          └────────────────┼────────────────┘
                           ↓
                     RCA Engine
                           ↓
                    Fix Plan Generator
                           ↓
                    Human Approval
                           ↓
                    Remediation Tool

Example

User:

Why is payment-service failing?

Agent:

1. Check deployment
2. Check pods
3. Inspect logs
4. Check Kubernetes events
5. Inspect Helm values
6. Check Prometheus metrics
7. Inspect recent Git changes
8. Correlate evidence
9. Determine root cause
10. Generate remediation plan

Output:

╔══════════════════════════════════════╗
║ INCIDENT RCA                         ║
╚══════════════════════════════════════╝

Service:
payment-service

Severity:
HIGH

Root Cause:
Invalid database endpoint.

Evidence:
✓ Pod logs
✓ Kubernetes events
✓ Deployment configuration
✓ Prometheus metrics
✓ Git commit

Recommended Fix:

1. Update DB_HOST
2. Deploy configuration
3. Restart affected pods

Confidence:
94%

Risk:
MEDIUM

[ APPROVE REMEDIATION ]

7 — Evaluation + Observability

Implement:

                 AI Application
                       │
          ┌────────────┼────────────┐
          ↓            ↓            ↓
       Tracing       Metrics       Logs
          │            │            │
          └────────────┼────────────┘
                       ↓
                 Observability
                       │
          ┌────────────┼────────────┐
          ↓            ↓            ↓
       Quality        Cost        Latency
          ↓            ↓            ↓
                 Evaluation

Track:

LLM latency
Token usage
Cost
Retrieval latency
Retrieval quality
Answer quality
Hallucination
Tool failures
Agent success rate

Create an evaluation dataset:

{
  "question": "Why is pod X crashing?",
  "expected_root_cause": "OOMKilled",
  "expected_tool": "kubernetes_logs",
  "expected_evidence": ["pod events", "container logs"]
}


8 — FDE

Now we package everything as if you're delivering it to a real customer.

Create:

fde-case-study/
├── problem.md
├── customer-workflow.md
├── requirements.md
├── architecture.md
├── security.md
├── deployment.md
├── success-metrics.md
├── pilot-plan.md
├── production-plan.md
└── roi.md


Example:

Customer problem

DevOps engineers spend 30–45 minutes diagnosing Kubernetes incidents.

Proposed solution

AI DevOps Assistant automatically correlates Kubernetes logs, events, Helm configuration, Git changes and Prometheus metrics.

Success metrics
MTTR
45 min → 15 min

Investigation time
30 min → 5 min

Automated RCA
65% → 90%

Human approval
Required for risky actions

That's FDE thinking.

Portfolio


├── llm-engineering-lab
│
├── enterprise-rag-platform
│
├── agentic-knowledge-assistant
│
├── ai-devops-assistant
│
├── ai-evaluation-platform
│
└── fde-ai-devops-case-study

AI ENGINEER / GENAI / FDE
──────────────────────────

Building production AI systems at the intersection
of LLMs, RAG, Agents and Cloud/DevOps.

⭐ Enterprise RAG Platform
⭐ AI DevOps Assistant
⭐ Agentic AI + MCP
⭐ AI Evaluation & Observability

Tech:
Python • FastAPI • LangGraph • MCP
PostgreSQL • pgvector • Qdrant
Kubernetes • Helm • Argo CD
Prometheus • Grafana • Docker

1: Local Qwen + llama.cpp + structured generation
2: Embeddings + pgvector + basic RAG
3: Hybrid retrieval + reranking + citations
4: Enterprise RAG + RBAC + multi-tenancy
5: LangGraph agents + tools + memory
6: Kubernetes + Prometheus + Git + MCP → AI DevOps Assistant
7: Evaluation + tracing + metrics + safety
8: Docker + Kubernetes + GitOps + FDE case study