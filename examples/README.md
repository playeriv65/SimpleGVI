# SimpleGVI 示例图像集

本文件夹包含用于测试SimpleGVI绿视指数计算工具的示例图像。

## 示例图像说明

### 按绿化程度分类

| 文件名 | 描述 | 预期GVI范围 |
|--------|------|-------------|
| `01_city_street.jpg` | 城市天际线，几乎无绿化 | 低 (0-0.1) |
| `02_urban_park.jpg` | 城市公园，林荫小道 | 高 (0.4-0.7) |
| `03_dense_forest.jpg` | 茂密森林，云雾缭绕 | 极高 (0.7-1.0) |
| `04_residential.jpg` | 住宅区，带庭院和泳池 | 中等 (0.2-0.4) |
| `green_street1.jpg` | 城市街道，有树木 | 中等 (0.2-0.4) |
| `green_park1.jpg` | 公园场景 | 高 (0.4-0.7) |
| `green_forest1.jpg` | 森林景观 | 极高 (0.7-1.0) |
| `garden.jpg` | 花园场景 | 高 (0.4-0.7) |
| `forest.jpg` | 森林图像 | 极高 (0.7-1.0) |
| `test.jpg` | 测试图像 | 视内容而定 |

## 使用方法

### 1. 单图像处理

```bash
# 处理单个图像
python main.py examples/02_urban_park.jpg --save_segmentation

# 处理全景图像
python main.py examples/03_dense_forest.jpg --is_panoramic --save_segmentation
```

### 2. 批量处理

```bash
# 批量处理整个示例文件夹
python batch_process.py examples/ --save_segmentation

# 批量处理（指定为全景图像）
python batch_process.py examples/ --is_panoramic --save_segmentation
```

### 3. Web界面

```bash
# 启动Streamlit Web界面
streamlit run app.py

# 然后在浏览器中打开 http://localhost:8501
# 上传示例文件夹中的图像进行测试
```

## 输出结果

处理完成后，结果将保存在 `results/` 目录中：

- `*_result.txt` - GVI计算结果文本文件
- `*_segmentation.png` - 语义分割可视化图像
- `gvi_results.csv` - 批量处理的CSV结果文件

## 图像来源

示例图像来自Unsplash免费图库，仅供测试使用。
