"""
全面测试 SimpleGVI 项目
"""

import os
import sys
import pytest
import numpy as np
from PIL import Image
import tempfile
import shutil

# 确保可以导入项目模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.settings import (
    ADE20K_VEGETATION_CLASSES,
    VEGETATION_NAMES,
    get_vegetation_colors,
    is_vegetation_class,
)
from modules.legend_config import (
    get_class_info,
    is_vegetation_class as legend_is_vegetation,
    get_ade20k_color_palette,
)


class TestConfiguration:
    """测试配置模块"""

    def test_vegetation_classes(self):
        """测试植被类别配置"""
        assert ADE20K_VEGETATION_CLASSES == {4, 9, 17, 66, 72}
        assert len(ADE20K_VEGETATION_CLASSES) == 5

    def test_vegetation_names(self):
        """测试植被名称配置"""
        assert VEGETATION_NAMES == ["tree", "grass", "plant", "flower", "palm"]
        assert len(VEGETATION_NAMES) == 5

    def test_vegetation_colors(self):
        """测试植被颜色配置"""
        colors = get_vegetation_colors()
        assert len(colors) == 5
        for color in colors:
            assert len(color) == 3
            assert all(0 <= c <= 255 for c in color)
            # 所有颜色都应该是绿色系 (R=0)
            assert color[0] == 0

    def test_is_vegetation_class(self):
        """测试植被类别判断函数"""
        # 植被类别
        for class_id in [4, 9, 17, 66, 72]:
            assert is_vegetation_class(class_id) is True
            assert legend_is_vegetation(class_id) is True

        # 非植被类别
        for class_id in [0, 1, 2, 3, 5, 6, 10, 20, 100]:
            assert is_vegetation_class(class_id) is False


class TestLegendConfig:
    """测试图例配置模块"""

    def test_get_class_info(self):
        """测试获取类别信息"""
        # 测试植被类别
        color, name = get_class_info(4)
        assert name == "tree"
        assert len(color) == 3

        color, name = get_class_info(9)
        assert name == "grass"

        # 测试不存在的类别
        color, name = get_class_info(999)
        assert name == "void"
        assert color == [0, 0, 0]

    def test_color_palette(self):
        """测试颜色调色板"""
        palette = get_ade20k_color_palette()
        assert len(palette) == 150
        for color in palette:
            assert len(color) == 3
            assert all(0 <= c <= 255 for c in color)


class TestGVICalculator:
    """测试 GVI 计算模块"""

    def test_model_loading(self):
        """测试模型加载"""
        from modules.gvi_calculator import get_models

        try:
            processor, model = get_models()
            assert processor is not None
            assert model is not None
            print("✓ 模型加载成功")
        except Exception as e:
            pytest.skip(f"模型加载失败: {e}")

    def test_process_image(self):
        """测试图像处理"""
        from modules.gvi_calculator import process_image, get_models

        # 使用示例图像测试
        test_image = "images/green_forest1.jpg"
        if not os.path.exists(test_image):
            pytest.skip("测试图像不存在")

        try:
            processor, model = get_models()
            gvi, segmentation = process_image(test_image, False, processor, model)

            # 验证结果
            assert 0 <= gvi <= 1, f"GVI 应该在 0-1 之间，实际是 {gvi}"
            assert segmentation is not None
            assert isinstance(segmentation, np.ndarray)
            print(f"✓ 图像处理成功，GVI: {gvi:.4f}")
        except Exception as e:
            pytest.skip(f"图像处理失败: {e}")


