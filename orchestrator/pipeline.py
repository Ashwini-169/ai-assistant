"""Async orchestration pipeline for the assistant."""
import asyncio
import json
import logging
import time
from typing import Any, Dict, Optional, Tuple

import httpx
from pydantic import BaseModel

from core.config import get_settings
from duplex.audio_listener import AudioListener
from duplex.interrupt_controller import InterruptController
from duplex.state_machine import AssistantState, AssistantStateController
from humanization.emotion_engine import EmotionEngine
from humanization.prosody_engine import apply_prosody
from humanization.voice_style import INDIAN_NEUTRAL_FEMALE
from memory.memory_manager import MemoryManager
from orchestrator.context_engine import build_prompt
from orchestrator.gpu_lock import gpu_lock
from orchestrator.memory_buffer import ConversationBuffer
from performance.metrics_logger import log_metrics
from streaming.llm_streamer import stream_llm
from streaming.tts_streamer import stream_tts_from_tokens

logger = logging.getLogger(__name__)


def _set_state(state_controller: Optional[AssistantStateController], state: AssistantState, visual_feedback: bool) -> None:
    if state_controller is None:
        return
    state_controller.set_state(state)
    if visual_feedback:
        logger.info(state_controller.visual_label())


def _resolve_emotional_context(emotion_engine: EmotionEngine, state_obj: Any) -> str:
    if hasattr(emotion_engine, "emotional_context"):
        try:
            return str(emotion_engine.emotional_context())
        except Exception:  # pylint: disable=broad-except
            pass
    if hasattr(state_obj, "emotional_context"):
        return str(state_obj.emotional_context())
    return "User sentiment: neutral. Conversation depth: 0."


class PipelineRequest(BaseModel):
    text: str


class PipelineResult(BaseModel):
    intent: str
    assistant_text: str
    tts_status: Optional[int]
    timings_ms: Dict[str, float]
    emotional_context: Optional[str] = None
    memories_used: Optional[str] = None


async def _post_json(client: httpx.AsyncClient, url: str, payload: Dict[str, Any], timeout: float = 15.0) -> Dict[str, Any]:
    response = await client.post(url, json=payload, timeout=timeout)
    response.raise_for_status()
    return response.json()


async def _call_intent(client: httpx.AsyncClient, text: str) -> Tuple[str, float]:
    start = time.perf_counter()
    settings = get_settings()
    url = f"{settings.intent_host}:{settings.intent_port}" if settings.intent_host.startswith("http") else f"http://{settings.intent_host}:{settings.intent_port}"
    try:
        data = await _post_json(client, f"{url}/classify", {"text": text})
        intent = data.get("label", "unknown")
    except Exception as exc:  # pylint: disable=broad-except
        logger.warning("Intent service unavailable, defaulting to chat: %s", exc)
        intent = "chat"
    elapsed_ms = (time.perf_counter() - start) * 1000
    logger.info(json.dumps({"stage": "intent", "intent": intent, "intent_ms": round(elapsed_ms, 2)}))
    return intent, elapsed_ms


async def _call_llm(client: httpx.AsyncClient, prompt: str) -> Tuple[str, float]:
    start = time.perf_counter()
    settings = get_settings()
    url = f"{settings.llm_host}:{settings.llm_port}" if settings.llm_host.startswith("http") else f"http://{settings.llm_host}:{settings.llm_port}"
    data = await _post_json(client, f"{url}/generate", {"prompt": prompt})
    response_text = data.get("response", "")
    elapsed_ms = (time.perf_counter() - start) * 1000
    logger.info(json.dumps({"stage": "llm", "llm_ms": round(elapsed_ms, 2)}))
    return response_text, elapsed_ms


async def _call_tts(client: httpx.AsyncClient, text: str) -> Tuple[Optional[int], float]:
    start = time.perf_counter()
    settings = get_settings()
    url = f"{settings.tts_host}:{settings.tts_port}" if settings.tts_host.startswith("http") else f"http://{settings.tts_host}:{settings.tts_port}"
    data = await _post_json(client, f"{url}/speak", {"text": text})
    elapsed_ms = (time.perf_counter() - start) * 1000
    logger.info(json.dumps({"stage": "tts", "tts_ms": round(elapsed_ms, 2)}))
    return data.get("backend_status"), elapsed_ms


