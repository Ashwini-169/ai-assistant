"""Global async GPU lock to serialize GPU-bound work."""
import asyncio
from contextlib import asynccontextmanager
from typing import AsyncIterator


_gpu_lock = asyncio.Lock()


async def acquire_gpu() -> None:
    await _gpu_lock.acquire()


def release_gpu() -> None:
    if _gpu_lock.locked():
        _gpu_lock.release()


@asynccontextmanager
async def gpu_lock() -> AsyncIterator[None]:
    await acquire_gpu()
    try:
        yield
    finally:
        release_gpu()
