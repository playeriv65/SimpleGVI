import os
import argparse
import logging
from modules.batch_processor import process_image_folder
from modules.resource_manager import print_resource_info, get_resource_monitor, ResourceConfig

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

  # 串行处理
  batch_process.py images/ -S

  # 查看系统资源
  batch_process.py --info

  # 设置内存使用上限（默认85%）
  batch_process.py images/ --max-mem 0.9
"""


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
    parser.add_argument("-S", "--sequential", action="store_true", help="串行处理")
    parser.add_argument("--info", action="store_true", help="显示系统资源信息")
    parser.add_argument("--max-mem", type=float, default=0.85,
                        help="最大内存使用率（默认: 0.85）")
    args = parser.parse_args()

    if args.info:
        print_resource_info()
        return

    if not args.folder_path:
        print(BANNER)
        print("""
功能说明:
  批量处理图像文件夹，计算每张图像的绿视指数(Green View Index, GVI)。
  填满式策略：不断提交任务，直到内存/显存接近上限。
  资源不足时等待任务完成，释放资源后继续提交。

参数说明:
  folder_path           包含图像的文件夹路径

选项:
  -o, --output_dir      输出目录（默认: results）
  -s, --save_segmentation  保存分割可视化结果
  -p, --is_panoramic    全景图模式
  -S, --sequential      串行处理
  --max-mem             最大内存使用率（默认: 0.85）
  --info                显示系统资源信息
  --help                显示此帮助信息
""")
        print(USAGE_EXAMPLES)
        return

    if not os.path.exists(args.folder_path):
        logger.error(f"文件夹 '{args.folder_path}' 不存在")
        return

    use_parallel = not args.sequential

    # 显示资源信息
    config = ResourceConfig(max_memory_usage=args.max_mem)
    monitor = get_resource_monitor(config)
    memory_usage = monitor.get_memory_usage()
    logger.info(f"当前内存使用率: {memory_usage:.1%}, 上限: {args.max_mem:.0%}")

    logger.info(f"开始处理: {args.folder_path}")
    logger.info(f"模式: {'并行（填满式）' if use_parallel else '串行'}")

    df = process_image_folder(
        args.folder_path,
        args.output_dir,
        args.save_segmentation,
        args.is_panoramic,
        use_parallel=use_parallel,
        max_workers=16,
        max_memory_usage=args.max_mem
    )

    if df is not None:
        logger.info(f"处理完成! 共处理 {len(df)} 张图像")
    else:
        logger.warning("未处理任何图像")


if __name__ == "__main__":
    main()
