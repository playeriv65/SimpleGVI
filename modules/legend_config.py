import numpy as np

try:
    from config.settings import (
        ADE20K_VEGETATION_CLASSES,
        ADE20K_CLASS_INFO,
        get_vegetation_colors,
        VEGETATION_COLORS,
    )
except ImportError:
    ADE20K_CLASS_INFO = {
        0: {"name": "wall", "color": [120, 120, 120]},
        1: {"name": "building", "color": [180, 120, 120]},
        2: {"name": "sky", "color": [6, 230, 230]},
        3: {"name": "floor", "color": [140, 140, 200]},
        4: {"name": "tree", "color": [140, 140, 140]},
        5: {"name": "ceiling", "color": [204, 5, 255]},
        6: {"name": "road", "color": [230, 230, 230]},
        7: {"name": "bed", "color": [4, 230, 0]},
        8: {"name": "window", "color": [240, 240, 240]},
        9: {"name": "grass", "color": [120, 120, 80]},
        10: {"name": "cabinet", "color": [140, 140, 140]},
        11: {"name": "sidewalk", "color": [204, 5, 255]},
        12: {"name": "person", "color": [230, 230, 230]},
        13: {"name": "earth", "color": [4, 200, 255]},
        14: {"name": "door", "color": [224, 5, 255]},
        15: {"name": "table", "color": [235, 255, 7]},
        16: {"name": "mountain", "color": [150, 5, 61]},
        17: {"name": "plant", "color": [120, 120, 70]},
        18: {"name": "curtain", "color": [8, 255, 51]},
        19: {"name": "chair", "color": [255, 6, 82]},
        20: {"name": "car", "color": [204, 70, 3]},
        21: {"name": "water", "color": [0, 102, 200]},
        22: {"name": "painting", "color": [61, 230, 250]},
        23: {"name": "sofa", "color": [255, 6, 51]},
        24: {"name": "shelf", "color": [11, 102, 255]},
        25: {"name": "house", "color": [255, 7, 71]},
        26: {"name": "sea", "color": [255, 9, 224]},
        27: {"name": "mirror", "color": [9, 7, 230]},
        28: {"name": "rug", "color": [220, 220, 220]},
        29: {"name": "field", "color": [255, 9, 92]},
        30: {"name": "armchair", "color": [112, 9, 255]},
        31: {"name": "seat", "color": [8, 255, 214]},
        32: {"name": "fence", "color": [7, 255, 224]},
        33: {"name": "desk", "color": [255, 184, 6]},
        34: {"name": "rock", "color": [10, 255, 71]},
        35: {"name": "wardrobe", "color": [255, 41, 10]},
        36: {"name": "lamp", "color": [7, 255, 255]},
        37: {"name": "bathtub", "color": [224, 255, 8]},
        38: {"name": "railing", "color": [102, 8, 255]},
        39: {"name": "cushion", "color": [255, 61, 6]},
        40: {"name": "base", "color": [255, 194, 7]},
        41: {"name": "box", "color": [255, 122, 8]},
        42: {"name": "column", "color": [0, 255, 20]},
        43: {"name": "signboard", "color": [255, 8, 41]},
        44: {"name": "chest", "color": [255, 5, 153]},
        45: {"name": "counter", "color": [6, 51, 255]},
        46: {"name": "sand", "color": [235, 12, 255]},
        47: {"name": "sink", "color": [160, 150, 20]},
        48: {"name": "skyscraper", "color": [0, 163, 255]},
        49: {"name": "fireplace", "color": [140, 140, 140]},
        50: {"name": "refrigerator", "color": [250, 10, 15]},
        51: {"name": "grandstand", "color": [20, 255, 0]},
        52: {"name": "path", "color": [31, 255, 0]},
        53: {"name": "stairs", "color": [255, 31, 0]},
        54: {"name": "runway", "color": [255, 224, 0]},
        55: {"name": "case", "color": [153, 255, 0]},
        56: {"name": "pool", "color": [0, 0, 255]},
        57: {"name": "pillow", "color": [255, 71, 0]},
        58: {"name": "screen_door", "color": [0, 235, 255]},
        59: {"name": "stairway", "color": [0, 173, 255]},
        60: {"name": "river", "color": [31, 0, 255]},
        61: {"name": "bridge", "color": [11, 200, 200]},
        62: {"name": "bookcase", "color": [255, 82, 0]},
        63: {"name": "blind", "color": [0, 255, 245]},
        64: {"name": "coffee_table", "color": [0, 61, 255]},
        65: {"name": "toilet", "color": [0, 255, 112]},
        66: {"name": "flower", "color": [0, 255, 133]},
        67: {"name": "book", "color": [255, 0, 0]},
        68: {"name": "hill", "color": [255, 163, 0]},
        69: {"name": "bench", "color": [204, 255, 0]},
        70: {"name": "countertop", "color": [0, 143, 255]},
        71: {"name": "stove", "color": [51, 255, 0]},
        72: {"name": "palm", "color": [0, 82, 255]},
    }
    ADE20K_VEGETATION_CLASSES = {4, 9, 17, 66, 72}

    def get_vegetation_colors():
        return [
            [0, 150, 0],
            [0, 200, 0],
            [0, 170, 0],
            [0, 180, 0],
            [0, 160, 0],
        ]


def get_class_info(class_id):
    if class_id in ADE20K_CLASS_INFO:
        return ADE20K_CLASS_INFO[class_id]["color"], ADE20K_CLASS_INFO[class_id]["name"]
    return [0, 0, 0], "void"


def is_vegetation_class(class_id):
    return class_id in ADE20K_VEGETATION_CLASSES


def get_ade20k_color_palette():
    max_idx = max(ADE20K_CLASS_INFO.keys()) if ADE20K_CLASS_INFO else 0
    palette = []
    for i in range(max_idx + 1):
        if i in ADE20K_CLASS_INFO:
            palette.append(ADE20K_CLASS_INFO[i]["color"])
        else:
            palette.append([0, 0, 0])
    while len(palette) < 150:
        palette.append([0, 0, 0])
    return palette[:150]


def convert_to_vegetation_visualization(segmentation):
    h, w = segmentation.shape
    rgb = np.zeros((h, w, 3), dtype=np.uint8)
    vegetation_colors_list = get_vegetation_colors()
    vegetation_color_map = {}
    for i, veg_id in enumerate(sorted(list(ADE20K_VEGETATION_CLASSES))):
        vegetation_color_map[veg_id] = vegetation_colors_list[
            i % len(vegetation_colors_list)
        ]
    for class_id in range(min(150, len(get_ade20k_color_palette()))):
        mask = segmentation == class_id
        if mask.any():
            if class_id in ADE20K_VEGETATION_CLASSES:
                color = vegetation_color_map[class_id]
                rgb[mask] = color
            else:
                if class_id < len(get_ade20k_color_palette()):
                    color = get_ade20k_color_palette()[class_id]
                    rgb[mask] = color
    return rgb
