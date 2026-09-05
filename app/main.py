import logging
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .core.config import APP_NAME, APP_VERSION, LOG_LEVEL, MODEL_PATH
from .core.logging import configure_logging
from .llm import analyze_incident
from .schemas.incident import IncidentAnalysis, IncidentRequest

configure_logging(LOG_LEVEL)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description="Local AI DevOps Assistant powered by Qwen3.5-2B GGUF and llama.cpp.",
)


@app.middleware("http")
async def request_context(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    start = time.perf_counter()

    try:
        response = await call_next(request)
    except Exception:
        logger.exception("Unhandled request error | request_id=%s", request_id)
        response = JSONResponse(
            status_code=500,
            content={"detail": "Internal server error", "request_id": request_id},
        )

    elapsed_ms = (time.perf_counter() - start) * 1000
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Processing-Time-Ms"] = f"{elapsed_ms:.2f}"
    logger.info(
        "%s %s -> %s | %.2f ms | request_id=%s",
        request.method,
        request.url.path,
        response.status_code,
        elapsed_ms,
        request_id,
    )
    return response


@app.get("/health")
def health():
    return {
        "status": "ok",
        "model": "qwen3.5-2b",
        "inference": "llama.cpp",
        "device": "cpu",
        "model_path": MODEL_PATH,
    }


@app.get("/ready")
def ready():
    return {"status": "ready", "model_loaded": True}


@app.post("/api/v1/analyze", response_model=IncidentAnalysis)
def analyze(request: IncidentRequest):
    return analyze_incident(
        service=request.service,
        environment=request.environment,
        logs=request.logs,
        description=request.description,
    )
