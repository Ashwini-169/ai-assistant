import json
import logging
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def _get_gpu_memory(torch_module: Any) -> Optional[Dict[str, int]]:
    try:
        free_bytes, total_bytes = torch_module.cuda.mem_get_info()
        return {
            "free_mb": int(free_bytes / (1024 * 1024)),
            "total_mb": int(total_bytes / (1024 * 1024)),
        }
    except Exception:  # pragma: no cover - best-effort metric
        return None


def _detect_cuda() -> Dict[str, Any]:
    try:
        import torch
    except ImportError:
        logger.warning("torch not installed; skipping CUDA detection")
        return {"available": False, "reason": "torch_not_installed"}

    if not torch.cuda.is_available():
        return {"available": False, "reason": "cuda_not_available"}

    try:
        device_index = torch.cuda.current_device()
        device_name = torch.cuda.get_device_name(device_index)
        props = torch.cuda.get_device_properties(device_index)
        memory = _get_gpu_memory(torch)
        return {
            "available": True,
            "device_index": device_index,
            "device_name": device_name,
            "total_memory_mb": int(props.total_memory / (1024 * 1024)),
            "memory_status": memory,
        }
    except Exception as exc:  # pylint: disable=broad-except
        logger.exception("Failed to query CUDA details: %s", exc)
        return {"available": False, "reason": "cuda_query_failed", "error": str(exc)}


def _detect_npu_providers() -> Dict[str, Any]:
    try:
        import onnxruntime as ort
    except ImportError:
        logger.warning("onnxruntime not installed; skipping NPU provider detection")
        return {
            "available": False,
            "providers": [],
            "reason": "onnxruntime_not_installed",
        }

    providers: List[str] = list(ort.get_available_providers())
    directml_present = any(provider.lower().startswith("dml") for provider in providers)
    preferred = "DmlExecutionProvider" if directml_present else "CPUExecutionProvider"
    return {
        "available": directml_present,
        "providers": providers,
        "preferred": preferred,
    }


def detect_devices() -> Dict[str, Any]:
    cuda_info = _detect_cuda()
    npu_info = _detect_npu_providers()
    cpu_cores = os.cpu_count() or 1

    result: Dict[str, Any] = {
        "cpu": {"cores": cpu_cores},
        "cuda": cuda_info,
        "npu": npu_info,
    }

    logger.info("Device detection result: %s", json.dumps(result))
    return result


def get_device_report() -> str:
    return json.dumps(detect_devices(), indent=2)