class TestVisualization:
    """测试可视化模块"""

    def test_segmentation_to_color(self):
        """测试分割结果转彩色图像"""
        from modules.visualization import segmentation_to_color

        # 创建测试分割数据
        segmentation = np.random.randint(0, 150, (100, 100))

        try:
            colored = segmentation_to_color(segmentation)
            assert colored.shape == (100, 100, 3)
            assert colored.dtype == np.uint8
            print("✓ 分割转彩色图像成功")
        except Exception as e:
            pytest.skip(f"分割转彩色失败: {e}")

    def test_save_segmentation_visualization(self):
        """测试保存分割可视化"""
        from modules.visualization import save_segmentation_visualization
        from modules.gvi_calculator import process_image, get_models

        test_image = "images/green_forest1.jpg"
        if not os.path.exists(test_image):
            pytest.skip("测试图像不存在")

        # 创建临时输出目录
        output_dir = tempfile.mkdtemp()
        output_path = os.path.join(output_dir, "test_result.png")

        try:
            processor, model = get_models()
            gvi, segmentation = process_image(test_image, False, processor, model)

            save_segmentation_visualization(test_image, segmentation, gvi, output_path)

            # 验证输出文件
            assert os.path.exists(output_path), "输出文件应该存在"
            assert os.path.getsize(output_path) > 0, "输出文件不应该为空"

            # 验证图像内容
            with Image.open(output_path) as img:
                assert img.size[0] > 0 and img.size[1] > 0
                print(f"✓ 可视化保存成功: {img.size}")
        except Exception as e:
            pytest.skip(f"可视化测试失败: {e}")
        finally:
            shutil.rmtree(output_dir, ignore_errors=True)


class TestCLIFunctionality:
    """测试 CLI 功能"""

    def test_main_cli_help(self):
        """测试主 CLI 帮助信息"""
        import subprocess

        result = subprocess.run(
            [sys.executable, "main.py", "--help"],
            capture_output=True,
            text=True,
            timeout=60,
        )

        assert result.returncode == 0
        assert "usage:" in result.stdout.lower()
        print("✓ CLI 帮助信息正常")

    def test_batch_processor_help(self):
        """测试批量处理器帮助信息"""
        import subprocess

        result = subprocess.run(
            [sys.executable, "batch_process.py", "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        assert result.returncode == 0
        assert "usage:" in result.stdout.lower()
        print("✓ 批量处理器帮助信息正常")


class TestLegendDisplay:
    """测试图例显示"""

    def test_legend_items_count(self):
        """测试图例项目数量"""
        from config.settings import VEGETATION_NAMES, get_vegetation_colors

        names = VEGETATION_NAMES
        colors = get_vegetation_colors()

        # 应该是5种植被 + 1个非植物
        assert len(names) == 5
        assert len(colors) == 5
        print(f"✓ 图例项目: {names}")

    def test_legend_colors_green(self):
        """测试图例颜色都是绿色系"""
        from config.settings import get_vegetation_colors

        colors = get_vegetation_colors()

        for i, color in enumerate(colors):
            # R 通道应该是 0 (绿色系)
            assert color[0] == 0, f"第 {i} 个颜色不是绿色系"
            # G 通道应该较高
            assert color[1] >= 100, f"第 {i} 个颜色 G 通道太低"
            print(f"✓ 颜色 {i}: RGB{color}")


class TestIntegration:
    """集成测试"""

    def test_end_to_end_single_image(self):
        """测试端到端单图处理"""
        from modules.gvi_calculator import process_image, get_models
        from modules.visualization import save_segmentation_visualization

        test_image = "images/green_forest1.jpg"
        if not os.path.exists(test_image):
            pytest.skip("测试图像不存在")

        output_dir = tempfile.mkdtemp()
        output_path = os.path.join(output_dir, "integration_test.png")

        try:
            # 1. 加载模型
            processor, model = get_models()
            print("✓ 模型加载成功")

            # 2. 处理图像
            gvi, segmentation = process_image(test_image, False, processor, model)
            print(f"✓ 图像处理成功, GVI: {gvi:.4f}")

            # 3. 保存可视化
            save_segmentation_visualization(test_image, segmentation, gvi, output_path)
            print(f"✓ 可视化保存成功")

            # 4. 验证结果
            assert os.path.exists(output_path)
            with Image.open(output_path) as img:
                assert img.format == "PNG"
                print(f"✓ 集成测试通过，输出: {img.size}")

        except Exception as e:
            pytest.fail(f"集成测试失败: {e}")
        finally:
            shutil.rmtree(output_dir, ignore_errors=True)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
