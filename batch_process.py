import os
import argparse
import logging
from modules.batch_processor import process_image_folder
from modules.resource_manager import get_optimal_workers, print_resource_info

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BANNER = """
╔═══════════════════════════════════════════════════════════════╗
║                    SimpleGVI 批量处理工具                      ║
║                   计算图像的绿视指数 (GVI)                      ║
╚═══════════════════════════════════════════════════════════════╝
"""

USAGE_EXAMPLES = """
使用示例:
  # 自动并行处理（推荐）
  batch_process.py images/

  # 保存分割结果
  batch_process.py images/ -s

  # 指定并行数
  batch_process.py images/ -w 4

  # 串行处理
  batch_process.py images/ -S

  # 查看系统资源
  batch_process.py --info

  # 自定义资源比率（高级）
  batch_process.py images/ --gpu-ratio 0.9 --cpu-ratio 0.8
"""


def print_help():
    """打印详细帮助信息"""
    print(BANNER)
    print("""
功能说明:
  批量处理图像文件夹，计算每张图像的绿视指数(Green View Index, GVI)。
  支持自动并行处理，根据系统资源智能决定并发数。

参数说明:
  folder_path           包含图像的文件夹路径

选项:
  -o, --output_dir      输出目录（默认: results）
  -s, --save_segmentation  保存分割可视化结果
  -p, --is_panoramic    全景图模式
  -w, --workers         并行数（默认: auto，可选: auto/数字）
  -S, --sequential      串行处理（关闭并行）
  --info                显示系统资源信息
  --help                显示此帮助信息

高级选项:
  --gpu-ratio           GPU显存使用比率（默认: 0.8）
  --cpu-ratio           CPU内存使用比率（默认: 0.7）
  --reserve-mb          预留内存MB（默认: 1024）
""")
    print(USAGE_EXAMPLES)


def main():
    """批量处理图像文件夹，计算每个图像的绿视指数(GVI)"""
    parser = argparse.ArgumentParser(
        description="批量计算图像的绿视指数(Green View Index, GVI)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=USAGE_EXAMPLES
    )
    parser.add_argument("folder_path", nargs='?', help="包含图像的文件夹路径")
    parser.add_argument("-o", "--output_dir", default="results", help="输出目录（默认: results）")
    parser.add_argument("-s", "--save_segmentation", action="store_true", help="保存分割可视化结果")
    parser.add_argument("-p", "--is_panoramic", action="store_true", help="全景图模式")
    parser.add_argument("-w", "--workers", type=str, default="auto",
                        help="并行数（默认: auto，可选: auto/数字）")
    parser.add_argument("-S", "--sequential", action="store_true", help="串行处理")
    parser.add_argument("--info", action="store_true", help="显示系统资源信息")
    parser.add_argument("--gpu-ratio", type=float, default=0.8, help=argparse.SUPPRESS)
    parser.add_argument("--cpu-ratio", type=float, default=0.7, help=argparse.SUPPRESS)
    parser.add_argument("--reserve-mb", type=int, default=1024, help=argparse.SUPPRESS)
    args = parser.parse_args()

    if args.info:
        print_resource_info()
        return

    if not args.folder_path:
        print_help()
        return

    use_parallel = not args.sequential

    if args.workers == "auto":
        max_workers = get_optimal_workers(
            gpu_memory_ratio=args.gpu_ratio,
            cpu_memory_ratio=args.cpu_ratio,
            reserve_memory_mb=args.reserve_mb
        )
    else:
        try:
            max_workers = int(args.workers)
        except ValueError:
            logger.error(f"无效的workers参数: {args.workers}，应为数字或'auto'")
            return

    if not os.path.exists(args.folder_path):
        logger.error(f"文件夹 '{args.folder_path}' 不存在")
        return

    logger.info(f"开始处理: {args.folder_path}")
    logger.info(f"模式: {'并行' if use_parallel else '串行'}, 并行数: {max_workers}")

    df = process_image_folder(
        args.folder_path,
        args.output_dir,
        args.save_segmentation,
        args.is_panoramic,
        use_parallel=use_parallel,
        max_workers=max_workers
    )

    if df is not None:
        logger.info(f"处理完成! 共处理 {len(df)} 张图像")
    else:
        logger.warning("未处理任何图像")


if __name__ == "__main__":
    main()
