"""
SimpleGVI Configuration Module
Centralized configuration for the Green View Index application
"""

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

# Vegetation class information with colors
ADE20K_CLASS_INFO: Dict[int, Dict[str, Any]] = {
    4: {"name": "tree", "color": [120, 120, 120]},
    9: {"name": "grass", "color": [120, 120, 80]},
    17: {"name": "plant", "color": [120, 120, 70]},
    66: {"name": "flower", "color": [0, 255, 133]},
    72: {"name": "palm", "color": [0, 82, 255]},
}

# Display names for vegetation classes
VEGETATION_NAMES: List[str] = ["tree", "grass", "plant", "flower", "palm"]

# Consistent green tones for vegetation visualization
VEGETATION_COLORS: List[List[int]] = [
    [0, 150, 0],  # medium green for trees
    [0, 200, 0],  # bright green for grass
    [0, 170, 0],  # mid-green for plants
    [0, 180, 0],  # green for flowers
    [0, 160, 0],  # green for palm trees
]

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
