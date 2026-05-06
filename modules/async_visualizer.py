"""
异步可视化模块

将可视化任务从主计算流程分离，使用线程池异步执行。
避免CPU密集的画图操作阻塞GPU/CPU计算。
"""

import os
import threading
from concurrent.futures import ThreadPoolExecutor, Future
from typing import Optional, Callable
import logging

logger = logging.getLogger(__name__)


class AsyncVisualizer:
    """
    异步可视化处理器
    
    使用线程池异步执行可视化任务，不阻塞主计算流程。
    """
    
    def __init__(self, max_workers: int = 2):
        """
        初始化异步可视化处理器
        
        Args:
            max_workers: 最大并发画图线程数，默认2
        """
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._futures: list[Future] = []
        self._lock = threading.Lock()
        self._completed_count = 0
        self._failed_count = 0
    
    def submit_visualization(
        self,
        func: Callable,
        image_path: str,
        segmentation,
        gvi: float,
        output_path: str,
        callback: Optional[Callable] = None
    ) -> Future:
        """
        提交可视化任务到异步队列
        
        Args:
            func: 可视化函数
            image_path: 原始图像路径
            segmentation: 分割结果
            gvi: GVI值
            output_path: 输出路径
            callback: 完成回调函数
            
        Returns:
            Future对象，可用于等待任务完成
        """
        def _task():
            try:
                func(image_path, segmentation, gvi, output_path)
                with self._lock:
                    self._completed_count += 1
                if callback:
                    callback(output_path, None)
                return output_path
            except Exception as e:
                with self._lock:
                    self._failed_count += 1
                logger.error(f"可视化任务失败: {output_path} - {e}")
                if callback:
                    callback(output_path, e)
                raise
        
        future = self._executor.submit(_task)
        
        with self._lock:
            self._futures.append(future)
        
        return future
    
    def wait_all(self, timeout: Optional[float] = None):
        """
        等待所有可视化任务完成
        
        Args:
            timeout: 超时时间（秒），None表示无限等待
        """
        with self._lock:
            futures = self._futures.copy()
        
        for future in futures:
            try:
                future.result(timeout=timeout)
            except Exception:
                pass  # 错误已在任务中处理
    
    def get_stats(self) -> dict:
        """
        获取可视化任务统计信息
        
        Returns:
            dict: 包含完成数、失败数、待处理数
        """
        with self._lock:
            pending_count = len(self._futures) - self._completed_count - self._failed_count
            return {
                'completed': self._completed_count,
                'failed': self._failed_count,
                'pending': max(0, pending_count)
            }
    
    def shutdown(self, wait: bool = True):
        """
        关闭线程池
        
        Args:
            wait: 是否等待所有任务完成
        """
        self._executor.shutdown(wait=wait)


# 全局可视化器实例
_visualizer: Optional[AsyncVisualizer] = None
_init_lock = threading.Lock()


def get_async_visualizer(max_workers: int = 2) -> AsyncVisualizer:
    """
    获取全局异步可视化器实例（单例模式）
    
    Args:
        max_workers: 最大并发线程数
        
    Returns:
        AsyncVisualizer实例
    """
    global _visualizer
    
    if _visualizer is None:
        with _init_lock:
            if _visualizer is None:
                _visualizer = AsyncVisualizer(max_workers=max_workers)
    
    return _visualizer


def shutdown_async_visualizer():
    """关闭全局异步可视化器"""
    global _visualizer
    
    if _visualizer is not None:
        with _init_lock:
            if _visualizer is not None:
                _visualizer.shutdown(wait=True)
                _visualizer = None
