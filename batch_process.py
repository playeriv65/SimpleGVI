import argparse
import logging
import os

from modules.cli_utils import configure_utf8_output
from modules.batch_processor import process_image_folder
from modules.resource_manager import print_resource_info

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

BANNER = """
╔═══════════════════════════════════════════════════════════════╗
║                    SimpleGVI 批量处理工具                      ║
║                   计算图像的绿视指数 (GVI)                      ║
╚═══════════════════════════════════════════════════════════════╝
"""

USAGE_EXAMPLES = """
使用示例:
  # 批量处理（默认 batch size 1）
  batch_process.py images/

  # 保存分割结果
  batch_process.py images/ -s

  # 设置 GPU batch size
  batch_process.py images/ --batch-size 2

  # 查看系统资源
  batch_process.py --info
"""

def main():
    """批量处理图像文件夹，计算每个图像的绿视指数(GVI)"""
    configure_utf8_output()

    parser = argparse.ArgumentParser(
        description="批量计算图像的绿视指数(Green View Index, GVI)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=USAGE_EXAMPLES,
    )
    parser.add_argument("folder_path", nargs="?", help="包含图像的文件夹路径")
    parser.add_argument("-o", "--output_dir", default="results", help="输出目录（默认: results）")
    parser.add_argument("-s", "--save_segmentation", action="store_true", help="保存分割可视化结果")
    parser.add_argument("-p", "--is_panoramic", action="store_true", help="全景图模式")
    parser.add_argument(
        "-b",
        "--batch-size",
        type=int,
        default=1,
        help="GPU/CPU 推理批量大小（默认: 1）",
    )
    parser.add_argument("--info", action="store_true", help="显示系统资源信息")
    args = parser.parse_args()

    if args.info:
        print_resource_info()
        return

    if not args.folder_path:
        print(BANNER)
        print("""
功能说明:
  批量处理图像文件夹，计算每张图像的绿视指数(Green View Index, GVI)。
  只加载一份模型，按 batch size 将图像送入 GPU/CPU 推理。

参数说明:
  folder_path           包含图像的文件夹路径

选项:
  -o, --output_dir      输出目录（默认: results）
  -s, --save_segmentation  保存分割可视化结果
  -p, --is_panoramic    全景图模式
  -b, --batch-size      GPU/CPU 推理批量大小（默认: 1）
  --info                显示系统资源信息
  --help                显示此帮助信息
""")
        print(USAGE_EXAMPLES)
        return

    if args.batch_size < 1:
        logger.error("--batch-size 必须大于等于 1")
        raise SystemExit(1)

    if not os.path.exists(args.folder_path):
        logger.error(f"文件夹 '{args.folder_path}' 不存在")
        raise SystemExit(1)

    logger.info(f"开始处理: {args.folder_path}")
    logger.info(f"模式: batch 推理，batch size={args.batch_size}")

    df = process_image_folder(
        args.folder_path,
        args.output_dir,
        args.save_segmentation,
        args.is_panoramic,
        batch_size=args.batch_size,
    )

    if df is not None:
        if not df.empty and "error" in df.columns and df["error"].notna().any():
            failed = int(df["error"].notna().sum())
            logger.error(f"处理完成但有 {failed} 张图像失败")
            raise SystemExit(1)

        if df.empty:
            logger.warning("未处理任何图像")
            raise SystemExit(1)

        logger.info(f"处理完成! 共处理 {len(df)} 张图像")
    else:
        logger.warning("未处理任何图像")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
