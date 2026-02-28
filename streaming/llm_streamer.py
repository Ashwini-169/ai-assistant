"""Streaming LLM client against Ollama with GPU serialization."""
import asyncio
import json
import logging
import time
from typing import AsyncIterator, Optional

import httpx

from core.config import get_settings
from orchestrator.gpu_lock import gpu_lock

MODEL_NAME = "qwen2.5-coder:7b"
logger = logging.getLogger(__name__)


async def stream_llm(prompt: str) -> AsyncIterator[str]:
    settings = get_settings()
    url = f"{str(settings.ollama_api_url).rstrip('/')}/api/generate"
    first_token_latency_ms: Optional[float] = None
    start = time.perf_counter()

    async with gpu_lock():
        async with httpx.AsyncClient(timeout=None) as client:
            try:
                async with client.stream(
                    "POST",
                    url,
                    json={"model": MODEL_NAME, "prompt": prompt, "stream": True, "keep_alive": "24h"},
                ) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        try:
                            data = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        token = data.get("response", "")
                        if token:
                            if first_token_latency_ms is None:
                                first_token_latency_ms = (time.perf_counter() - start) * 1000
                            yield token
                        if data.get("done", False):
                            break
            except GeneratorExit:
                logger.debug("LLM stream cancelled by caller")
                return
            except Exception as exc:
                logger.error("LLM stream error: %s", exc)
                raise

    if first_token_latency_ms is not None:
        logger.info(json.dumps({"stage": "llm_stream", "first_token_ms": round(first_token_latency_ms, 2)}))
