import os
import argparse
from modules.gvi_calculator import process_image, get_models


def main():
    """
    计算图像的绿视指数(Green View Index, GVI)
    """
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="计算图像的绿视指数(Green View Index, GVI)")
    parser.add_argument("image_path", help="输入图像的路径")
    parser.add_argument("--output_dir", "-o", default="results", help="输出结果的文件夹")
    parser.add_argument("--save_segmentation", "-s", action="store_true", help="是否保存语义分割结果")
    parser.add_argument("--is_panoramic", "-p", action="store_true", help="图像是否为全景图")
    args = parser.parse_args()

    # 确保输出目录存在
    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)
        
    # 加载模型
    print("加载语义分割模型...")
    processor, model = get_models()
    
    # 处理图像并计算GVI
    print(f"处理图像: {args.image_path}")
    image_name = os.path.basename(args.image_path).split('.')[0]
    gvi, segmented_image = process_image(
        args.image_path, 
        args.is_panoramic, 
        processor, 
        model
    )
    
    # 输出GVI结果
    print(f"绿视指数(GVI): {gvi:.4f}")
    
    # 保存结果
    with open(os.path.join(args.output_dir, f"{image_name}_result.txt"), "w", encoding="utf-8") as f:
        f.write(f"图像: {args.image_path}\n")
        f.write(f"绿视指数(GVI): {gvi:.4f}\n")
    
    # 如果需要，保存分割图像
    if args.save_segmentation:
        from modules.visualization import save_segmentation_visualization
        save_segmentation_visualization(
            args.image_path,
            segmented_image,
            gvi,
            os.path.join(args.output_dir, f"{image_name}_segmentation.png")
        )
        print(f"分割可视化结果已保存到: {os.path.join(args.output_dir, f'{image_name}_segmentation.png')}")
    
    print("处理完成!")


if __name__ == "__main__":
    main()
