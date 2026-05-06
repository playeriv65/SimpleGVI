"""
资源管理器模块

检测系统资源（GPU显存、CPU内存），自动计算最优并行数。
类似vLLM的显存使用比率机制。
"""

import os
import logging
from dataclasses import dataclass
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class SystemResources:
    """系统资源信息"""
    # GPU资源
    gpu_available: bool = False
    gpu_name: str = ""
    gpu_total_memory_mb: int = 0
    gpu_used_memory_mb: int = 0
    gpu_free_memory_mb: int = 0
    
    # CPU资源
    cpu_count: int = 0
    cpu_total_memory_mb: int = 0
    cpu_available_memory_mb: int = 0
    
    # 估算的单任务消耗
    estimated_gpu_per_task_mb: int = 0
    estimated_cpu_per_task_mb: int = 0


@dataclass
class ResourceConfig:
    """资源配置"""
    gpu_memory_ratio: float = 0.8  # GPU显存使用比率（类似vLLM）
    cpu_memory_ratio: float = 0.7  # CPU内存使用比率
    min_workers: int = 1  # 最小并行数
    max_workers: int = 16  # 最大并行数上限
    reserve_memory_mb: int = 1024  # 预留内存（MB）


class ResourceManager:
    """
    资源管理器
    
    检测系统资源，自动计算最优并行数。
    """
    
    def __init__(self, config: Optional[ResourceConfig] = None):
        """
        初始化资源管理器
        
        Args:
            config: 资源配置，None使用默认配置
        """
        self.config = config or ResourceConfig()
        self._resources: Optional[SystemResources] = None
    
    def detect_resources(self) -> SystemResources:
        """
        检测系统资源
        
        Returns:
            SystemResources: 系统资源信息
        """
        resources = SystemResources()
        
        # 检测GPU资源
        self._detect_gpu(resources)
        
        # 检测CPU资源
        self._detect_cpu(resources)
        
        # 估算单任务消耗
        self._estimate_task_consumption(resources)
        
        self._resources = resources
        return resources
    
    def _detect_gpu(self, resources: SystemResources):
        """检测GPU资源"""
        try:
            import torch
            
            if torch.cuda.is_available():
                resources.gpu_available = True
                resources.gpu_name = torch.cuda.get_device_name(0)
                
                # 获取GPU显存信息
                gpu_props = torch.cuda.get_device_properties(0)
                resources.gpu_total_memory_mb = gpu_props.total_mem // (1024 * 1024)
                
                # 当前使用情况
                resources.gpu_used_memory_mb = torch.cuda.memory_allocated(0) // (1024 * 1024)
                resources.gpu_free_memory_mb = resources.gpu_total_memory_mb - resources.gpu_used_memory_mb
                
                logger.info(f"GPU: {resources.gpu_name}")
                logger.info(f"GPU显存: {resources.gpu_total_memory_mb}MB 总量, {resources.gpu_free_memory_mb}MB 可用")
            else:
                logger.info("GPU: 不可用，使用CPU模式")
                
        except ImportError:
            logger.info("PyTorch未安装，跳过GPU检测")
    
    def _detect_cpu(self, resources: SystemResources):
        """检测CPU资源"""
        resources.cpu_count = os.cpu_count() or 1
        
        # 尝试使用psutil
        try:
            import psutil
            memory = psutil.virtual_memory()
            resources.cpu_total_memory_mb = memory.total // (1024 * 1024)
            resources.cpu_available_memory_mb = memory.available // (1024 * 1024)
        except ImportError:
            # 回退方案：从/proc/meminfo读取
            resources.cpu_total_memory_mb, resources.cpu_available_memory_mb = self._get_memory_from_proc()
        
        logger.info(f"CPU: {resources.cpu_count} 核心")
        logger.info(f"内存: {resources.cpu_total_memory_mb}MB 总量, {resources.cpu_available_memory_mb}MB 可用")
    
    def _get_memory_from_proc(self) -> Tuple[int, int]:
        """从/proc/meminfo获取内存信息"""
        total_mb = 8192  # 默认8GB
        available_mb = 4096  # 默认4GB
        
        try:
            with open('/proc/meminfo', 'r') as f:
                for line in f:
                    if line.startswith('MemTotal:'):
                        total_mb = int(line.split()[1]) // 1024
                    elif line.startswith('MemAvailable:'):
                        available_mb = int(line.split()[1]) // 1024
        except (FileNotFoundError, IOError, ValueError):
            pass
        
        return total_mb, available_mb
    
    def _estimate_task_consumption(self, resources: SystemResources):
        """估算单任务资源消耗"""
        # 基于经验估算
        # Mask2Former Large 模型约需要 2-4GB 显存
        # 图像处理额外需要 500MB-1GB
        
        if resources.gpu_available:
            # GPU模式：主要消耗显存
            resources.estimated_gpu_per_task_mb = 3000  # 约3GB
            resources.estimated_cpu_per_task_mb = 500  # 约500MB
        else:
            # CPU模式：主要消耗内存
            resources.estimated_gpu_per_task_mb = 0
            resources.estimated_cpu_per_task_mb = 3000  # 约3GB
    
    def calculate_optimal_workers(self, custom_ratio: Optional[float] = None) -> int:
        """
        计算最优并行数
        
        Args:
            custom_ratio: 自定义资源使用比率，None使用配置中的比率
            
        Returns:
            int: 推荐的并行数
        """
        if self._resources is None:
            self.detect_resources()
        
        resources = self._resources
        
        if resources.gpu_available:
            # GPU模式：基于显存计算
            ratio = custom_ratio or self.config.gpu_memory_ratio
            available_memory = int(resources.gpu_free_memory_mb * ratio)
            available_memory -= self.config.reserve_memory_mb
            
            if resources.estimated_gpu_per_task_mb > 0:
                gpu_workers = max(1, available_memory // resources.estimated_gpu_per_task_mb)
            else:
                gpu_workers = 1
            
            # 同时考虑CPU内存
            cpu_available = int(resources.cpu_available_memory_mb * self.config.cpu_memory_ratio)
            cpu_available -= self.config.reserve_memory_mb
            cpu_workers = max(1, cpu_available // resources.estimated_cpu_per_task_mb)
            
            # 取较小值，并限制范围
            workers = min(gpu_workers, cpu_workers)
            
        else:
            # CPU模式：基于内存计算
            ratio = custom_ratio or self.config.cpu_memory_ratio
            available_memory = int(resources.cpu_available_memory_mb * ratio)
            available_memory -= self.config.reserve_memory_mb
            
            workers = max(1, available_memory // resources.estimated_cpu_per_task_mb)
        
        # 限制范围
        workers = max(self.config.min_workers, min(workers, self.config.max_workers))
        workers = min(workers, resources.cpu_count)  # 不超过CPU核心数
        
        logger.info(f"计算最优并行数: {workers}")
        logger.info(f"  资源使用比率: {ratio:.1%}")
        logger.info(f"  可用内存: {available_memory}MB")
        logger.info(f"  单任务消耗: {resources.estimated_gpu_per_task_mb or resources.estimated_cpu_per_task_mb}MB")
        
        return workers
    
    def get_resource_summary(self) -> str:
        """
        获取资源摘要信息
        
        Returns:
            str: 资源摘要
        """
        if self._resources is None:
            self.detect_resources()
        
        r = self._resources
        lines = [
            "=== 系统资源摘要 ===",
            f"CPU: {r.cpu_count} 核心",
            f"内存: {r.cpu_total_memory_mb}MB 总量, {r.cpu_available_memory_mb}MB 可用",
        ]
        
        if r.gpu_available:
            lines.extend([
                f"GPU: {r.gpu_name}",
                f"显存: {r.gpu_total_memory_mb}MB 总量, {r.gpu_free_memory_mb}MB 可用",
            ])
        else:
            lines.append("GPU: 不可用")
        
        lines.extend([
            "",
            "=== 单任务估算 ===",
            f"GPU消耗: {r.estimated_gpu_per_task_mb}MB",
            f"CPU消耗: {r.estimated_cpu_per_task_mb}MB",
        ])
        
        return "\n".join(lines)


def get_optimal_workers(
    gpu_memory_ratio: float = 0.8,
    cpu_memory_ratio: float = 0.7,
    reserve_memory_mb: int = 1024
) -> int:
    """
    获取最优并行数（便捷函数）
    
    Args:
        gpu_memory_ratio: GPU显存使用比率
        cpu_memory_ratio: CPU内存使用比率
        reserve_memory_mb: 预留内存
        
    Returns:
        int: 推荐的并行数
    """
    config = ResourceConfig(
        gpu_memory_ratio=gpu_memory_ratio,
        cpu_memory_ratio=cpu_memory_ratio,
        reserve_memory_mb=reserve_memory_mb
    )
    
    manager = ResourceManager(config)
    return manager.calculate_optimal_workers()


def print_resource_info():
    """打印系统资源信息"""
    manager = ResourceManager()
    manager.detect_resources()
    print(manager.get_resource_summary())
    print()
    print(f"推荐并行数: {manager.calculate_optimal_workers()}")
