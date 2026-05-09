import os
import platform
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import torch
from modules.legend_config import (
    get_ade20k_color_palette,
    convert_to_vegetation_visualization,
)
from config.settings import ADE20K_CLASS_INFO, ADE20K_VEGETATION_CLASSES

ADE20K_COLOR_PALETTE = get_ade20k_color_palette()
VEGETATION_CLASS_IDS = ADE20K_VEGETATION_CLASSES


def _get_system_fonts():
    """获取当前系统的可用字体路径列表（按优先级排序）"""
    system = platform.system()

    if system == "Linux":
        return [
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
        ]
    elif system == "Darwin":
        return [
            "/System/Library/Fonts/PingFang.ttc",
            "/System/Library/Fonts/Hiragino Sans GB.ttc",
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


def segmentation_to_color(segmentation_tensor, selected_classes=None):
    """
    将分割张量转换为RGB彩色图像

    Args:
        segmentation_tensor (torch.Tensor or np.ndarray): 分割结果张量或数组
        selected_classes (set, optional): 选中的植被类别ID集合，None表示全部选中

    Returns:
        numpy.ndarray: RGB彩色图像 (H, W, 3)，uint8类型
    """
    if isinstance(segmentation_tensor, torch.Tensor):
        segmentation_array = segmentation_tensor.numpy()
    else:
        segmentation_array = segmentation_tensor

    return convert_to_vegetation_visualization(segmentation_array, selected_classes)


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


def _text_bbox(draw, xy, text, font):
    """Return a text bounding box compatible with current and older Pillow."""
    if hasattr(draw, "textbbox"):
        return draw.textbbox(xy, text, font=font)
    width, height = draw.textsize(text, font=font)
    x, y = xy
    return (x, y, x + width, y + height)


def _draw_label(draw, text, center, font, image_size):
    """Draw a compact label centered at the given point."""
    width, height = image_size
    x, y = center
    bbox = _text_bbox(draw, (0, 0), text, font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    pad_x = 4
    pad_y = 2

    left = int(round(x - text_w / 2 - pad_x))
    top = int(round(y - text_h / 2 - pad_y))
    right = left + text_w + pad_x * 2
    bottom = top + text_h + pad_y * 2

    left = max(0, min(left, width - (right - left)))
    top = max(0, min(top, height - (bottom - top)))
    right = left + text_w + pad_x * 2
    bottom = top + text_h + pad_y * 2

    draw.rounded_rectangle(
        [left, top, right, bottom],
        radius=2,
        fill=(0, 0, 0, 155),
        outline=(255, 255, 255, 170),
        width=1,
    )
    draw.text((left + pad_x, top + pad_y - 1), text, fill=(255, 255, 255, 245), font=font)
    return (left, top, right, bottom)


def _boxes_overlap(a, b, margin=4):
    return not (
        a[2] + margin < b[0]
        or b[2] + margin < a[0]
        or a[3] + margin < b[1]
        or b[3] + margin < a[1]
    )


def _annotate_segmentation(seg_image, segmentation, min_area_ratio=0.003, max_labels=18):
    """Overlay ADE20K class labels on the largest visible regions."""
    if isinstance(segmentation, torch.Tensor):
        segmentation = segmentation.cpu().numpy()

    segmentation = np.asarray(segmentation)
    if segmentation.shape != (seg_image.height, seg_image.width):
        seg_for_labels = Image.fromarray(segmentation.astype(np.uint8)).resize(
            seg_image.size, Image.NEAREST
        )
        segmentation = np.asarray(seg_for_labels)

    overlay = Image.new("RGBA", seg_image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    font = _load_font(13)

    total_pixels = segmentation.size
    min_area = max(80, int(total_pixels * min_area_ratio))
    labels = []

    class_ids, counts = np.unique(segmentation, return_counts=True)
    for class_id, count in zip(class_ids.tolist(), counts.tolist()):
        if count < min_area or class_id not in ADE20K_CLASS_INFO:
            continue

        ys, xs = np.nonzero(segmentation == class_id)
        if len(xs) == 0:
            continue

        # Median point is usually inside the dominant region and resists thin masks.
        labels.append(
            {
                "area": count,
                "name": ADE20K_CLASS_INFO[class_id]["name"],
                "x": float(np.median(xs)),
                "y": float(np.median(ys)),
            }
        )

    labels.sort(key=lambda item: item["area"], reverse=True)
    placed_boxes = []
    for item in labels:
        if len(placed_boxes) >= max_labels:
            break

        bbox = _text_bbox(draw, (0, 0), item["name"], font)
        text_w = bbox[2] - bbox[0] + 8
        text_h = bbox[3] - bbox[1] + 4
        candidate = (
            int(item["x"] - text_w / 2),
            int(item["y"] - text_h / 2),
            int(item["x"] + text_w / 2),
            int(item["y"] + text_h / 2),
        )
        if any(_boxes_overlap(candidate, placed) for placed in placed_boxes):
            continue

        placed_boxes.append(
            _draw_label(draw, item["name"], (item["x"], item["y"]), font, seg_image.size)
        )

    return Image.alpha_composite(seg_image.convert("RGBA"), overlay).convert("RGB")


def _blend_segmentation(original_image, seg_image, opacity=0.5):
    """Blend the segmentation mask over the original image."""
    return Image.blend(original_image.convert("RGB"), seg_image.convert("RGB"), opacity)


def save_segmentation_visualization(image_source, segmentation, gvi, output_path):
    """
    保存分割可视化结果

    将原始图像、50% 透明分割叠加图、语义分割结果上下拼接显示。

    Args:
        image_source (str or PIL.Image.Image): 原始图像路径或预处理后的图像
        segmentation (torch.Tensor or np.ndarray): 分割结果（类别ID数组）
        gvi (float): 绿视指数值 (0-1)
        output_path (str): 输出图像保存路径

    Returns:
        None
    """
    if isinstance(image_source, Image.Image):
        original_image = image_source.convert("RGB")
    else:
        with Image.open(image_source) as img:
            original_image = img.convert("RGB")

    colored_segmentation = segmentation_to_color(segmentation)
    seg_image = Image.fromarray(colored_segmentation)

    if seg_image.size != original_image.size:
        seg_image = seg_image.resize(original_image.size, Image.NEAREST)

    overlay_image = _annotate_segmentation(
        _blend_segmentation(original_image, seg_image, opacity=0.5),
        segmentation,
    )
    seg_image = _annotate_segmentation(seg_image, segmentation)

    width, height = original_image.size
    separator_height = max(8, min(16, height // 80))
    combined = Image.new(
        "RGB",
        (width, height * 3 + separator_height * 2),
        (255, 255, 255),
    )
    combined.paste(original_image, (0, 0))
    combined.paste(overlay_image, (0, height + separator_height))
    combined.paste(seg_image, (0, height * 2 + separator_height * 2))

    combined.save(output_path, "PNG")
