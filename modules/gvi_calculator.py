"""
绿视指数计算模块
使用 Mask2Former 模型进行语义分割和 GVI 计算
"""

import torch
import warnings
from transformers import AutoImageProcessor, Mask2FormerForUniversalSegmentation
from PIL import Image, ImageOps
import numpy as np
from config.settings import ADE20K_VEGETATION_CLASSES

warnings.filterwarnings(
    "ignore",
    message=".*The following named arguments are not valid for `Mask2FormerImageProcessor.__init__`.*",
)

# ============================================================
# 配置常量
# ============================================================
# 图像尺寸限制
MAX_IMAGE_SIZE = 1024  # 最大边长 (像素)
MIN_IMAGE_SIZE = 1  # 最小边长 (避免 resize 到 0)
# 全景图像处理
PANORAMIC_BOTTOM_CROP_RATIO = 0.2  # 裁剪底部 20% (移除地面畸变区域)


def get_models():
    """
    加载预训练的 ADE20K 语义分割模型
    
    Returns:
        tuple: (processor, model) 图像处理器和分割模型
    """
    processor = AutoImageProcessor.from_pretrained(
        "facebook/mask2former-swin-large-ade-semantic", use_fast=True
    )
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = Mask2FormerForUniversalSegmentation.from_pretrained(
        "facebook/mask2former-swin-large-ade-semantic"
    )
    model = model.to(device)
    return processor, model


def segment_image(image, processor, model):
    """
    对输入图像进行语义分割
    
    Args:
        image: PIL Image 对象
        processor: 图像处理器
        model: 分割模型
    
    Returns:
        torch.Tensor: 分割结果张量
    """
    inputs = processor(images=image, return_tensors="pt")

    with torch.no_grad():
        if torch.cuda.is_available():
            inputs = {k: v.to("cuda") for k, v in inputs.items()}
            outputs = model(**inputs)
            segmentation = processor.post_process_semantic_segmentation(
                outputs, target_sizes=[image.size[::-1]]
            )[0].to("cpu")
        else:
            outputs = model(**inputs)
            segmentation = processor.post_process_semantic_segmentation(
                outputs, target_sizes=[image.size[::-1]]
            )[0]

    return segmentation


def calculate_gvi(segmentation):
    """
    计算分割图像的绿视指数 (GVI)
    
    Args:
        segmentation: 分割结果张量
    
    Returns:
        float: GVI 值 (0-1 之间)
    """
    total_pixels = segmentation.numel()

    vegetation_pixels = 0
    for veg_class in ADE20K_VEGETATION_CLASSES:
        vegetation_pixels += (segmentation == veg_class).sum().item()

    return vegetation_pixels / total_pixels if total_pixels else 0


def process_panoramic_image(image, processor, model):
    """
    处理全景图像
    
    全景图像通常有地面畸变，需要：
    1. 裁剪底部 20% (移除畸变区域)
    2. 分 4 块处理
    3. 取 4 块的平均值
    
    Args:
        image: PIL Image 对象
        processor: 图像处理器
        model: 分割模型
    
    Returns:
        tuple: (gvi, segmentation) GVI 值和分割结果
    """
    width, height = image.size

    # 裁剪底部 20% (全景图像地面畸变校正)
    bottom_crop = int(height * PANORAMIC_BOTTOM_CROP_RATIO)
    image = image.crop((0, 0, width, height - bottom_crop))

    segmentation = segment_image(image, processor, model)

    # 分 4 块处理
    w4 = int(width / 4)
    h4 = int(height / 4)
    hFor43 = int(w4 * 3 / 4)

    segmentations = []

    for w in range(4):
        x_begin = w * w4
        x_end = (w + 1) * w4
        cropped_segmentation = segmentation[h4 : h4 + hFor43, x_begin:x_end]
        segmentations.append(cropped_segmentation)

    gvi = calculate_gvi_from_segmentations(segmentations)

    return gvi, segmentation


def calculate_gvi_from_segmentations(segmentations):
    """
    从多个分割结果计算平均绿视指数
    
    Args:
        segmentations: 分割结果列表
    
    Returns:
        float: 平均 GVI 值
    """
    total_pixels = 0
    vegetation_pixels = 0

    for segment in segmentations:
        total_pixels += segment.numel()
        for veg_class in ADE20K_VEGETATION_CLASSES:
            vegetation_pixels += (segment == veg_class).sum().item()

    return vegetation_pixels / total_pixels if total_pixels else 0


def process_image(image_path, is_panoramic, processor, model, max_size=MAX_IMAGE_SIZE):
    """
    处理图像并计算绿视指数
    
    Args:
        image_path: 图像文件路径
        is_panoramic: 是否为全景图像
        processor: 图像处理器
        model: 分割模型
        max_size: 最大边长限制，默认 1024px（避免显存溢出）
    
    Returns:
        tuple: (gvi, segmentation, resized_image) - GVI 值、分割结果、处理后的图像
    
    Raises:
        FileNotFoundError: 图像文件不存在
        PIL.UnidentifiedImageError: 无法识别的图像格式
    """
    image = Image.open(image_path)
    
    # 🔧 修复 EXIF 方向问题 - 自动纠正手机照片的旋转
    image = ImageOps.exif_transpose(image)
    
    # 自动调整过大图像尺寸 - 长边最大 max_size px
    width, height = image.size
    max_dimension = max(width, height)
    
    if max_dimension > max_size:
        scale = max_size / max_dimension
        # 确保最小尺寸为 1，避免整数截断导致 0 尺寸
        new_width = max(MIN_IMAGE_SIZE, int(width * scale))
        new_height = max(MIN_IMAGE_SIZE, int(height * scale))
        image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    if is_panoramic:
        gvi, segmentation = process_panoramic_image(image, processor, model)
    else:
        segmentation = segment_image(image, processor, model)
        gvi = calculate_gvi(segmentation)
    
    # 返回处理后的图像（用于显示）
    return gvi, segmentation, image
