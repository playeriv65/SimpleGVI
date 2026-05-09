import numpy as np

from config.settings import (
    ADE20K_CLASS_INFO,
    ADE20K_VEGETATION_CLASSES,
    INACTIVE_VEGETATION_COLOR,
)


def get_class_info(class_id):
    if class_id in ADE20K_CLASS_INFO:
        return ADE20K_CLASS_INFO[class_id]["color"], ADE20K_CLASS_INFO[class_id]["name"]
    return [0, 0, 0], "void"


def is_vegetation_class(class_id):
    return class_id in ADE20K_VEGETATION_CLASSES


def get_ade20k_color_palette():
    palette = []
    for class_id in range(150):
        palette.append(ADE20K_CLASS_INFO.get(class_id, {"color": [0, 0, 0]})["color"])
    return palette


def convert_to_vegetation_visualization(segmentation, selected_classes=None):
    segmentation = np.asarray(segmentation)
    h, w = segmentation.shape
    rgb = np.zeros((h, w, 3), dtype=np.uint8)
    palette = get_ade20k_color_palette()

    if selected_classes is None:
        selected_classes = set(ADE20K_VEGETATION_CLASSES)

    for class_id, color in enumerate(palette):
        mask = segmentation == class_id
        if not mask.any():
            continue

        if class_id in ADE20K_VEGETATION_CLASSES and class_id not in selected_classes:
            rgb[mask] = INACTIVE_VEGETATION_COLOR
        else:
            rgb[mask] = color

    return rgb
