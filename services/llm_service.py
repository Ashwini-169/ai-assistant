"""LLM service that proxies requests to a local Ollama instance."""
import logging
from typing import Any, Dict

import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from core.config import get_settings

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="LLM Service", version="0.1.0")

OLLAMA_MODEL = "qwen2.5-coder:7b"
KEEP_ALIVE = "24h"

_http_session = requests.Session()


class GenerateRequest(BaseModel):
    prompt: str


class GenerateResponse(BaseModel):
    model: str
    response: str


def _ollama_ready() -> bool:
    settings = get_settings()
    try:
        response = _http_session.get(f"{str(settings.ollama_api_url).rstrip('/')}/api/tags", timeout=5)
        return response.status_code == 200
    except Exception:  # pylint: disable=broad-except
        return False


def _post_generate(payload: Dict[str, Any]) -> Dict[str, Any]:
    settings = get_settings()
    try:
        response = _http_session.post(
            f"{str(settings.ollama_api_url).rstrip('/')}/api/generate",
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
        return response.json()
    except Exception as exc:  # pylint: disable=broad-except
        logger.error("Ollama request failed: %s", exc)
        raise HTTPException(status_code=502, detail="LLM backend unavailable") from exc


@app.on_event("startup")
async def warmup_model() -> None:
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": "warmup",
        "keep_alive": KEEP_ALIVE,
        "stream": False,
    }
    try:
        _post_generate(payload)
        logger.info("Warmed up Ollama model '%s'", OLLAMA_MODEL)
    except HTTPException:
        logger.warning("Warmup failed for model '%s'", OLLAMA_MODEL, exc_info=True)


@app.post("/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest) -> GenerateResponse:
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": request.prompt,
        "keep_alive": KEEP_ALIVE,
        "stream": False,
    }
    data = _post_generate(payload)
    text = data.get("response", "")
    return GenerateResponse(model=OLLAMA_MODEL, response=text)


@app.get("/health")
async def health():
    backend_ready = _ollama_ready()
    if backend_ready:
        return {"status": "ok", "service": "llm", "model": OLLAMA_MODEL, "backend_ready": True}
    raise HTTPException(status_code=503, detail="LLM backend unavailable")


if __name__ == "__main__":
    from uvicorn import run

    settings = get_settings()
    run(app, host=settings.llm_host, port=settings.llm_port, log_level=settings.log_level.lower())
