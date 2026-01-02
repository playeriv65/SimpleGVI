import torch
import warnings
from transformers import AutoImageProcessor, Mask2FormerForUniversalSegmentation
from PIL import Image
import numpy as np

# 忽略 transformers 库中关于无效参数的警告
warnings.filterwarnings("ignore", message=".*The following named arguments are not valid for `Mask2FormerImageProcessor.__init__`.*")

def get_models():
    """
    加载预训练的语义分割模型
    
    返回值:
        tuple: (processor, model) 图像处理器和语义分割模型
    """
    # 加载预训练的AutoImageProcessor
    processor = AutoImageProcessor.from_pretrained(
        "facebook/mask2former-swin-large-cityscapes-semantic",
        use_fast=True
    )
    # 设置设备为GPU（如果可用），否则使用CPU
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    # 加载预训练的Mask2FormerForUniversalSegmentation模型
    model = Mask2FormerForUniversalSegmentation.from_pretrained("facebook/mask2former-swin-large-cityscapes-semantic")
    # 将模型移动到指定设备（GPU或CPU）
    model = model.to(device)
    # 返回处理器和模型
    return processor, model

def segment_image(image, processor, model):
    """
    对输入图像进行语义分割
    
    参数:
        image (PIL.Image): 输入图像
        processor: 图像预处理器
        model: 语义分割模型
    
    返回值:
        torch.Tensor: 语义分割结果
    """
    # 使用图像处理器预处理图像
    inputs = processor(images=image, return_tensors="pt")
    
    # 通过模型进行前向传播以获得分割结果
    with torch.no_grad():
        # 检查是否有GPU可用
        if torch.cuda.is_available():
            # 将输入移至GPU
            inputs = {k: v.to('cuda') for k, v in inputs.items()}
            # 通过模型进行前向传播
            outputs = model(**inputs)
            # 使用处理器后处理语义分割输出并将结果移至CPU
            segmentation = processor.post_process_semantic_segmentation(outputs, target_sizes=[image.size[::-1]])[0].to('cpu')
        else:
            # 通过模型进行前向传播
            outputs = model(**inputs)
            # 使用处理器后处理语义分割输出
            segmentation = processor.post_process_semantic_segmentation(outputs, target_sizes=[image.size[::-1]])[0]
            
    return segmentation

def calculate_gvi(segmentation):
    """
    计算分割图像的绿视指数(GVI)
    
    参数:
        segmentation (torch.Tensor): 语义分割结果
    
    返回值:
        float: 绿视指数，表示植被像素占总像素的比例
    """
    # 计算分割中的总像素数
    total_pixels = segmentation.numel()
    # 过滤表示植被（标签8）的像素并计数
    vegetation_pixels = (segmentation == 8).sum().item()
    
    # 计算分割中的绿色像素百分比
    return vegetation_pixels / total_pixels if total_pixels else 0

def process_panoramic_image(image, processor, model):
    """
    处理全景图像
    
    参数:
        image (PIL.Image): 输入的全景图像
        processor: 图像预处理器
        model: 语义分割模型
    
    返回值:
        tuple: (gvi, segmentation) 绿视指数和分割结果
    """
    # 获取图像尺寸
    width, height = image.size

    # 裁剪图像底部20%以去除全景图像底部的条带
    bottom_crop = int(height * 0.2)
    image = image.crop((0, 0, width, height - bottom_crop))

    # 对图像应用语义分割
    segmentation = segment_image(image, processor, model)
    
    # 将全景图像分为4个等宽部分
    w4 = int(width / 4)
    h4 = int(height / 4)
    hFor43 = int(w4 * 3 / 4)
    
    segmentations = []
    
    # 裁剪全景图像的4个部分
    for w in range(4):
        x_begin = w * w4
        x_end = (w + 1) * w4
        cropped_segmentation = segmentation[h4:h4+hFor43, x_begin:x_end]
        segmentations.append(cropped_segmentation)
    
    # 计算绿视指数
    gvi = calculate_gvi_from_segmentations(segmentations)
    
    return gvi, segmentation

def calculate_gvi_from_segmentations(segmentations):
    """
    从多个分割结果计算平均绿视指数
    
    参数:
        segmentations (list): 分割结果列表
    
    返回值:
        float: 平均绿视指数
    """
    total_pixels = 0
    vegetation_pixels = 0
    
    for segment in segmentations:
        # 计算分割中的总像素数
        total_pixels += segment.numel()
        # 过滤表示植被（标签8）的像素并计数
        vegetation_pixels += (segment == 8).sum().item()
    
    # 计算分割中的绿色像素百分比
    return vegetation_pixels / total_pixels if total_pixels else 0

def process_image(image_path, is_panoramic, processor, model):
    """
    处理图像并计算绿视指数
    
    参数:
        image_path (str): 图像文件路径
        is_panoramic (bool): 是否为全景图像
        processor: 图像预处理器
        model: 语义分割模型
    
    返回值:
        tuple: (gvi, segmentation) 绿视指数和分割结果
    """
    # 打开图像
    image = Image.open(image_path)
    
    if is_panoramic:
        # 处理全景图像
        return process_panoramic_image(image, processor, model)
    else:
        # 处理普通图像
        segmentation = segment_image(image, processor, model)
        gvi = calculate_gvi(segmentation)
        return gvi, segmentation