async def run_pipeline(
    text: str,
    buffer: ConversationBuffer,
    memory_manager: Optional[MemoryManager] = None,
    emotion_engine: Optional[EmotionEngine] = None,
) -> PipelineResult:
    timings: Dict[str, float] = {"whisper_ms": 0.0, "intent_ms": 0.0, "llm_ms": 0.0, "tts_ms": 0.0, "embedding_ms": 0.0, "memory_ms": 0.0}
    intent = "unknown"
    assistant_text = ""
    tts_status: Optional[int] = None
    memories_used: Optional[str] = None
    emotional_context: Optional[str] = None

    memory_manager = memory_manager or MemoryManager()
    emotion_engine = emotion_engine or EmotionEngine()

    try:
        async with httpx.AsyncClient() as client:
            intent, intent_ms = await _call_intent(client, text)
            timings["intent_ms"] = intent_ms

            if intent != "chat":
                assistant_text = f"Intent '{intent}' not supported in this phase."
                buffer.add("user", text)
                buffer.add("assistant", assistant_text)
                return PipelineResult(intent=intent, assistant_text=assistant_text, tts_status=None, timings_ms=timings)

            # Memory retrieval
            mem_start = time.perf_counter()
            memories = memory_manager.retrieve(text)
            memories_used = memory_manager.format_memories(memories)
            timings["memory_ms"] = (time.perf_counter() - mem_start) * 1000

            # Emotion state update
            state_obj = emotion_engine.update(text)
            emotional_context = _resolve_emotional_context(emotion_engine, state_obj)

            prompt = build_prompt(buffer, text, emotional_state=emotional_context, retrieved_memories=memories_used)

            async with gpu_lock():
                assistant_text, llm_ms = await _call_llm(client, prompt)
            timings["llm_ms"] = llm_ms

            prosody_text, _ = apply_prosody(assistant_text)
            tts_status, tts_ms = await _call_tts(client, prosody_text)
            timings["tts_ms"] = tts_ms

            # Store memory after response
            embed_start = time.perf_counter()
            memory_manager.add_interaction(text, assistant_text)
            timings["embedding_ms"] = (time.perf_counter() - embed_start) * 1000
    except Exception as exc:  # pylint: disable=broad-except
        logger.error("Pipeline failed: %s", exc)
        assistant_text = f"Service error: {exc}"
        return PipelineResult(intent=intent, assistant_text=assistant_text, tts_status=tts_status, timings_ms=timings, emotional_context=emotional_context, memories_used=memories_used)

    buffer.add("user", text)
    buffer.add("assistant", assistant_text)

    log_metrics({
        "whisper_ms": timings.get("whisper_ms"),
        "intent_ms": timings.get("intent_ms"),
        "llm_ms": timings.get("llm_ms"),
        "tts_ms": timings.get("tts_ms"),
        "memory_ms": timings.get("memory_ms"),
        "embedding_ms": timings.get("embedding_ms"),
    })

    return PipelineResult(
        intent=intent,
        assistant_text=assistant_text,
        tts_status=tts_status,
        timings_ms=timings,
        emotional_context=emotional_context,
        memories_used=memories_used,
    )


async def run_pipeline_streaming(
    text: str,
    buffer: "ConversationBuffer",
    interrupt_controller: Optional["InterruptController"] = None,
    state_controller: Optional["AssistantStateController"] = None,
    audio_listener: Optional["AudioListener"] = None,
    visual_feedback: bool = True,
    memory_manager: Optional[MemoryManager] = None,
    emotion_engine: Optional[EmotionEngine] = None,
) -> PipelineResult:
    """Run full pipeline: intent → memory → LLM stream → TTS stream."""
    settings = get_settings()
    timings: Dict[str, float] = {"whisper_ms": 0.0, "intent_ms": 0.0, "llm_ms": 0.0, "tts_ms": 0.0, "embedding_ms": 0.0, "memory_ms": 0.0}
    tts_status: Optional[int] = None
    memories_used: Optional[str] = None
    emotional_context: Optional[str] = None
    assistant_text = ""
    interrupted = False

    memory_manager = memory_manager or MemoryManager()
    emotion_engine = emotion_engine or EmotionEngine()

    _set_state(state_controller, AssistantState.LISTENING, visual_feedback)

    # ── Intent ───────────────────────────────────────────────────────
    async with httpx.AsyncClient() as client:
        intent, intent_ms = await _call_intent(client, text)
        timings["intent_ms"] = intent_ms

    # ── Memory retrieval ─────────────────────────────────────────────
    mem_start = time.perf_counter()
    memories = memory_manager.retrieve(text)
    memories_used = memory_manager.format_memories(memories)
    timings["memory_ms"] = (time.perf_counter() - mem_start) * 1000

    # ── Emotion ──────────────────────────────────────────────────────
    state_obj = emotion_engine.update(text)
    emotional_context = _resolve_emotional_context(emotion_engine, state_obj)

    # ── Build prompt ─────────────────────────────────────────────────
    prompt = build_prompt(buffer, text, emotional_state=emotional_context, retrieved_memories=memories_used)

    # ── LLM + TTS streaming ──────────────────────────────────────────
    _set_state(state_controller, AssistantState.THINKING, visual_feedback)

    async def token_iter():
        nonlocal assistant_text
        async for token in stream_llm(prompt):
            if interrupt_controller and interrupt_controller.is_triggered():
                break
            assistant_text += token
            yield token

    _set_state(state_controller, AssistantState.SPEAKING, visual_feedback)

    try:
        tts_result = await stream_tts_from_tokens(
            token_iter(),
            interrupt_controller=interrupt_controller,
        )
        if tts_result == "interrupted":
            interrupted = True
            _set_state(state_controller, AssistantState.INTERRUPTED, visual_feedback)
    except asyncio.CancelledError:
        interrupted = True
        _set_state(state_controller, AssistantState.INTERRUPTED, visual_feedback)
    except Exception as exc:
        logger.error("Streaming pipeline error: %s", exc)

    if interrupted:
        _set_state(state_controller, AssistantState.INTERRUPTED, visual_feedback)

    # ── Save to memory (non-fatal) ───────────────────────────────────
    if assistant_text.strip():
        try:
            embed_start = time.perf_counter()
            memory_manager.add_interaction(text, assistant_text)
            timings["embedding_ms"] = (time.perf_counter() - embed_start) * 1000
        except Exception as exc:
            logger.warning("Memory save failed (non-fatal): %s", exc)

    buffer.add("user", text)
    buffer.add("assistant", assistant_text)

    _set_state(state_controller, AssistantState.IDLE, visual_feedback)

    return PipelineResult(
        intent=intent,
        assistant_text=assistant_text,
        tts_status=tts_status,
        timings_ms=timings,
        emotional_context=emotional_context,
        memories_used=memories_used,
    )
