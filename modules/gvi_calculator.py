"""
绿视指数计算模块
使用 Mask2Former 模型进行语义分割和 GVI 计算
"""

import torch
import warnings
from transformers import AutoImageProcessor, Mask2FormerForUniversalSegmentation
from PIL import Image, ImageOps
from config.settings import ADE20K_VEGETATION_CLASSES

warnings.filterwarnings(
    "ignore",
    message=".*The following named arguments are not valid for `Mask2FormerImageProcessor.__init__`.*",
)

# ============================================================
# 配置常量
# ============================================================
# 图像尺寸限制
SEGMENTATION_SHORT_SIDE = 384  # 分割图短边最大边长 (像素)
DISPLAY_SHORT_SIDE = 1024  # 展示图短边最大边长 (像素)
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
    model = model.to(device=device)
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


def resize_to_max_short_side(image, max_short_side=SEGMENTATION_SHORT_SIDE):
    """
    等比例缩小图像，使短边不超过指定尺寸。

    只在短边超过限制时压缩，不放大小图。
    """
    width, height = image.size
    short_side = min(width, height)

    if short_side <= max_short_side:
        return image

    scale = max_short_side / short_side
    new_width = max(MIN_IMAGE_SIZE, int(width * scale))
    new_height = max(MIN_IMAGE_SIZE, int(height * scale))
    return image.resize((new_width, new_height), Image.Resampling.LANCZOS)


def process_panoramic_image(
    image, processor, model, max_short_side=SEGMENTATION_SHORT_SIDE
):
    """
    处理全景图像
    
    全景图像通常在底部有畸变；先裁剪底部区域，
    展示图按短边 1024px 输出，分割图按短边 384px 计算。
    
    Args:
        image: PIL Image 对象
        processor: 图像处理器
        model: 分割模型
        max_short_side: 分割图短边最大边长
    
    Returns:
        tuple: (gvi, segmentation, image) GVI 值、分割结果和展示图像
    """
    width, height = image.size

    # 裁剪底部 20% (全景图像地面畸变校正)
    bottom_crop = int(height * PANORAMIC_BOTTOM_CROP_RATIO)
    image = image.crop((0, 0, width, height - bottom_crop))
    display_image = resize_to_max_short_side(image, DISPLAY_SHORT_SIDE)
    segmentation_image = resize_to_max_short_side(image, max_short_side)

    segmentation = segment_image(segmentation_image, processor, model)
    gvi = calculate_gvi(segmentation)

    return gvi, segmentation, display_image


def process_image(
    image_path, is_panoramic, processor, model, max_short_side=SEGMENTATION_SHORT_SIDE
):
    """
    处理图像并计算绿视指数
    
    Args:
        image_path: 图像文件路径
        is_panoramic: 是否为全景图像
        processor: 图像处理器
        model: 分割模型
        max_short_side: 分割图短边最大边长，默认 384px（避免显存溢出）
    
    Returns:
        tuple: (gvi, segmentation, display_image) - GVI 值、分割结果、展示图像
    
    Raises:
        FileNotFoundError: 图像文件不存在
        PIL.UnidentifiedImageError: 无法识别的图像格式
    """
    image = Image.open(image_path)
    
    # 🔧 修复 EXIF 方向问题 - 自动纠正手机照片的旋转
    image = ImageOps.exif_transpose(image)
    
    if is_panoramic:
        gvi, segmentation, image = process_panoramic_image(
            image, processor, model, max_short_side
        )
    else:
        display_image = resize_to_max_short_side(image, DISPLAY_SHORT_SIDE)
        segmentation_image = resize_to_max_short_side(image, max_short_side)
        segmentation = segment_image(segmentation_image, processor, model)
        gvi = calculate_gvi(segmentation)
        image = display_image
    
    # 返回处理后的图像（用于显示）
    return gvi, segmentation, image
