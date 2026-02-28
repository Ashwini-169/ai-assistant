"""Chunked TTS streaming orchestrator."""
import asyncio
from typing import AsyncIterator, Iterable, List

import httpx

from core.config import get_settings
from duplex.interrupt_controller import InterruptController

CHUNK_SIZE = 120


async def _send_tts(text: str, client: httpx.AsyncClient) -> None:
    settings = get_settings()
    url = f"{settings.tts_host}:{settings.tts_port}" if settings.tts_host.startswith("http") else f"http://{settings.tts_host}:{settings.tts_port}"
    await client.post(f"{url}/speak", json={"text": text})


def _chunk_text(text: str, size: int = CHUNK_SIZE) -> List[str]:
    return [text[i : i + size] for i in range(0, len(text), size)]


def _is_interrupted(interrupt_flag: asyncio.Event | None, interrupt_controller: InterruptController | None) -> bool:
    if interrupt_flag and interrupt_flag.is_set():
        return True
    if interrupt_controller and interrupt_controller.is_triggered():
        return True
    return False


async def stream_tts(
    text: str,
    interrupt_flag: asyncio.Event | None = None,
    interrupt_controller: InterruptController | None = None,
) -> str:
    chunks = _chunk_text(text)
    async with httpx.AsyncClient() as client:
        for chunk in chunks:
            if _is_interrupted(interrupt_flag, interrupt_controller):
                return "interrupted"
            await _send_tts(chunk, client)
            await asyncio.sleep(0)  # yield control
    return "completed"


async def stream_tts_from_tokens(
    token_iter: Iterable[str],
    interrupt_flag: asyncio.Event | None = None,
    interrupt_controller: InterruptController | None = None,
) -> str:
    buffer = ""
    async with httpx.AsyncClient() as client:
        async for token in token_iter:  # type: ignore
            if _is_interrupted(interrupt_flag, interrupt_controller):
                return "interrupted"
            buffer += token
            if len(buffer) >= CHUNK_SIZE:
                await _send_tts(buffer, client)
                buffer = ""
                await asyncio.sleep(0)
        if buffer and not _is_interrupted(interrupt_flag, interrupt_controller):
            await _send_tts(buffer, client)
    return "completed"
