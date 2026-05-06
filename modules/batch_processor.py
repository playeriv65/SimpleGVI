import os
import glob
import logging
from typing import Optional

import pandas as pd
from tqdm import tqdm

from modules.gvi_calculator import process_image, get_models
from modules.visualization import save_segmentation_visualization
from modules.async_visualizer import get_async_visualizer, shutdown_async_visualizer
from modules.parallel_processor import process_image_folder_parallel, ProcessingConfig, ParallelProcessor

logger = logging.getLogger(__name__)


def process_image_folder(
    folder_path: str,
    output_dir: str,
    save_segmentation: bool = False,
    is_panoramic: bool = False,
    use_parallel: bool = True,
    max_workers: int = 4
):
    """
    处理文件夹中的所有图像并计算GVI
    
    参数:
        folder_path (str): 包含图像的文件夹路径
        output_dir (str): 输出结果的文件夹路径
        save_segmentation (bool): 是否保存分割结果
        is_panoramic (bool): 图像是否为全景图
        use_parallel (bool): 是否使用并行处理，默认True
        max_workers (int): 最大并行数，默认4
    
    返回值:
        pandas.DataFrame: 包含所有图像GVI结果的数据框
    """
    if use_parallel:
        return _process_parallel(folder_path, output_dir, save_segmentation, is_panoramic, max_workers)
    else:
        return _process_sequential(folder_path, output_dir, save_segmentation, is_panoramic)


def _process_parallel(
    folder_path: str,
    output_dir: str,
    save_segmentation: bool,
    is_panoramic: bool,
    max_workers: int
) -> pd.DataFrame:
    """
    并行处理图像文件夹
    """
    config = ProcessingConfig(
        max_workers=max_workers,
        save_segmentation=save_segmentation,
        is_panoramic=is_panoramic,
        output_dir=output_dir
    )
    
    processor = ParallelProcessor(config)
    return processor.process_folder(folder_path)


def _process_sequential(
    folder_path: str,
    output_dir: str,
    save_segmentation: bool,
    is_panoramic: bool
) -> pd.DataFrame:
    """
    串行处理图像文件夹（使用异步可视化）
    """
    # 确保输出目录存在
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    # 支持的图像格式
    image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.bmp', '*.tif', '*.tiff']
    image_files = []
    
    # 获取所有支持格式的图像文件
    for ext in image_extensions:
        image_files.extend(glob.glob(os.path.join(folder_path, ext)))
        if os.name != 'nt':
            image_files.extend(glob.glob(os.path.join(folder_path, ext.upper())))
    
    # 去重并过滤掉可能已经生成的分割结果图
    image_files = list(set(image_files))
    image_files = [f for f in image_files if "_segmentation.png" not in f]
    
    if not image_files:
        logger.warning(f"在 {folder_path} 未找到图像文件")
        return None
    
    # 加载模型（只加载一次）
    logger.info("加载语义分割模型...")
    processor, model = get_models()
    
    # 获取异步可视化器
    visualizer = get_async_visualizer(max_workers=2) if save_segmentation else None
    
    # 存储结果的列表
    results = []
    
    # 处理每个图像文件
    for image_path in tqdm(image_files, desc="处理图像"):
        image_name = os.path.basename(image_path)
        try:
            # 处理图像（GPU/CPU计算）
            gvi, segmentation, processed_image = process_image(
                image_path, is_panoramic, processor, model
            )
            
            # 将结果添加到列表中
            results.append({
                'image_name': image_name,
                'image_path': image_path,
                'GVI': gvi
            })
            
            # 异步保存分割可视化结果
            if save_segmentation and visualizer:
                out_name = os.path.splitext(image_name)[0] + '_segmentation.png'
                output_path = os.path.join(output_dir, out_name)
                visualizer.submit_visualization(
                    save_segmentation_visualization,
                    image_path,
                    segmentation,
                    gvi,
                    output_path
                )
                
        except Exception as e:
            logger.error(f"处理 {image_name} 时出错: {e}")
    
    # 等待所有可视化任务完成
    if visualizer:
        logger.info("等待可视化任务完成...")
        visualizer.wait_all()
        stats = visualizer.get_stats()
        logger.info(f"可视化完成: {stats['completed']} 成功, {stats['failed']} 失败")
        shutdown_async_visualizer()
    
    # 创建DataFrame并保存为CSV
    df = pd.DataFrame(results)
    csv_path = os.path.join(output_dir, 'gvi_results.csv')
    df.to_csv(csv_path, index=False, encoding='utf-8-sig')
    logger.info(f"结果已保存到 {csv_path}")
    
    # 计算平均GVI
    avg_gvi = df['GVI'].mean()
    logger.info(f"平均绿视指数: {avg_gvi:.4f}")
    
    return df
