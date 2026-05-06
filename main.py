import os
import argparse
from modules.gvi_calculator import process_image, get_models

BANNER = """
╔═══════════════════════════════════════════════════════════════╗
║                    SimpleGVI 单图处理工具                      ║
║                   计算图像的绿视指数 (GVI)                      ║
╚═══════════════════════════════════════════════════════════════╝
"""

USAGE_EXAMPLES = """
使用示例:
  # 处理单张图像
  main.py image.jpg

  # 保存分割结果
  main.py image.jpg -s

  # 指定输出目录
  main.py image.jpg -o output/

  # 处理全景图
  main.py panorama.jpg -p
"""


def main():
    """计算图像的绿视指数 (Green View Index, GVI)"""
    parser = argparse.ArgumentParser(
        description="计算图像的绿视指数 (Green View Index, GVI)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=USAGE_EXAMPLES
    )
    parser.add_argument("image_path", nargs='?', help="输入图像的路径")
    parser.add_argument("-o", "--output_dir", default="results", help="输出目录（默认: results）")
    parser.add_argument("-s", "--save_segmentation", action="store_true", help="保存语义分割结果")
    parser.add_argument("-p", "--is_panoramic", action="store_true", help="全景图模式")
    args = parser.parse_args()

    if not args.image_path:
        print(BANNER)
        print("""
功能说明:
  处理单张图像，计算绿视指数(Green View Index, GVI)。
  使用 Mask2Former 模型进行语义分割，识别植被区域。

参数说明:
  image_path            输入图像的路径

选项:
  -o, --output_dir      输出目录（默认: results）
  -s, --save_segmentation  保存分割可视化结果
  -p, --is_panoramic    全景图模式
  -h, --help            显示帮助信息
""")
        print(USAGE_EXAMPLES)
        return

    if not os.path.exists(args.image_path):
        print(f"错误: 图像文件 '{args.image_path}' 不存在")
        return

    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)

    print("加载语义分割模型...")
    processor, model = get_models()

    print(f"处理图像：{args.image_path}")
    image_name = os.path.basename(args.image_path).split(".")[0]
    gvi, segmentation, processed_image = process_image(
        args.image_path, args.is_panoramic, processor, model
    )

    print(f"绿视指数 (GVI): {gvi:.4f}")

    with open(
        os.path.join(args.output_dir, f"{image_name}_result.txt"), "w", encoding="utf-8"
    ) as f:
        f.write(f"图像：{args.image_path}\n")
        f.write(f"绿视指数 (GVI): {gvi:.4f}\n")

    if args.save_segmentation:
        from modules.visualization import save_segmentation_visualization

        output_path = os.path.join(args.output_dir, f"{image_name}_segmentation.png")
        save_segmentation_visualization(
            args.image_path,
            segmentation,
            gvi,
            output_path,
        )
        print(f"分割结果已保存: {output_path}")

    print("处理完成!")


if __name__ == "__main__":
    main()
