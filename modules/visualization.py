import os
import platform
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage
import torch
from modules.legend_config import (
    get_ade20k_color_palette,
    convert_to_vegetation_visualization,
)
from config.settings import ADE20K_CLASS_INFO, ADE20K_VEGETATION_CLASSES

ADE20K_COLOR_PALETTE = get_ade20k_color_palette()
VEGETATION_CLASS_IDS = ADE20K_VEGETATION_CLASSES
LABEL_PAD_X = 4
LABEL_PAD_Y = 3


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


def _text_metrics(draw, text, font):
    bbox = _text_bbox(draw, (0, 0), text, font)
    return bbox, bbox[2] - bbox[0], bbox[3] - bbox[1]


def _label_box(
    draw, text, center, font, image_size, pad_x=LABEL_PAD_X, pad_y=LABEL_PAD_Y
):
    width, height = image_size
    x, y = center
    bbox, text_w, text_h = _text_metrics(draw, text, font)

    left = int(round(x - text_w / 2 - pad_x))
    top = int(round(y - text_h / 2 - pad_y))
    right = left + text_w + pad_x * 2
    bottom = top + text_h + pad_y * 2

    left = max(0, min(left, width - (right - left)))
    top = max(0, min(top, height - (bottom - top)))
    right = left + text_w + pad_x * 2
    bottom = top + text_h + pad_y * 2

    return bbox, (left, top, right, bottom)


def _draw_label(draw, text, center, font, image_size):
    """Draw a compact label centered at the given point."""
    bbox, label_box = _label_box(draw, text, center, font, image_size)
    left, top, right, bottom = label_box

    draw.rounded_rectangle(
        label_box,
        radius=2,
        fill=(0, 0, 0, 155),
        outline=(255, 255, 255, 170),
        width=1,
    )
    text_x = left + LABEL_PAD_X - bbox[0]
    text_y = top + LABEL_PAD_Y - bbox[1]
    draw.text((text_x, text_y), text, fill=(255, 255, 255, 245), font=font)
    return (left, top, right, bottom)


def _boxes_overlap(a, b, margin=4):
    return not (
        a[2] + margin < b[0]
        or b[2] + margin < a[0]
        or a[3] + margin < b[1]
        or b[3] + margin < a[1]
    )


def _choose_component_font(
    draw,
    text,
    component_area,
    component_box,
    image_height,
    min_component_label_area_ratio,
):
    min_font_size = 11
    max_font_size = max(min_font_size, min(42, int(np.sqrt(component_area) / 14)))
    y0, x0, y1, x1 = component_box
    component_w = x1 - x0
    component_h = y1 - y0

    for font_size in range(max_font_size, min_font_size - 1, -1):
        font = _load_font(font_size)
        _, text_w, text_h = _text_metrics(draw, text, font)
        label_w = text_w + LABEL_PAD_X * 2
        label_h = text_h + LABEL_PAD_Y * 2
        label_area = label_w * label_h
        if component_area < label_area * min_component_label_area_ratio:
            continue
        if component_w < label_w * 1.1 or component_h < label_h * 1.1:
            continue
        return font

    return None


def _annotate_segmentation(
    seg_image,
    segmentation,
    min_area_ratio=0.0002,
    max_labels=24,
    min_component_label_area_ratio=8,
):
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

    total_pixels = segmentation.size
    min_area = max(80, int(total_pixels * min_area_ratio))
    labels = []

    class_ids = np.unique(segmentation)
    structure = np.ones((3, 3), dtype=np.uint8)
    for class_id in class_ids.tolist():
        if class_id not in ADE20K_CLASS_INFO:
            continue

        mask = segmentation == class_id
        labeled_components, component_count = ndimage.label(mask, structure=structure)
        if component_count == 0:
            continue

        component_slices = ndimage.find_objects(labeled_components)
        for component_id, component_slice in enumerate(component_slices, start=1):
            if component_slice is None:
                continue

            y_slice, x_slice = component_slice
            component_mask = labeled_components[component_slice] == component_id
            component_area = int(component_mask.sum())
            if component_area < min_area:
                continue

            name = ADE20K_CLASS_INFO[class_id]["name"]
            component_box = (y_slice.start, x_slice.start, y_slice.stop, x_slice.stop)
            font = _choose_component_font(
                draw,
                name,
                component_area,
                component_box,
                seg_image.height,
                min_component_label_area_ratio,
            )
            if font is None:
                continue

            ys, xs = np.nonzero(component_mask)
            labels.append(
                {
                    "area": component_area,
                    "name": name,
                    "font": font,
                    "x": float(np.median(xs + x_slice.start)),
                    "y": float(np.median(ys + y_slice.start)),
                }
            )

    labels.sort(key=lambda item: item["area"], reverse=True)
    placed_boxes = []
    for item in labels:
        if len(placed_boxes) >= max_labels:
            break

        _, candidate = _label_box(
            draw,
            item["name"],
            (item["x"], item["y"]),
            item["font"],
            seg_image.size,
        )
        if any(_boxes_overlap(candidate, placed) for placed in placed_boxes):
            continue

        placed_boxes.append(
            _draw_label(
                draw,
                item["name"],
                (item["x"], item["y"]),
                item["font"],
                seg_image.size,
            )
        )

    return Image.alpha_composite(seg_image.convert("RGBA"), overlay).convert("RGB")


def _blend_segmentation(original_image, seg_image, opacity=0.5):
    """Blend the segmentation mask over the original image."""
    return Image.blend(original_image.convert("RGB"), seg_image.convert("RGB"), opacity)


def save_segmentation_visualization(image_source, segmentation, gvi, output_path):
    """
    保存分割可视化结果

    将显示图像、50% 透明分割叠加图、语义分割结果上下拼接显示。

    Args:
        image_source (str or PIL.Image.Image): 显示图像路径或 PIL 图像
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
