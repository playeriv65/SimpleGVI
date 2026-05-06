"""
并行处理器模块

实现图像的并行处理，充分利用CPU/GPU资源。
使用实时资源监测，动态控制任务提交。
"""

import os
import glob
import time
import logging
from concurrent.futures import ProcessPoolExecutor, as_completed, Future
from typing import List, Optional, Callable
from dataclasses import dataclass

import pandas as pd
from tqdm import tqdm

from modules.resource_manager import ResourceMonitor, ResourceConfig, get_resource_monitor

logger = logging.getLogger(__name__)


@dataclass
class ProcessingConfig:
    """处理配置"""
    max_workers: int = 16  # 最大并行数上限
    save_segmentation: bool = False
    is_panoramic: bool = False
    output_dir: str = "results"
    max_memory_usage: float = 0.85  # 最大内存使用率


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
    """处理单张图像（在子进程中执行）"""
    from modules.gvi_calculator import process_image, get_models
    from modules.visualization import save_segmentation_visualization
    
    try:
        processor, model = get_models()
        
        gvi, segmentation, processed_image = process_image(
            task.image_path, 
            task.is_panoramic, 
            processor, 
            model
        )
        
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
    
    填满式策略：不断提交任务，直到内存/显存接近上限。
    资源不足时等待任务完成，释放资源后继续提交。
    """
    
    def __init__(self, config: ProcessingConfig):
        self.config = config
        
        resource_config = ResourceConfig(
            max_memory_usage=config.max_memory_usage,
            max_workers=config.max_workers
        )
        self.monitor = get_resource_monitor(resource_config)
    
    def _get_image_files(self, folder_path: str) -> List[str]:
        """获取文件夹中的所有图像文件"""
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
        
        填满式策略：
        1. 不断提交任务，直到内存/显存接近上限
        2. 等待任务完成，释放资源后继续提交
        """
        image_files = self._get_image_files(folder_path)
        
        if not image_files:
            logger.warning(f"在 {folder_path} 未找到图像文件")
            return pd.DataFrame()
        
        if not os.path.exists(self.config.output_dir):
            os.makedirs(self.config.output_dir)
        
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
        
        results = []
        futures: dict[Future, ImageTask] = {}
        pending_futures = set()
        
        with ProcessPoolExecutor(max_workers=self.config.max_workers) as executor:
            with tqdm(total=len(tasks), desc="处理图像") as pbar:
                task_iter = iter(tasks)
                
                while True:
                    # 填满式提交：不断提交直到资源接近上限
                    while len(pending_futures) < self.config.max_workers:
                        # 检查资源是否可用
                        if not self.monitor.can_submit_task():
                            memory_usage = self.monitor.get_memory_usage()
                            logger.debug(f"内存使用率 {memory_usage:.1%}，等待资源释放...")
                            break
                        
                        try:
                            task = next(task_iter)
                        except StopIteration:
                            break
                        
                        future = executor.submit(_process_single_image, task)
                        futures[future] = task
                        pending_futures.add(future)
                    
                    # 所有任务都完成了
                    if not pending_futures:
                        break
                    
                    # 等待一个任务完成
                    done = set()
                    for future in pending_futures:
                        if future.done():
                            done.add(future)
                    
                    # 如果没有完成的任务，等待一小段时间
                    if not done:
                        time.sleep(0.1)
                        continue
                    
                    # 处理完成的任务
                    for future in done:
                        pending_futures.remove(future)
                        task = futures[future]
                        
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
        
        csv_path = os.path.join(self.config.output_dir, 'gvi_results.csv')
        df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        logger.info(f"结果已保存到 {csv_path}")
        
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
    max_workers: int = 16,
    max_memory_usage: float = 0.85
) -> pd.DataFrame:
    """并行处理图像文件夹（便捷函数）"""
    config = ProcessingConfig(
        max_workers=max_workers,
        save_segmentation=save_segmentation,
        is_panoramic=is_panoramic,
        output_dir=output_dir,
        max_memory_usage=max_memory_usage
    )
    
    processor = ParallelProcessor(config)
    return processor.process_folder(folder_path)
