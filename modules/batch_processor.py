import os
import glob
import pandas as pd
from tqdm import tqdm

from modules.gvi_calculator import process_image, get_models
from modules.visualization import save_segmentation_visualization

def process_image_folder(folder_path, output_dir, save_segmentation=False, is_panoramic=False):
    """
    处理文件夹中的所有图像并计算GVI
    
    参数:
        folder_path (str): 包含图像的文件夹路径
        output_dir (str): 输出结果的文件夹路径
        save_segmentation (bool): 是否保存分割结果
        is_panoramic (bool): 图像是否为全景图
    
    返回值:
        pandas.DataFrame: 包含所有图像GVI结果的数据框
    """
    # 确保输出目录存在
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    # 支持的图像格式
    image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.bmp', '*.tif', '*.tiff']
    image_files = []
    
    # 获取所有支持格式的图像文件
    for ext in image_extensions:
        image_files.extend(glob.glob(os.path.join(folder_path, ext)))
        if os.name != 'nt': # 在非Windows系统上处理大写扩展名
            image_files.extend(glob.glob(os.path.join(folder_path, ext.upper())))
    
    # 去重并过滤掉可能已经生成的分割结果图
    image_files = list(set(image_files))
    image_files = [f for f in image_files if "_segmentation.png" not in f]
    
    if not image_files:
        print(f"在 {folder_path} 未找到图像文件")
        return None
    
    # 加载模型（只加载一次）
    print("加载语义分割模型...")
    processor, model = get_models()
    
    # 存储结果的列表
    results = []
    
    # 处理每个图像文件
    for image_path in tqdm(image_files, desc="处理图像"):
        image_name = os.path.basename(image_path)
        try:
            # 处理图像
            gvi, segmentation = process_image(image_path, is_panoramic, processor, model)
            
            # 将结果添加到列表中
            results.append({
                'image_name': image_name,
                'image_path': image_path,
                'GVI': gvi
            })
            
            # 如果需要，保存分割可视化结果
            if save_segmentation:
                out_name = os.path.splitext(image_name)[0] + '_segmentation.png'
                save_segmentation_visualization(
                    image_path,
                    segmentation,
                    gvi,
                    os.path.join(output_dir, out_name)
                )
        except Exception as e:
            print(f"处理 {image_name} 时出错: {e}")
    
    # 创建DataFrame并保存为CSV
    df = pd.DataFrame(results)
    csv_path = os.path.join(output_dir, 'gvi_results.csv')
    df.to_csv(csv_path, index=False, encoding='utf-8-sig')
    print(f"结果已保存到 {csv_path}")
    
    # 计算平均GVI
    avg_gvi = df['GVI'].mean()
    print(f"平均绿视指数: {avg_gvi:.4f}")
    
    return df
