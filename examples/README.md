# 示例图像

本目录提供最小化的测试图像集，覆盖普通图和全景图两种处理路径。

全景图处理会先裁剪底部 20%，再用短边 384px 的版本进行分割计算，并用短边 1024px 的版本生成可视化底图。

## 图像清单

| 文件名 | 类型 | 说明 |
|--------|------|------|
| `01_city_street.jpg` | 普通图 | 城市街景，低绿化 |
| `02_urban_park.jpg` | 普通图 | 城市公园，高绿化 |
| `03_dense_forest.jpg` | 普通图 | 森林场景，极高绿化 |
| `04_residential.jpg` | 普通图 | 住宅区，中等绿化 |
| `05_panoramic.jpg` | 全景图 | 全景图处理示例 |

## 使用示例

```bash
# 普通图
uv run main.py examples/02_urban_park.jpg --save_segmentation

# 全景图
uv run main.py examples/05_panoramic.jpg --is_panoramic --save_segmentation

# 批量处理
uv run batch_process.py examples/ --save_segmentation
```

结果默认输出到 `results/` 目录；批量处理会额外生成 `gvi_results.csv`。
保存分割结果时会输出三段竖向拼接图：显示图、50% 透明分割叠加图、纯分割图。
