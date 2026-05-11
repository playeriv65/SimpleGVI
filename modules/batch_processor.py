import glob
import logging
import os

import pandas as pd
from tqdm import tqdm

from modules.async_visualizer import get_async_visualizer, shutdown_async_visualizer
from modules.gvi_calculator import (
    calculate_vegetation_class_gvi,
    calculate_gvi,
    get_models,
    prepare_image_for_processing,
    segment_images,
)
from modules.visualization import save_segmentation_visualization

logger = logging.getLogger(__name__)

IMAGE_EXTENSIONS = ["*.jpg", "*.jpeg", "*.png", "*.bmp", "*.tif", "*.tiff"]


def _get_image_files(folder_path: str):
    image_files = []

    for ext in IMAGE_EXTENSIONS:
        image_files.extend(glob.glob(os.path.join(folder_path, ext)))
        if os.name != "nt":
            image_files.extend(glob.glob(os.path.join(folder_path, ext.upper())))

    image_files = list(set(image_files))
    return [f for f in image_files if "_segmentation.png" not in f]


def _iter_batches(items, batch_size: int):
    for start in range(0, len(items), batch_size):
        yield items[start:start + batch_size]


def process_image_folder(
    folder_path: str,
    output_dir: str,
    save_segmentation: bool = False,
    is_panoramic: bool = False,
    batch_size: int = 1,
):
    """
    处理文件夹中的所有图像并计算 GVI。

    batch_size 控制单次送入模型的图像数量；模型只加载一次。
    """
    return _process_batched(
        folder_path,
        output_dir,
        save_segmentation,
        is_panoramic,
        batch_size,
    )


def _process_batched(
    folder_path: str,
    output_dir: str,
    save_segmentation: bool,
    is_panoramic: bool,
    batch_size: int,
) -> pd.DataFrame:
    """使用单个模型按 batch 处理图像文件夹。"""
    batch_size = max(1, int(batch_size))

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    image_files = _get_image_files(folder_path)

    if not image_files:
        logger.warning(f"在 {folder_path} 未找到图像文件")
        return pd.DataFrame()

    logger.info(f"批量大小: {batch_size}")
    logger.info("加载语义分割模型...")
    processor, model = get_models()
    visualizer = get_async_visualizer(max_threads=2, max_pending=4) if save_segmentation else None

    results = []

    batches = list(_iter_batches(image_files, batch_size))
    for batch_paths in tqdm(batches, desc="处理批次"):
        batch_items = []

        for image_path in batch_paths:
            image_name = os.path.basename(image_path)
            try:
                display_image, segmentation_image = prepare_image_for_processing(
                    image_path,
                    is_panoramic,
                )
                batch_items.append(
                    {
                        "image_name": image_name,
                        "image_path": image_path,
                        "display_image": display_image,
                        "segmentation_image": segmentation_image,
                    }
                )
            except Exception as e:
                logger.error(f"读取 {image_name} 时出错: {e}")
                results.append(
                    {
                        "image_name": image_name,
                        "image_path": image_path,
                        "GVI": 0.0,
                        "segmentation_path": None,
                        "error": str(e),
                    }
                )

        if not batch_items:
            continue

        try:
            segmentations = segment_images(
                [item["segmentation_image"] for item in batch_items],
                processor,
                model,
            )
        except Exception as e:
            logger.error(f"批次处理失败: {e}")
            for item in batch_items:
                results.append(
                    {
                        "image_name": item["image_name"],
                        "image_path": item["image_path"],
                        "GVI": 0.0,
                        "segmentation_path": None,
                        "error": str(e),
                    }
                )
            continue

        for item, segmentation in zip(batch_items, segmentations):
            gvi = calculate_gvi(segmentation)
            class_gvi = calculate_vegetation_class_gvi(segmentation)
            segmentation_path = None

            if save_segmentation and visualizer:
                out_name = os.path.splitext(item["image_name"])[0] + "_segmentation.png"
                segmentation_path = os.path.join(output_dir, out_name)
                visualizer.submit_visualization(
                    save_segmentation_visualization,
                    item["display_image"],
                    segmentation,
                    gvi,
                    segmentation_path,
                )

            results.append(
                {
                    "image_name": item["image_name"],
                    "image_path": item["image_path"],
                    **class_gvi,
                    "GVI": gvi,
                    "segmentation_path": segmentation_path,
                    "error": None,
                }
            )

    if visualizer:
        logger.info("等待可视化任务完成...")
        visualizer.wait_all()
        stats = visualizer.get_stats()
        logger.info(f"可视化完成: {stats['completed']} 成功, {stats['failed']} 失败")
        shutdown_async_visualizer()

    df = pd.DataFrame(results)
    csv_path = os.path.join(output_dir, "gvi_results.csv")
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    logger.info(f"结果已保存到 {csv_path}")

    valid_results = df[df["error"].isna()] if "error" in df.columns else df
    if not valid_results.empty:
        avg_gvi = valid_results["GVI"].mean()
        logger.info(f"平均绿视指数: {avg_gvi:.4f}")

    return df
