import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import torch

# 颜色调色板，将每个类映射到RGB值
color_palette = [
    [128, 64, 128],  # 0: road - 道路
    [244, 35, 232],  # 1: sidewalk - 人行道
    [70, 70, 70],    # 2: building - 建筑
    [102, 102, 156], # 3: wall - 墙
    [190, 153, 153], # 4: fence - 围栏
    [153, 153, 153], # 5: pole - 杆
    [250, 170, 30],  # 6: traffic light - 交通灯
    [220, 220, 0],   # 7: traffic sign - 交通标志
    [0, 255, 0],     # 8: vegetation - 植被
    [152, 251, 152], # 9: terrain - 地形
    [70, 130, 180],  # 10: sky - 天空
    [220, 20, 60],   # 11: person - 人
    [255, 0, 0],     # 12: rider - 骑手
    [0, 0, 142],     # 13: car - 汽车
    [0, 0, 70],      # 14: truck - 卡车
    [0, 60, 100],    # 15: bus - 公交车
    [0, 80, 100],    # 16: train - 火车
    [0, 0, 230],     # 17: motorcycle - 摩托车
    [119, 11, 32]    # 18: bicycle - 自行车
]

def segmentation_to_color(segmentation_tensor):
    """
    将分割张量转换为RGB彩色图像
    
    参数:
        segmentation_tensor (torch.Tensor): 分割结果张量
        
    返回值:
        numpy.ndarray: RGB彩色图像
    """
    if isinstance(segmentation_tensor, torch.Tensor):
        segmentation_array = segmentation_tensor.numpy()
    else:
        segmentation_array = segmentation_tensor
    
    # 创建一个空的RGB图像
    height, width = segmentation_array.shape
    colored_segmentation = np.zeros((height, width, 3), dtype=np.uint8)
    
    # 为每个类别分配颜色
    for class_idx, color in enumerate(color_palette):
        mask = segmentation_array == class_idx
        colored_segmentation[mask] = color
    
    return colored_segmentation

def save_segmentation_visualization(image_path, segmentation, gvi, output_path):
    """
    保存分割可视化结果 (使用 PIL 以规避 Matplotlib 的 libpng 警告)
    
    参数:
        image_path (str): 原始图像路径
        segmentation (torch.Tensor): 分割结果
        gvi (float): 绿视指数
        output_path (str): 输出图像路径
    """
    # 打开原始图像并转换为RGB
    with Image.open(image_path) as img:
        original_image = img.convert("RGB")
    
    # 将分割转换为彩色图像
    colored_segmentation = segmentation_to_color(segmentation)
    seg_image = Image.fromarray(colored_segmentation)
    
    # 确保尺寸一致
    if seg_image.size != original_image.size:
        seg_image = seg_image.resize(original_image.size, Image.NEAREST)
    
    # 创建并排对比图
    width, height = original_image.size
    combined = Image.new("RGB", (width * 2, height + 60), (255, 255, 255))
    combined.paste(original_image, (0, 60))
    combined.paste(seg_image, (width, 60))
    
    # 添加文字说明
    draw = ImageDraw.Draw(combined)
    try:
        # 尝试加载系统字体 (Windows 常用路径)
        font_path = "C:\\Windows\\Fonts\\msyh.ttc" # 微软雅黑
        if not os.path.exists(font_path):
            font_path = "C:\\Windows\\Fonts\\simhei.ttf" # 黑体
        
        font_title = ImageFont.truetype(font_path, 30)
        font_text = ImageFont.truetype(font_path, 20)
    except:
        # 如果失败则使用默认字体
        font_title = ImageFont.load_default()
        font_text = ImageFont.load_default()
    
    title = f"绿视指数分析 (GVI: {gvi:.4f})"
    draw.text((10, 10), title, fill=(0, 0, 0), font=font_title)
    draw.text((10, height + 30), "原始图像", fill=(0, 0, 0), font=font_text)
    draw.text((width + 10, height + 30), f"分割结果 (GVI: {gvi:.4f})", fill=(0, 0, 0), font=font_text)
    
    # 保存图像，显式不带任何元数据
    combined.save(output_path, "PNG", icc_profile=None)
