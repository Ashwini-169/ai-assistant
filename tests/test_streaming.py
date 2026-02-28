import asyncio

import pytest

from duplex.interrupt_controller import InterruptController
from streaming.tts_streamer import _chunk_text, stream_tts


@pytest.mark.anyio
async def test_chunking_and_stream(monkeypatch):
    calls = []

    async def fake_post(text: str, client):  # pylint: disable=unused-argument
        calls.append(text)

    monkeypatch.setattr("streaming.tts_streamer._send_tts", fake_post)

    await stream_tts("Hello world this is streaming test", interrupt_flag=None)
    # Should have produced at least one call
    assert calls


def test_chunk_helper():
    chunks = _chunk_text("a" * 250, size=120)
    assert len(chunks) == 3


@pytest.mark.anyio
async def test_stream_interrupt_controller(monkeypatch):
    calls = []
    interrupt_controller = InterruptController()

    async def fake_post(text: str, client):  # pylint: disable=unused-argument
        calls.append(text)

    monkeypatch.setattr("streaming.tts_streamer._send_tts", fake_post)

    interrupt_controller.trigger()
    status = await stream_tts("Hello interruption", interrupt_controller=interrupt_controller)

    assert status == "interrupted"
    assert calls == []
