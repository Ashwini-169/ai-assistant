"""Lightweight resource monitor for GPU and CPU on Windows."""
import subprocess
import time

import psutil


def print_gpu_usage() -> None:
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=timestamp,name,utilization.gpu,memory.used,memory.total", "--format=csv"],
            capture_output=True,
            text=True,
            check=False,
        )
        print(result.stdout.strip() or "nvidia-smi produced no output")
    except FileNotFoundError:
        print("nvidia-smi not found; skipping GPU stats")


def print_cpu_ram_usage() -> None:
    cpu_percent = psutil.cpu_percent(interval=None)
    virtual_mem = psutil.virtual_memory()
    print(
        f"CPU: {cpu_percent:.1f}% | RAM used: {virtual_mem.used // (1024 * 1024)} MB / "
        f"{virtual_mem.total // (1024 * 1024)} MB"
    )


def main() -> None:
    while True:
        print_gpu_usage()
        print_cpu_ram_usage()
        time.sleep(5)


if __name__ == "__main__":
    main()
