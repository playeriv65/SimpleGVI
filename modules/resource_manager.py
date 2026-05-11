"""系统资源信息输出。"""

import os
from typing import Tuple

import psutil


class ResourceMonitor:
    """Collect CPU, memory, and optional PyTorch GPU resource information."""

    def __init__(self):
        self._gpu_available = False
        self._cpu_total_mb = 0
        self._detect_hardware()

    def _detect_hardware(self):
        try:
            import torch

            self._gpu_available = torch.cuda.is_available()
        except ImportError:
            self._gpu_available = False

        self._cpu_total_mb, _ = self._get_memory_info()

    def _get_memory_info(self) -> Tuple[int, int]:
        memory = psutil.virtual_memory()
        return memory.total // (1024 * 1024), memory.available // (1024 * 1024)

    def get_memory_usage(self) -> float:
        total, available = self._get_memory_info()
        used = total - available
        return used / total if total > 0 else 0.0

    def get_resource_summary(self) -> str:
        total, available = self._get_memory_info()
        memory_usage = self.get_memory_usage()

        lines = [
            "=== 系统资源 ===",
            f"CPU: {os.cpu_count()} 核心",
            f"内存: {total}MB 总量, {available}MB 可用, 使用率 {memory_usage:.1%}",
        ]

        if self._gpu_available:
            import torch

            free_bytes, total_bytes = torch.cuda.mem_get_info(0)
            gpu_total = total_bytes // (1024 * 1024)
            gpu_available = free_bytes // (1024 * 1024)
            gpu_used = gpu_total - gpu_available
            gpu_usage = gpu_used / gpu_total if gpu_total else 0.0
            lines.append(f"GPU: {torch.cuda.get_device_name(0)}")
            lines.append(
                f"显存: {gpu_total}MB 总量, {gpu_available}MB 可用, "
                f"{gpu_used}MB 使用, 使用率 {gpu_usage:.1%}"
            )

        return "\n".join(lines)


def print_resource_info():
    """打印系统资源信息。"""
    monitor = ResourceMonitor()
    print(monitor.get_resource_summary())
