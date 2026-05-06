import os
import argparse
import logging
from modules.batch_processor import process_image_folder
from modules.resource_manager import get_optimal_workers, print_resource_info

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def main():
    """
    批量处理图像文件夹，计算每个图像的绿视指数(GVI)
    """
    parser = argparse.ArgumentParser(description="批量计算图像的绿视指数(Green View Index, GVI)")
    parser.add_argument("folder_path", nargs='?', help="包含图像的文件夹路径")
    parser.add_argument("--output_dir", "-o", default="results", help="输出结果的文件夹路径")
    parser.add_argument("--save_segmentation", "-s", action="store_true", help="是否保存分割可视化结果")
    parser.add_argument("--is_panoramic", "-p", action="store_true", help="图像是否为全景图")
    parser.add_argument("--parallel", "-P", action="store_true", default=True, help="使用并行处理（默认开启）")
    parser.add_argument("--sequential", "-S", action="store_true", help="使用串行处理")
    parser.add_argument("--workers", "-w", type=str, default="auto",
                        help="并行处理的最大工作数（默认auto，可指定数字或auto）")
    parser.add_argument("--gpu-ratio", type=float, default=0.8,
                        help="GPU显存使用比率（默认0.8，类似vLLM）")
    parser.add_argument("--cpu-ratio", type=float, default=0.7,
                        help="CPU内存使用比率（默认0.7）")
    parser.add_argument("--reserve-mb", type=int, default=1024,
                        help="预留内存MB（默认1024）")
    parser.add_argument("--info", action="store_true", help="显示系统资源信息并退出")
    args = parser.parse_args()

    if args.info:
        print_resource_info()
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

    logger.info(f"开始处理文件夹: {args.folder_path}")
    logger.info(f"处理模式: {'并行' if use_parallel else '串行'}")
    if use_parallel:
        logger.info(f"最大并行数: {max_workers}")
        if args.workers == "auto":
            logger.info(f"GPU显存比率: {args.gpu_ratio}")
            logger.info(f"CPU内存比率: {args.cpu_ratio}")

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
