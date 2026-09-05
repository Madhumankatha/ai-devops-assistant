import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parents[2]

APP_NAME = os.getenv("APP_NAME", "AI DevOps Assistant")
APP_VERSION = os.getenv("APP_VERSION", "0.2.0")
MODEL_PATH = os.getenv(
    "MODEL_PATH",
    str(BASE_DIR / "models" / "qwen3.5-2b-ud-q4_k_xl.gguf"),
)
N_CTX = int(os.getenv("N_CTX", "4096"))
N_THREADS = int(os.getenv("N_THREADS", str(os.cpu_count() or 4)))
N_BATCH = int(os.getenv("N_BATCH", "256"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
