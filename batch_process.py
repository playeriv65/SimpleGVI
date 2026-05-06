import os
import argparse
import logging
from modules.batch_processor import process_image_folder

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def main():
    """
    批量处理图像文件夹，计算每个图像的绿视指数(GVI)
    """
    parser = argparse.ArgumentParser(description="批量计算图像的绿视指数(Green View Index, GVI)")
    parser.add_argument("folder_path", help="包含图像的文件夹路径")
    parser.add_argument("--output_dir", "-o", default="results", help="输出结果的文件夹路径")
    parser.add_argument("--save_segmentation", "-s", action="store_true", help="是否保存分割可视化结果")
    parser.add_argument("--is_panoramic", "-p", action="store_true", help="图像是否为全景图")
    parser.add_argument("--parallel", "-P", action="store_true", default=True, help="使用并行处理（默认开启）")
    parser.add_argument("--sequential", "-S", action="store_true", help="使用串行处理")
    parser.add_argument("--workers", "-w", type=int, default=4, help="并行处理的最大工作数（默认4）")
    args = parser.parse_args()
    
    # 确定是否使用并行处理
    use_parallel = not args.sequential
    
    # 确保文件夹路径存在
    if not os.path.exists(args.folder_path):
        logger.error(f"文件夹 '{args.folder_path}' 不存在")
        return
    
    logger.info(f"开始处理文件夹: {args.folder_path}")
    logger.info(f"处理模式: {'并行' if use_parallel else '串行'}")
    if use_parallel:
        logger.info(f"最大并行数: {args.workers}")
    
    # 处理图像文件夹
    df = process_image_folder(
        args.folder_path,
        args.output_dir,
        args.save_segmentation,
        args.is_panoramic,
        use_parallel=use_parallel,
        max_workers=args.workers
    )
    
    if df is not None:
        logger.info(f"处理完成! 共处理 {len(df)} 张图像")
    else:
        logger.warning("未处理任何图像")


if __name__ == "__main__":
    main()
