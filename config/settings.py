"""
SimpleGVI Configuration Module
Centralized configuration for the Green View Index application
"""

import csv
from pathlib import Path
from typing import Dict, List, Set, Any
import torch

# ADE20K dataset vegetation class mappings
# Based on Hugging Face model: facebook/mask2former-swin-large-ade-semantic
# Reference: https://huggingface.co/facebook/mask2former-swin-large-ade-semantic

# Vegetation class IDs according to ADE20K labeling convention
ADE20K_VEGETATION_CLASSES: Set[int] = {
    4,
    9,
    17,
    66,
    72,
}  # tree, grass, plant, flower, palm

ADE20K_COLOR_CSV = Path(__file__).resolve().with_name("ade20k_colors.csv")


def _parse_rgb(value: str) -> List[int]:
    """Parse an ADE20K RGB tuple string such as '(120, 120, 120)'."""
    return [int(part.strip()) for part in value.strip().strip('"()').split(",")]


def _load_ade20k_class_info() -> Dict[int, Dict[str, Any]]:
    """Load ADE20K's official 150-class color table from the bundled CSV."""
    class_info: Dict[int, Dict[str, Any]] = {}
    with ADE20K_COLOR_CSV.open("r", encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            class_id = int(row["Idx"]) - 1
            class_info[class_id] = {
                "name": row["Name"].split(";")[0],
                "color": _parse_rgb(row["Color_Code (R,G,B)"]),
            }
    return class_info


ADE20K_CLASS_INFO: Dict[int, Dict[str, Any]] = _load_ade20k_class_info()

# Display names for vegetation classes
VEGETATION_NAMES: List[str] = ["tree", "grass", "plant", "flower", "palm"]

VEGETATION_COLORS: List[List[int]] = [
    ADE20K_CLASS_INFO[class_id]["color"]
    for class_id in sorted(ADE20K_VEGETATION_CLASSES)
]

# Inactive color for unselected vegetation classes
INACTIVE_VEGETATION_COLOR: List[int] = [200, 200, 200]

# Model configuration
MODEL_CONFIG: Dict[str, Any] = {
    "model_name": "facebook/mask2former-swin-large-ade-semantic",
    "device": torch.device("cuda" if torch.cuda.is_available() else "cpu"),
    "use_fast_processor": True,
}


def get_vegetation_classes() -> Set[int]:
    """Get the set of vegetation class IDs used in GVI calculation."""
    return ADE20K_VEGETATION_CLASSES


def get_vegetation_colors() -> List[List[int]]:
    """Get the colors used for vegetation in visualizations."""
    return VEGETATION_COLORS


def get_vegetation_names() -> List[str]:
    """Get the names of vegetation classes."""
    return VEGETATION_NAMES


def get_class_info(class_id: int) -> Dict[str, Any]:
    """Get information about a specific ADE20K class."""
    return ADE20K_CLASS_INFO.get(
        class_id, {"name": "unknown", "color": [128, 128, 128]}
    )


def is_vegetation_class(class_id: int) -> bool:
    """Check if a given class ID represents vegetation."""
    return class_id in ADE20K_VEGETATION_CLASSES


def get_model_config() -> Dict[str, Any]:
    """Get the model configuration."""
    return MODEL_CONFIG
