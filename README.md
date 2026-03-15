# SimpleGVI - 绿视指数计算工具

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

SimpleGVI 是一个简化版的绿视指数 (Green View Index, GVI) 计算工具，使用 Facebook 的 Mask2Former 模型进行语义分割，计算图像中植被区域的占比。

---

## 快速开始

### 1. 安装依赖

```bash
git clone https://github.com/yourusername/SimpleGVI.git
cd SimpleGVI

# 使用 uv（推荐）
uv venv && source .venv/bin/activate
uv pip install -r requirements.txt
```

### 2. 使用方法

#### 命令行 (CLI)

```bash
# 处理单张图像
uv run main.py examples/forest.jpg --save_segmentation

# 批量处理文件夹
uv run batch_process.py path/to/images/ --save_segmentation
```

#### Python API

```python
from modules.gvi_calculator import process_image, get_models

# 加载模型
processor, model = get_models()

# 处理图像
gvi, segmentation, image = process_image(
    'examples/forest.jpg',
    is_panoramic=False,
    processor=processor,
    model=model
)

print(f'绿视指数：{gvi:.4f} ({gvi*100:.1f}%)')
```

#### Web 界面

```bash
uv run streamlit run app.py --server.port 8501
```

访问 http://localhost:8501

---

## 输出结果

- **CLI**: `results/` 目录下生成结果文件和分割图
- **批量处理**: `gvi_results.csv` 包含所有图像的 GVI 结果
- **Web UI**: 实时显示结果，支持 CSV 导出

---

## 绿化等级

| GVI 范围 | 等级 |
|---------|------|
| ≥ 0.30 | 优秀 🟢 |
| ≥ 0.15 | 良好 🟡 |
| < 0.15 | 较低 🔴 |

---

## 依赖

- torch
- transformers
- pillow
- numpy
- pandas
- streamlit

完整依赖见 [`requirements.txt`](requirements.txt)

---

## 示例

```bash
# 测试示例图像
uv run main.py examples/forest.jpg -s
```

输出:
```
加载语义分割模型...
处理图像：examples/forest.jpg
绿视指数 (GVI): 1.0000
分割可视化结果已保存到：results/forest_segmentation.png
处理完成!
```

---

## 致谢

基于 [StreetView-NatureVisibility](https://github.com/Spatial-Data-Science-and-GEO-AI-Lab/StreetView-NatureVisibility) 项目，使用 Facebook [Mask2Former](https://github.com/facebookresearch/Mask2Former) 模型。

---

## License

MIT License
