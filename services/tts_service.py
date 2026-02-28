"""Text-to-speech proxy service for Piper running on CPU."""
import logging
from typing import Any, Dict

import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from core.config import get_settings

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="TTS Service", version="0.1.0")

_http_session = requests.Session()


class SpeakRequest(BaseModel):
    text: str


class SpeakResponse(BaseModel):
    accepted: bool
    backend_status: int


def _post_tts(payload: Dict[str, Any]) -> requests.Response:
    settings = get_settings()
    try:
        response = _http_session.post(
            f"{settings.piper_api_url}/synthesize",
            json=payload,
            timeout=15,
        )
        response.raise_for_status()
        return response
    except Exception as exc:  # pylint: disable=broad-except
        logger.error("Piper request failed: %s", exc)
        raise HTTPException(status_code=502, detail="TTS backend unavailable") from exc


@app.post("/speak", response_model=SpeakResponse)
async def speak(request: SpeakRequest) -> SpeakResponse:
    response = _post_tts({"text": request.text})
    return SpeakResponse(accepted=True, backend_status=response.status_code)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "tts"}


if __name__ == "__main__":
    from uvicorn import run

    settings = get_settings()
    run(app, host=settings.tts_host, port=settings.tts_port, log_level=settings.log_level.lower())
