import os
import argparse
from modules.batch_processor import process_image_folder

def main():
    """
    批量处理图像文件夹，计算每个图像的绿视指数(GVI)
    """
    parser = argparse.ArgumentParser(description="批量计算图像的绿视指数(Green View Index, GVI)")
    parser.add_argument("folder_path", help="包含图像的文件夹路径")
    parser.add_argument("--output_dir", "-o", default="results", help="输出结果的文件夹路径")
    parser.add_argument("--save_segmentation", "-s", action="store_true", help="是否保存分割可视化结果")
    parser.add_argument("--is_panoramic", "-p", action="store_true", help="图像是否为全景图")
    args = parser.parse_args()
    
    # 确保文件夹路径存在
    if not os.path.exists(args.folder_path):
        print(f"错误: 文件夹 '{args.folder_path}' 不存在")
        return
        
    # 处理图像文件夹
    process_image_folder(
        args.folder_path,
        args.output_dir,
        args.save_segmentation,
        args.is_panoramic
    )
    
    print("批处理完成!")

if __name__ == "__main__":
    main()
