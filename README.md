# SimpleGVI - 简化版绿视指数计算工具

SimpleGVI是一个简化版的绿视指数(Green View Index, GVI)计算工具，它基于[StreetView-NatureVisibility](https://github.com/Spatial-Data-Science-and-GEO-AI-Lab/StreetView-NatureVisibility)项目，但只保留了核心的GVI计算功能。

## 什么是绿视指数(GVI)?

绿视指数(Green View Index, GVI)是一个衡量城市环境中可见绿化比例的指标。它通过计算图像中植被区域占整个图像的百分比来定量化视野中的绿色元素。GVI值范围从0到1，其中0表示没有植被，1表示整个图像都是植被。

## 功能特点

- 支持处理单个图像或批量处理整个文件夹
- 支持普通图像和全景图像
- 使用Facebook的Mask2Former模型进行语义分割，准确识别植被区域
- 可视化语义分割结果，直观展示绿视分析
- 输出详细的GVI计算结果

## 安装

### 1. 克隆仓库

```bash
git clone https://github.com/yourusername/SimpleGVI.git
cd SimpleGVI
```

### 2. 环境配置

推荐使用 [uv](https://github.com/astral-sh/uv) 快速配置环境：

```bash
# 创建虚拟环境并安装依赖
uv venv
# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate

# 安装依赖
uv pip install -r requirements.txt
```

如果你已经有了 `pyproject.toml`，也可以直接同步环境：

```bash
uv sync
```

你也可以直接使用 `uv run` 运行脚本，它会自动处理环境：

```bash
uv run main.py path/to/image.jpg --is_panoramic
```

或者使用传统的 `pip` 或 `conda`：

#### 使用 conda:

```bash
conda create -n simplegvi python=3.9
conda activate simplegvi
pip install -r requirements.txt
```

#### 使用 venv:

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/macOS
source venv/bin/activate
pip install -r requirements.txt
```

## 使用方法

### 处理单个图像

```bash
python main.py path/to/image.jpg --is_panoramic --save_segmentation
```

参数说明:
- `path/to/image.jpg`: 图像文件路径
- `--output_dir`或`-o`: 输出目录，默认为"results"
- `--save_segmentation`或`-s`: 保存分割可视化结果
- `--is_panoramic`或`-p`: 指定图像为全景图

### 批量处理图像文件夹

```bash
python batch_process.py path/to/image/folder --is_panoramic --save_segmentation
```

参数说明:
- `path/to/image/folder`: 包含图像的文件夹路径
- `--output_dir`或`-o`: 输出目录，默认为"results"
- `--save_segmentation`或`-s`: 保存分割可视化结果
- `--is_panoramic`或`-p`: 指定所有图像均为全景图

## 输出结果

程序会在指定的输出目录中生成以下文件:

1. 对于单个图像:
   - `image_name_result.txt`: 包含GVI计算结果的文本文件
   - `image_name_segmentation.png`: 分割可视化结果(如果使用了`--save_segmentation`选项)

2. 对于批量处理:
   - `gvi_results.csv`: 包含所有图像GVI计算结果的CSV文件
   - 每个图像的分割可视化结果(如果使用了`--save_segmentation`选项)

## 技术原理

SimpleGVI使用以下步骤计算绿视指数:

1. **图像预处理**: 对输入图像进行必要的预处理，如全景图像会裁剪底部20%以去除不相关区域。

2. **语义分割**: 使用预训练的Mask2Former模型对图像进行语义分割，识别不同类别的区域(如道路、建筑、植被等)。

3. **植被识别**: 从分割结果中提取植被区域（包括树、草、植物、花、棕榈树等类别）。

4. **GVI计算**: 计算植被像素占总像素的比例，即为绿视指数。

对于全景图像，工具会将图像分为四个等宽部分分别处理，然后计算平均GVI。

## 依赖库

- torch
- transformers
- pillow
- numpy
- pandas
- tqdm

## 致谢

本项目基于[StreetView-NatureVisibility](https://github.com/Spatial-Data-Science-and-GEO-AI-Lab/StreetView-NatureVisibility)项目，该项目由Utrecht大学的空间数据科学和GEO-AI实验室开发。
