"""
并行处理器模块

实现图像的并行处理，充分利用CPU/GPU资源。
使用进程池处理图像，队列机制控制并发数。
"""

import os
import glob
import logging
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
from queue import Queue
import threading

import pandas as pd
from tqdm import tqdm

logger = logging.getLogger(__name__)


@dataclass
class ProcessingConfig:
    """处理配置"""
    max_workers: int = 4  # 最大并行数
    max_queue_size: int = 100  # 最大队列大小
    save_segmentation: bool = False
    is_panoramic: bool = False
    output_dir: str = "results"


@dataclass
class ImageTask:
    """图像处理任务"""
    image_path: str
    image_name: str
    output_dir: str
    save_segmentation: bool
    is_panoramic: bool


@dataclass
class ProcessingResult:
    """处理结果"""
    image_name: str
    image_path: str
    gvi: float
    segmentation_path: Optional[str] = None
    error: Optional[str] = None


def _process_single_image(task: ImageTask) -> ProcessingResult:
    """
    处理单张图像（在子进程中执行）
    
    Args:
        task: 图像处理任务
        
    Returns:
        ProcessingResult: 处理结果
    """
    from modules.gvi_calculator import process_image, get_models
    from modules.visualization import save_segmentation_visualization
    
    try:
        # 每个子进程加载自己的模型
        processor, model = get_models()
        
        # 处理图像
        gvi, segmentation, processed_image = process_image(
            task.image_path, 
            task.is_panoramic, 
            processor, 
            model
        )
        
        # 保存分割结果（如果需要）
        segmentation_path = None
        if task.save_segmentation:
            out_name = os.path.splitext(task.image_name)[0] + '_segmentation.png'
            segmentation_path = os.path.join(task.output_dir, out_name)
            save_segmentation_visualization(
                task.image_path,
                segmentation,
                gvi,
                segmentation_path
            )
        
        return ProcessingResult(
            image_name=task.image_name,
            image_path=task.image_path,
            gvi=gvi,
            segmentation_path=segmentation_path
        )
        
    except Exception as e:
        logger.error(f"处理 {task.image_name} 失败: {e}")
        return ProcessingResult(
            image_name=task.image_name,
            image_path=task.image_path,
            gvi=0.0,
            error=str(e)
        )


class ParallelProcessor:
    """
    并行图像处理器
    
    使用进程池并行处理图像，队列机制控制资源使用。
    """
    
    def __init__(self, config: ProcessingConfig):
        """
        初始化并行处理器
        
        Args:
            config: 处理配置
        """
        self.config = config
        self._task_queue: Queue = Queue(maxsize=config.max_queue_size)
        self._results: List[ProcessingResult] = []
        self._lock = threading.Lock()
    
    def _get_image_files(self, folder_path: str) -> List[str]:
        """
        获取文件夹中的所有图像文件
        
        Args:
            folder_path: 文件夹路径
            
        Returns:
            图像文件路径列表
        """
        image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.bmp', '*.tif', '*.tiff']
        image_files = []
        
        for ext in image_extensions:
            image_files.extend(glob.glob(os.path.join(folder_path, ext)))
            if os.name != 'nt':
                image_files.extend(glob.glob(os.path.join(folder_path, ext.upper())))
        
        image_files = list(set(image_files))
        image_files = [f for f in image_files if "_segmentation.png" not in f]
        
        return image_files
    
    def process_folder(
        self,
        folder_path: str,
        progress_callback: Optional[Callable] = None
    ) -> pd.DataFrame:
        """
        并行处理文件夹中的所有图像
        
        Args:
            folder_path: 图像文件夹路径
            progress_callback: 进度回调函数
            
        Returns:
            结果DataFrame
        """
        # 获取图像文件列表
        image_files = self._get_image_files(folder_path)
        
        if not image_files:
            logger.warning(f"在 {folder_path} 未找到图像文件")
            return pd.DataFrame()
        
        # 确保输出目录存在
        if not os.path.exists(self.config.output_dir):
            os.makedirs(self.config.output_dir)
        
        # 创建任务列表
        tasks = [
            ImageTask(
                image_path=image_path,
                image_name=os.path.basename(image_path),
                output_dir=self.config.output_dir,
                save_segmentation=self.config.save_segmentation,
                is_panoramic=self.config.is_panoramic
            )
            for image_path in image_files
        ]
        
        # 使用进程池并行处理
        results = []
        
        with ProcessPoolExecutor(max_workers=self.config.max_workers) as executor:
            # 提交所有任务
            future_to_task = {
                executor.submit(_process_single_image, task): task
                for task in tasks
            }
            
            # 处理完成的任务
            with tqdm(total=len(tasks), desc="处理图像") as pbar:
                for future in as_completed(future_to_task):
                    task = future_to_task[future]
                    try:
                        result = future.result()
                        results.append(result)
                        
                        if result.error:
                            logger.warning(f"处理 {result.image_name} 出错: {result.error}")
                        else:
                            logger.info(f"完成 {result.image_name}: GVI={result.gvi:.4f}")
                            
                    except Exception as e:
                        logger.error(f"任务异常 {task.image_name}: {e}")
                        results.append(ProcessingResult(
                            image_name=task.image_name,
                            image_path=task.image_path,
                            gvi=0.0,
                            error=str(e)
                        ))
                    
                    pbar.update(1)
                    if progress_callback:
                        progress_callback(len(results), len(tasks))
        
        # 转换为DataFrame
        df = pd.DataFrame([
            {
                'image_name': r.image_name,
                'image_path': r.image_path,
                'GVI': r.gvi,
                'segmentation_path': r.segmentation_path,
                'error': r.error
            }
            for r in results
        ])
        
        # 保存结果
        csv_path = os.path.join(self.config.output_dir, 'gvi_results.csv')
        df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        logger.info(f"结果已保存到 {csv_path}")
        
        # 计算平均GVI
        valid_results = df[df['error'].isna()]
        if not valid_results.empty:
            avg_gvi = valid_results['GVI'].mean()
            logger.info(f"平均绿视指数: {avg_gvi:.4f}")
        
        return df


def process_image_folder_parallel(
    folder_path: str,
    output_dir: str = "results",
    save_segmentation: bool = False,
    is_panoramic: bool = False,
    max_workers: int = 4
) -> pd.DataFrame:
    """
    并行处理图像文件夹（便捷函数）
    
    Args:
        folder_path: 图像文件夹路径
        output_dir: 输出目录
        save_segmentation: 是否保存分割结果
        is_panoramic: 是否为全景图
        max_workers: 最大并行数
        
    Returns:
        结果DataFrame
    """
    config = ProcessingConfig(
        max_workers=max_workers,
        save_segmentation=save_segmentation,
        is_panoramic=is_panoramic,
        output_dir=output_dir
    )
    
    processor = ParallelProcessor(config)
    return processor.process_folder(folder_path)
