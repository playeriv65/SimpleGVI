import os
import platform
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import torch
from modules.legend_config import (
    get_ade20k_color_palette,
    convert_to_vegetation_visualization,
)
from config.settings import ADE20K_VEGETATION_CLASSES

ADE20K_COLOR_PALETTE = get_ade20k_color_palette()
VEGETATION_CLASS_IDS = ADE20K_VEGETATION_CLASSES


def _get_system_fonts():
    """获取当前系统的可用字体路径列表（按优先级排序）"""
    system = platform.system()

    if system == "Linux":
        return [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
        ]
    elif system == "Darwin":
        return [
            "/System/Library/Fonts/Helvetica.ttc",
            "/System/Library/Fonts/HelveticaNeue.ttc",
            "/Library/Fonts/Arial.ttf",
            "/System/Library/Fonts/Supplemental/Arial.ttf",
        ]
    elif system == "Windows":
        return [
            "C:\\Windows\\Fonts\\msyh.ttc",
            "C:\\Windows\\Fonts\\simhei.ttf",
            "C:\\Windows\\Fonts\\arial.ttf",
            "C:\\Windows\\Fonts\\segoeui.ttf",
        ]
    else:
        return []


def _load_font(size, bold=False):
    """加载系统字体，如果找不到则使用默认字体"""
    fonts = _get_system_fonts()

    if bold:
        for font_path in fonts:
            if "Bold" in font_path or "Bold" in os.path.basename(font_path):
                if os.path.exists(font_path):
                    try:
                        return ImageFont.truetype(font_path, size)
                    except:
                        pass

    for font_path in fonts:
        if os.path.exists(font_path):
            try:
                return ImageFont.truetype(font_path, size)
            except:
                pass

    return ImageFont.load_default()


def segmentation_to_color(segmentation_tensor):
    """
    将分割张量转换为RGB彩色图像

    Args:
        segmentation_tensor (torch.Tensor or np.ndarray): 分割结果张量或数组

    Returns:
        numpy.ndarray: RGB彩色图像 (H, W, 3)，uint8类型
    """
    if isinstance(segmentation_tensor, torch.Tensor):
        segmentation_array = segmentation_tensor.numpy()
    else:
        segmentation_array = segmentation_tensor

    return convert_to_vegetation_visualization(segmentation_array)


def get_class_color(class_id):
    """
    获取指定类别ID的颜色

    Args:
        class_id (int): 类别ID

    Returns:
        list: RGB颜色值 [R, G, B]
    """
    if 0 <= class_id < len(ADE20K_COLOR_PALETTE):
        return ADE20K_COLOR_PALETTE[class_id]
    return [0, 0, 0]


def is_vegetation(class_id):
    """
    判断指定类别是否为植被

    Args:
        class_id (int): 类别ID

    Returns:
        bool: 是否为植被类别
    """
    return class_id in VEGETATION_CLASS_IDS


def save_segmentation_visualization(image_path, segmentation, gvi, output_path):
    """
    保存分割可视化结果

    将原始图像与语义分割结果并排显示，并添加标题、图例和GVI值。
    使用 ADE20K 150类别调色板，植被类别用绿色系显示，非植被用灰色显示。

    Args:
        image_path (str): 原始图像文件路径
        segmentation (torch.Tensor or np.ndarray): 分割结果（类别ID数组）
        gvi (float): 绿视指数值 (0-1)
        output_path (str): 输出图像保存路径

    Returns:
        None
    """
    with Image.open(image_path) as img:
        original_image = img.convert("RGB")

    colored_segmentation = segmentation_to_color(segmentation)
    seg_image = Image.fromarray(colored_segmentation)

    if seg_image.size != original_image.size:
        seg_image = seg_image.resize(original_image.size, Image.NEAREST)

    width, height = original_image.size
    combined = Image.new("RGB", (width * 2, height + 80), (255, 255, 255))
    combined.paste(original_image, (0, 60))
    combined.paste(seg_image, (width, 60))

    draw = ImageDraw.Draw(combined)
    font_title = _load_font(24, bold=True)
    font_text = _load_font(18)

    title = f"ADE20K 语义分割 | 绿视指数 GVI: {gvi:.2%}"
    draw.text((10, 15), title, fill=(0, 0, 0), font=font_title)
    draw.text((10, height + 65), "原始图像", fill=(0, 0, 0), font=font_text)
    draw.text(
        (width + 10, height + 65), "分割结果 (150类别)", fill=(0, 0, 0), font=font_text
    )

    legend_y = 50
    from config.settings import VEGETATION_NAMES, get_vegetation_colors

    vegetation_names = VEGETATION_NAMES
    vegetation_colors = get_vegetation_colors()

    legend_items = []
    for i, label in enumerate(vegetation_names):
        if i < len(vegetation_colors):
            color = vegetation_colors[i]
            legend_items.append((label, color))
    legend_items.append(("非植物", [128, 128, 128]))

    x_start = width * 2 - 550
    x_offset = x_start
    item_spacing = 90

    for i, (label, color) in enumerate(legend_items):
        if i == 3:
            x_offset = x_start
            legend_y = 25

        draw.rectangle(
            [x_offset, legend_y, x_offset + 12, legend_y + 12], fill=tuple(color)
        )
        draw.text((x_offset + 16, legend_y - 2), label, fill=(0, 0, 0), font=font_text)
        x_offset += item_spacing

    combined.save(output_path, "PNG")
