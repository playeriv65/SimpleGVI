import torch
import warnings
from transformers import AutoImageProcessor, Mask2FormerForUniversalSegmentation
from PIL import Image
import numpy as np
from config.settings import ADE20K_VEGETATION_CLASSES

warnings.filterwarnings(
    "ignore",
    message=".*The following named arguments are not valid for `Mask2FormerImageProcessor.__init__`.*",
)


def get_models():
    """加载预训练的 ADE20K 语义分割模型"""
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
    """对输入图像进行语义分割"""
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
    """计算分割图像的绿视指数(GVI)"""
    total_pixels = segmentation.numel()

    vegetation_pixels = 0
    for veg_class in ADE20K_VEGETATION_CLASSES:
        vegetation_pixels += (segmentation == veg_class).sum().item()

    return vegetation_pixels / total_pixels if total_pixels else 0


def process_panoramic_image(image, processor, model):
    """处理全景图像"""
    width, height = image.size

    bottom_crop = int(height * 0.2)
    image = image.crop((0, 0, width, height - bottom_crop))

    segmentation = segment_image(image, processor, model)

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
    """从多个分割结果计算平均绿视指数"""
    total_pixels = 0
    vegetation_pixels = 0

    for segment in segmentations:
        total_pixels += segment.numel()
        for veg_class in ADE20K_VEGETATION_CLASSES:
            vegetation_pixels += (segment == veg_class).sum().item()

    return vegetation_pixels / total_pixels if total_pixels else 0


def process_image(image_path, is_panoramic, processor, model):
    """处理图像并计算绿视指数"""
    image = Image.open(image_path)

    if is_panoramic:
        return process_panoramic_image(image, processor, model)
    else:
        segmentation = segment_image(image, processor, model)
        gvi = calculate_gvi(segmentation)
        return gvi, segmentation
