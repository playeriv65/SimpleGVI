"""
资源管理器模块

实时监测系统资源，动态控制任务提交。
不预估单任务消耗，而是根据实际内存使用情况决定是否添加新任务。
"""

import os
import time
import logging
from dataclasses import dataclass
from typing import Tuple

import psutil

logger = logging.getLogger(__name__)


@dataclass
class ResourceConfig:
    """资源配置"""
    max_memory_usage: float = 0.85  # 最大内存使用率（超过此值暂停提交任务）
    check_interval: float = 1.0  # 检查间隔（秒）
    max_workers: int = 16  # 最大并行数上限


class ResourceMonitor:
    """
    资源监测器
    
    实时监测系统资源，动态决定是否可以添加新任务。
    """
    
    def __init__(self, config: ResourceConfig = None):
        self.config = config or ResourceConfig()
        self._gpu_available = False
        self._gpu_total_mb = 0
        self._cpu_total_mb = 0
        self._detect_hardware()
    
    def _detect_hardware(self):
        """检测硬件信息"""
        try:
            import torch
            if torch.cuda.is_available():
                self._gpu_available = True
                props = torch.cuda.get_device_properties(0)
                self._gpu_total_mb = props.total_memory // (1024 * 1024)
                logger.info(f"GPU: {torch.cuda.get_device_name(0)}, 显存: {self._gpu_total_mb}MB")
        except ImportError:
            pass
        
        self._cpu_total_mb, _ = self._get_memory_info()
        logger.info(f"CPU: {os.cpu_count()} 核心, 内存: {self._cpu_total_mb}MB")
    
    def _get_memory_info(self) -> Tuple[int, int]:
        """获取内存信息（总量MB，可用MB）"""
        memory = psutil.virtual_memory()
        return memory.total // (1024 * 1024), memory.available // (1024 * 1024)

    def get_memory_usage(self) -> float:
        """获取当前内存使用率 (0.0-1.0)"""
        total, available = self._get_memory_info()
        used = total - available
        return used / total if total > 0 else 0.0
    
    def get_gpu_usage(self) -> float:
        """获取当前GPU显存使用率 (0.0-1.0)"""
        if not self._gpu_available:
            return 0.0
        
        try:
            import torch
            free_bytes, total_bytes = torch.cuda.mem_get_info(0)
            used_bytes = total_bytes - free_bytes
            return used_bytes / total_bytes if total_bytes > 0 else 0.0
        except Exception:
            return 0.0
    
    def can_submit_task(self) -> bool:
        """检查是否可以提交新任务"""
        memory_usage = self.get_memory_usage()
        if memory_usage >= self.config.max_memory_usage:
            return False
        
        if self._gpu_available:
            gpu_usage = self.get_gpu_usage()
            if gpu_usage >= self.config.max_memory_usage:
                return False
        
        return True
    
    def wait_for_resources(self, timeout: float = 300.0) -> bool:
        """
        等待资源可用
        
        Returns:
            True表示资源已可用，False表示超时
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if self.can_submit_task():
                return True
            
            memory_usage = self.get_memory_usage()
            logger.debug(f"等待资源... 内存使用率: {memory_usage:.1%}")
            time.sleep(self.config.check_interval)
        
        return False
    
    def get_resource_summary(self) -> str:
        """获取资源摘要"""
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
            gpu_usage = self.get_gpu_usage()
            lines.append(f"GPU: {torch.cuda.get_device_name(0)}")
            lines.append(
                f"显存: {gpu_total}MB 总量, {gpu_available}MB 可用, {gpu_used}MB 使用, 使用率 {gpu_usage:.1%}"
            )
        
        lines.append(f"\n配置: 最大内存使用率 {self.config.max_memory_usage:.0%}")
        
        return "\n".join(lines)


_monitor: ResourceMonitor = None


def get_resource_monitor(config: ResourceConfig = None) -> ResourceMonitor:
    """获取全局资源监测器"""
    global _monitor
    if _monitor is None or (config is not None and _monitor.config != config):
        _monitor = ResourceMonitor(config)
    return _monitor


def print_resource_info():
    """打印系统资源信息"""
    monitor = get_resource_monitor()
    print(monitor.get_resource_summary())
