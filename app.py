"""
SimpleGVI - 绿视指数计算工具
Streamlit Web GUI Application
"""

import os
import tempfile
import logging
import pandas as pd
import streamlit as st
from PIL import Image, ImageOps
import numpy as np
from modules.gvi_calculator import process_image
from modules.visualization import segmentation_to_color
from config.settings import ADE20K_CLASS_INFO, ADE20K_VEGETATION_CLASSES
import html

MAX_UPLOAD_SIZE_MB = 50
MAX_BATCH_FILES = 20
MODEL_CACHE_MAX_SIZE = 10
FILENAME_DISPLAY_LENGTH_SIDEBAR = 12  # For left panel list
MAX_ERROR_LENGTH = 50  # For error message truncation


def cached_segmentation_to_color(segmentation, selected_classes):
    """直接调用可视化函数，不使用缓存（因为torch.Tensor无法哈希）"""
    return segmentation_to_color(segmentation, selected_classes)


def sanitize_filename(filename):
    """Sanitize filename by escaping HTML special characters to prevent XSS attacks."""
    if filename is None:
        return filename
    return html.escape(str(filename))


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="SimpleGVI",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def inject_apple_styles():
    try:
        from styles import get_apple_styles

        css_content = get_apple_styles()
        if css_content and isinstance(css_content, str):
            st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)
    except Exception as e:
        logger.warning(f"样式加载失败：{e}")

    # 强制单页显示 - 限制图片高度和紧凑布局
    st.markdown(
        """
    <style>
    /* 限制图片最大高度，防止撑大页面 */
    .stImage img {
        max-height: 320px !important;
        object-fit: contain !important;
        width: 100% !important;
    }
    
    /* 图片容器固定高度 */
    .stImage {
        max-height: 360px !important;
        overflow: hidden !important;
    }
    
    /* 紧凑布局 - 减少标题和元素间距 */
    .block-container {
        padding-top: 0.5rem !important;
        padding-bottom: 0.5rem !important;
    }
    
    /* 减少列间距 */
    .stColumns {
        gap: 0.25rem !important;
    }
    
    /* 限制右侧面板整体高度 */
    .main .block-container {
        max-height: 100vh;
        overflow: hidden;
    }
    
    /* 紧凑的标题和说明文字 */
    .stMarkdown p {
        margin-bottom: 0.25rem !important;
    }
    
    /* 紧凑的 slider */
    .stSlider {
        min-height: 2rem !important;
    }
    
    /* 减少 caption 间距 */
    .stCaption {
        margin-top: 0 !important;
        margin-bottom: 0 !important;
        font-size: 11px !important;
        line-height: 1 !important;
    }
    
    /* 隐藏 Streamlit 默认元素 */
    header {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stToolbar {display: none;}
    
    /* 紧凑的按钮 */
    .stButton > button {
        padding: 0.25rem 0.5rem !important;
        margin: 0.125rem 0 !important;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )


inject_apple_styles()


@st.cache_resource(show_spinner=False)
def load_models():
    from modules.gvi_calculator import get_models

    return get_models()


def init_session_state():
    defaults = {
        "opacity": 0.5,
        "original_size": None,
        "processed_size": None,
        "model_loaded": False,
        "all_results": [],
        "all_images": {},
        "selected_index": 0,
        "uploaded_files": [],
        "is_panoramic": False,
        "selected_vegetation_classes": {4, 9, 17, 66, 72},
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def blend_images(original, overlay, opacity: float):
    if isinstance(original, np.ndarray):
        original = Image.fromarray(original)
    if isinstance(overlay, np.ndarray):
        overlay = Image.fromarray(overlay)

    if original.size != overlay.size:
        overlay = overlay.resize(original.size, Image.Resampling.LANCZOS)

    original = original.convert("RGBA")
    overlay = overlay.convert("RGBA")

    overlay_array = np.array(overlay)
    overlay_array[:, :, 3] = (overlay_array[:, :, 3] * opacity).astype(np.uint8)
    overlay_blended = Image.fromarray(overlay_array)

    result = Image.alpha_composite(original, overlay_blended)
    return result.convert("RGB")


def process_all_uploaded_images(uploaded_files, is_panoramic, processor, model):
    if len(uploaded_files) > MAX_BATCH_FILES:
        st.warning(f"最多支持 {MAX_BATCH_FILES} 个文件")
        uploaded_files = uploaded_files[:MAX_BATCH_FILES]

    results = []
    images_cache = {}

    for idx, uploaded_file in enumerate(uploaded_files):
        try:
            file_size_mb = len(uploaded_file.getvalue()) / 1024 / 1024
            file_size_bytes = len(uploaded_file.getvalue())

            if file_size_mb > MAX_UPLOAD_SIZE_MB:
                results.append(
                    {
                        "文件名": uploaded_file.name,
                        "文件大小": file_size_bytes,
                        "绿视指数": None,
                        "植被占比 (%)": None,
                        "状态": f"❌ 超过{MAX_UPLOAD_SIZE_MB}MB",
                        "index": idx,
                    }
                )
                continue

            with tempfile.NamedTemporaryFile(
                delete=False, suffix=os.path.splitext(uploaded_file.name)[1]
            ) as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_path = tmp_file.name

            try:
                # Get original size before processing
                with Image.open(tmp_path) as img:
                    original_size = img.size

                gvi, segmentation, processed_image = process_image(
                    tmp_path, is_panoramic, processor, model
                )
                segmentation_rgb = segmentation_to_color(
                    segmentation, st.session_state.selected_vegetation_classes
                )

                # Get processed size
                processed_size = processed_image.size

                images_cache[uploaded_file.name] = {
                    "original": processed_image,
                    "segmentation": segmentation_rgb,
                    "segmentation_raw": segmentation,
                    "gvi": gvi,
                    "original_size": original_size,
                    "processed_size": processed_size,
                    "index": idx,
                }

                if len(images_cache) > MODEL_CACHE_MAX_SIZE:
                    oldest_key = next(iter(images_cache))
                    del images_cache[oldest_key]

                results.append(
                    {
                        "文件名": uploaded_file.name,
                        "文件大小": file_size_bytes,
                        "绿视指数": round(gvi, 4),
                        "植被占比 (%)": round(gvi * 100, 2),
                        "状态": "✅",
                        "index": idx,
                    }
                )

            finally:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)

        except Exception as e:
            logger.error(f"处理失败：{e}")
            results.append(
                {
                    "文件名": uploaded_file.name,
                    "文件大小": len(uploaded_file.getvalue()) if uploaded_file else 0,
                    "绿视指数": None,
                    "植被占比 (%)": None,
                    "状态": f"❌ {str(e)[:MAX_ERROR_LENGTH]}",
                    "index": idx,
                }
            )

    return results, images_cache


def render_loading_animation():
    st.markdown(
        """
    <style>
    @keyframes apple-spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    .loading-container { display: flex; flex-direction: column; align-items: center; padding: 60px 40px; }
    .loading-spinner { width: 40px; height: 40px; border: 3px solid #F5F5F7; border-top-color: #34C759; border-radius: 50%; animation: apple-spin 1s linear infinite; }
    .loading-text { color: #86868B; font-size: 14px; margin-top: 16px; }
    </style>
    <div class="loading-container">
        <div class="loading-spinner"></div>
        <div class="loading-text">正在加载模型...</div>
    </div>
    """,
        unsafe_allow_html=True,
    )


def render_unified_interface(processor, model):
    left_col, right_col = st.columns([1, 3], gap="small")

    with left_col:
        # 紧凑上传区
        uploaded_files = st.file_uploader(
            "上传",
            type=["jpg", "jpeg", "png", "bmp", "tif", "tiff"],
            accept_multiple_files=True,
            label_visibility="collapsed",
        )
        is_panoramic = st.checkbox("全景", value=False)

        # 自动处理：检测到新上传文件就立即处理
        if uploaded_files and len(uploaded_files) > 0:
            current_files = [(f.name, len(f.getvalue())) for f in uploaded_files]
            prev_files = [
                (r["文件名"], r.get("文件大小", 0))
                for r in st.session_state.all_results
            ]

            if current_files != prev_files:
                with st.spinner(f"分析 {len(uploaded_files)} 个图像..."):
                    results, images_cache = process_all_uploaded_images(
                        uploaded_files, is_panoramic, processor, model
                    )
                    st.session_state.all_results = results
                    st.session_state.all_images = images_cache
                    st.session_state.selected_index = 0
                    st.rerun()

        # 显示结果列表
        if st.session_state.all_results:
            success_count = len(
                [r for r in st.session_state.all_results if r["状态"] == "✅"]
            )
            st.caption(f"{success_count}/{len(st.session_state.all_results)} 成功")

            for idx, result in enumerate(st.session_state.all_results):
                name = sanitize_filename(result["文件名"])
                display_name = (
                    name[:FILENAME_DISPLAY_LENGTH_SIDEBAR] + "..."
                    if len(name) > FILENAME_DISPLAY_LENGTH_SIDEBAR
                    else name
                )

                if result["状态"] == "✅":
                    label = f"{display_name} · {result['绿视指数'] * 100:.0f}%"
                else:
                    label = f"{display_name} · ❌"

                is_selected = st.session_state.selected_index == idx
                btn_type = "primary" if is_selected else "secondary"

                if st.button(
                    label, key=f"img_{idx}", use_container_width=True, type=btn_type
                ):
                    st.session_state.selected_index = idx
                    st.rerun()

            # 下载按钮
            if success_count > 0:
                df = pd.DataFrame(
                    [
                        {
                            "文件名": r["文件名"],
                            "GVI": r["绿视指数"],
                            "植被%": r["植被占比 (%)"],
                        }
                        for r in st.session_state.all_results
                        if r["状态"] == "✅"
                    ]
                )
                csv = df.to_csv(index=False).encode("utf-8-sig")
                st.download_button(
                    "📥 导出 CSV", csv, "gvi.csv", use_container_width=True
                )

    with right_col:
        if not st.session_state.all_results:
            st.info("上传图像开始分析")
            return

        current_idx = st.session_state.selected_index
        if current_idx >= len(st.session_state.all_results):
            return

        result = st.session_state.all_results[current_idx]
        filename = result["文件名"]

        if result["状态"] != "✅":
            st.error(f"处理失败")
            return

        if filename not in st.session_state.all_images:
            st.error("数据丢失")
            return

        img_data = st.session_state.all_images[filename]
        gvi = img_data["gvi"]

        # 更新尺寸信息
        st.session_state.original_size = img_data.get("original_size", (0, 0))
        st.session_state.processed_size = img_data.get("processed_size", (0, 0))

        # 一行布局：植被占比 + 叠加透明度滑块
        info_cols = st.columns([1, 3])
        with info_cols[0]:
            st.markdown(
                f"<div style='font-size:28px;font-weight:700;color:#1D1D1F;line-height:1;'>{gvi * 100:.1f}%</div>",
                unsafe_allow_html=True,
            )
            st.caption("植被占比")
        with info_cols[1]:
            st.markdown(
                "<div style='font-size:11px;color:#666;margin-bottom:4px;line-height:1;'>叠加透明度</div>",
                unsafe_allow_html=True,
            )
            opacity = st.slider(
                "透明度",
                0.0,
                1.0,
                st.session_state.opacity,
                0.05,
                label_visibility="collapsed",
                key="opacity_slider",
            )
            st.session_state.opacity = opacity

        st.markdown(
            "<div class='legend-label'>植被类别</div>",
            unsafe_allow_html=True,
        )

        legend_cols = st.columns(5, gap="small")
        sorted_veg_ids = sorted(list(ADE20K_VEGETATION_CLASSES))
        for i, veg_id in enumerate(sorted_veg_ids):
            class_info = ADE20K_CLASS_INFO.get(
                veg_id, {"name": "unknown", "color": [128, 128, 128]}
            )
            class_name = class_info["name"]
            color = class_info["color"]
            color_hex = f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"

            with legend_cols[i]:
                is_selected = veg_id in st.session_state.selected_vegetation_classes
                checkbox_key = f"veg_checkbox_{veg_id}"

                # 使用markdown显示颜色块
                safe_class_name = html.escape(class_name)
                st.markdown(
                    f"<div style='display:flex;align-items:center;gap:4px;margin-bottom:4px;'>"
                    f"<span style='display:inline-block;width:12px;height:12px;background:{color_hex};border-radius:2px;'></span>"
                    f"<span style='font-size:12px;'>{safe_class_name}</span>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
                
                # 使用checkbox处理交互
                if st.checkbox(
                    "显示",
                    value=is_selected,
                    key=checkbox_key,
                    label_visibility="collapsed",
                ):
                    st.session_state.selected_vegetation_classes.add(veg_id)
                else:
                    st.session_state.selected_vegetation_classes.discard(veg_id)

        segmentation_raw = img_data.get("segmentation_raw", img_data["segmentation"])
        selected_classes = st.session_state.selected_vegetation_classes
        segmentation_rgb = cached_segmentation_to_color(segmentation_raw, selected_classes)

        # 图像显示（固定高度，三列紧凑布局）
        blended = blend_images(img_data["original"], segmentation_rgb, opacity)

        img_cols = st.columns(3, gap="small")
        with img_cols[0]:
            st.image(img_data["original"], caption="显示图", use_container_width=True)
        with img_cols[1]:
            st.image(
                blended, caption=f"叠加 {opacity * 100:.0f}%", use_container_width=True
            )
        with img_cols[2]:
            st.image(segmentation_rgb, caption="分割", use_container_width=True)

        # 导航按钮（如果有多张）
        if len(st.session_state.all_results) > 1:
            nav_cols = st.columns(2, gap="small")
            with nav_cols[0]:
                if current_idx > 0:
                    if st.button(
                        "← 上一个", use_container_width=True, key=f"prev_{current_idx}"
                    ):
                        st.session_state.selected_index -= 1
                        st.rerun()
            with nav_cols[1]:
                if current_idx < len(st.session_state.all_results) - 1:
                    if st.button(
                        "下一个 →", use_container_width=True, key=f"next_{current_idx}"
                    ):
                        st.session_state.selected_index += 1
                        st.rerun()


def main():
    init_session_state()

    # 顶部栏：Logo + 模型状态
    st.markdown(
        """
    <style>
    header {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stToolbar {display: none;}
    </style>
    """,
        unsafe_allow_html=True,
    )

    status_color = "#34C759" if st.session_state.model_loaded else "#FF9500"
    status_text = "模型就绪" if st.session_state.model_loaded else "加载中"

    st.markdown(
        f"""
    <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;'>
        <div style='display: flex; align-items: center; gap: 16px;'>
            <span style='font-size:18px;font-weight:600;'>🌿 SimpleGVI</span>
            <span style='font-size:13px;color:{status_color};'>{status_text}</span>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    if not st.session_state.model_loaded:
        render_loading_animation()
        try:
            processor, model = load_models()
            st.session_state.model_loaded = True
            st.session_state.processor = processor
            st.session_state.model = model
            st.rerun()
        except Exception as e:
            st.error(f"模型加载失败：{str(e)}")
            return
        return

    try:
        processor = st.session_state.processor
        model = st.session_state.model
    except KeyError:
        st.error("模型未正确加载，请刷新页面。")
        return

    render_unified_interface(processor, model)


if __name__ == "__main__":
    main()
