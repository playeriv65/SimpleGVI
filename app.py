"""
SimpleGVI - 绿视指数计算工具
"""

import os
import tempfile
import logging
import pandas as pd
import streamlit as st
from PIL import Image
import numpy as np

MAX_UPLOAD_SIZE_MB = 50
MAX_BATCH_FILES = 20
MODEL_CACHE_MAX_SIZE = 10
MAX_IMAGE_HEIGHT = 380  # 限制图像最大高度(px)，确保不滚动

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="SimpleGVI",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# 注入样式：限制图像高度、紧凑布局
def inject_styles():
    st.markdown(
        """
    <style>
    /* 限制图像高度，防止页面滚动 */
    .stImage img {
        max-height: 380px !important;
        width: auto !important;
        object-fit: contain !important;
    }
    /* 紧凑按钮 */
    .stButton button {
        padding: 4px 8px !important;
        min-height: 32px !important;
        font-size: 13px !important;
    }
    /* 结果区域固定高度 */
    .result-bar {
        display: flex;
        align-items: center;
        gap: 24px;
        padding: 12px 16px;
        background: #f8f9fa;
        border-radius: 8px;
        margin-bottom: 12px;
    }
    .result-item {
        display: flex;
        flex-direction: column;
        align-items: flex-start;
    }
    .result-value {
        font-size: 26px;
        font-weight: 700;
        color: #1d1d1f;
        line-height: 1;
    }
    .result-label {
        font-size: 11px;
        color: #86868b;
        margin-top: 2px;
    }
    .result-level {
        font-size: 16px;
        font-weight: 600;
    }
    /* 文件列表样式 */
    .file-list-item {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 8px 12px;
        margin: 4px 0;
        border-radius: 6px;
        border: 1px solid #e5e5e5;
        cursor: pointer;
        transition: all 0.2s;
    }
    .file-list-item:hover {
        background: #f5f5f7;
    }
    .file-list-item.active {
        background: #34c759;
        color: white;
        border-color: #34c759;
    }
    .file-list-item.active .file-gvi {
        color: white;
    }
    .file-name {
        font-size: 13px;
        flex: 1;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    .file-gvi {
        font-size: 13px;
        font-weight: 600;
        color: #34c759;
        margin-left: 8px;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )


inject_styles()


@st.cache_resource(show_spinner=False)
def load_models():
    from modules.gvi_calculator import get_models

    return get_models()


def init_session_state():
    defaults = {
        "gvi_result": None,
        "display_image": None,
        "segmentation_rgb": None,
        "opacity": 0.5,
        "uploaded_name": None,
        "original_size": None,
        "processed_size": None,
        "model_loaded": False,
        "all_results": [],
        "all_images": {},
        "selected_index": 0,
        "is_panoramic": False,
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
        uploaded_files = uploaded_files[:MAX_BATCH_FILES]

    results = []
    images_cache = {}

    for idx, uploaded_file in enumerate(uploaded_files):
        try:
            file_size_mb = len(uploaded_file.getvalue()) / 1024 / 1024
            if file_size_mb > MAX_UPLOAD_SIZE_MB:
                results.append(
                    {
                        "文件名": uploaded_file.name,
                        "绿视指数": None,
                        "植被占比 (%)": None,
                        "状态": "❌",
                        "error": "大小超限",
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
                from modules.gvi_calculator import process_image
                from modules.visualization import segmentation_to_color

                gvi, segmentation, processed_image = process_image(
                    tmp_path, is_panoramic, processor, model
                )
                segmentation_rgb = segmentation_to_color(segmentation)

                images_cache[uploaded_file.name] = {
                    "original": processed_image,
                    "segmentation": segmentation_rgb,
                    "gvi": gvi,
                    "index": idx,
                }

                if len(images_cache) > MODEL_CACHE_MAX_SIZE:
                    oldest_key = next(iter(images_cache))
                    del images_cache[oldest_key]

                results.append(
                    {
                        "文件名": uploaded_file.name,
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
                    "绿视指数": None,
                    "植被占比 (%)": None,
                    "状态": "❌",
                    "error": str(e)[:20],
                    "index": idx,
                }
            )

    return results, images_cache


def render_header():
    cols = st.columns([1, 8, 1])
    with cols[0]:
        st.markdown(
            "<span style='font-size:18px;font-weight:600;'>🌿 SimpleGVI</span>",
            unsafe_allow_html=True,
        )
    with cols[2]:
        status = "就绪" if st.session_state.model_loaded else "加载中"
        color = "#34C759" if st.session_state.model_loaded else "#FF9500"
        st.markdown(
            f"<span style='font-size:12px;color:{color};'>{status}</span>",
            unsafe_allow_html=True,
        )


def render_left_panel(processor, model):
    st.markdown("**图像**")

    # 上传组件
    uploaded_files = st.file_uploader(
        "上传",
        type=["jpg", "jpeg", "png", "bmp", "tif", "tiff"],
        accept_multiple_files=True,
        label_visibility="collapsed",
    )

    is_panoramic = st.checkbox("全景", value=st.session_state.is_panoramic)
    st.session_state.is_panoramic = is_panoramic

    # 自动处理新上传的文件
    if uploaded_files:
        current_names = [f.name for f in uploaded_files]
        prev_names = [r["文件名"] for r in st.session_state.all_results]

        if current_names != prev_names:
            with st.spinner(f"分析 {len(uploaded_files)} 个图像..."):
                results, images_cache = process_all_uploaded_images(
                    uploaded_files, is_panoramic, processor, model
                )
                st.session_state.all_results = results
                st.session_state.all_images = images_cache
                st.session_state.selected_index = 0
                st.rerun()

    # 显示处理结果列表（紧凑样式）
    if st.session_state.all_results:
        success_count = len(
            [r for r in st.session_state.all_results if r["状态"] == "✅"]
        )
        st.caption(f"成功 {success_count}/{len(st.session_state.all_results)}")

        for idx, result in enumerate(st.session_state.all_results):
            name = result["文件名"]
            display_name = name[:18] + "..." if len(name) > 18 else name

            is_selected = st.session_state.selected_index == idx
            is_success = result["状态"] == "✅"

            # 使用HTML样式显示文件列表项
            active_class = "active" if is_selected else ""
            gvi_text = f"{result['绿视指数'] * 100:.0f}%" if is_success else "❌"

            # 使用 columns 创建紧凑的文件列表
            cols = st.columns([6, 2])
            with cols[0]:
                btn_label = f"{display_name}"
                btn_type = "primary" if is_selected else "secondary"
                if st.button(
                    btn_label, key=f"btn_{idx}", use_container_width=True, type=btn_type
                ):
                    st.session_state.selected_index = idx
                    st.rerun()
            with cols[1]:
                if is_success:
                    st.markdown(
                        f"<span style='color:#34C759;font-weight:600;font-size:13px;'>{gvi_text}</span>",
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        f"<span style='color:#FF3B30;font-size:13px;'>失败</span>",
                        unsafe_allow_html=True,
                    )

        # 导出按钮
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
            st.download_button("📥 导出CSV", csv, "gvi.csv", use_container_width=True)


def render_right_panel():
    st.markdown("**结果**")

    if not st.session_state.all_results:
        st.info("上传图像开始分析")
        return

    current_idx = st.session_state.selected_index
    if current_idx >= len(st.session_state.all_results):
        return

    result = st.session_state.all_results[current_idx]
    filename = result["文件名"]

    if result["状态"] != "✅":
        st.error(f"处理失败: {result.get('error', '未知错误')}")
        return

    if filename not in st.session_state.all_images:
        st.error("数据丢失")
        return

    img_data = st.session_state.all_images[filename]
    gvi = img_data["gvi"]

    # 使用HTML创建固定布局的结果栏（避免错位）
    level = "优秀" if gvi >= 0.3 else "良好" if gvi >= 0.15 else "较低"
    level_color = "#34C759" if gvi >= 0.3 else "#FF9500" if gvi >= 0.15 else "#FF3B30"
    short_name = filename[:20] + "..." if len(filename) > 20 else filename

    st.markdown(
        f"""
    <div class="result-bar">
        <div class="result-item">
            <span class="result-value">{gvi * 100:.1f}%</span>
            <span class="result-label">植被占比</span>
        </div>
        <div class="result-item">
            <span class="result-level" style="color:{level_color};">{level}</span>
            <span class="result-label">等级</span>
        </div>
        <div class="result-item" style="flex:1;min-width:120px;">
            <span style="font-size:13px;color:#666;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:150px;display:block;">{short_name}</span>
            <span class="result-label">{current_idx + 1} / {len(st.session_state.all_results)}</span>
        </div>
        <div class="result-item" style="min-width:140px;">
            <span style="font-size:12px;color:#86868b;">透明度</span>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # 透明度滑块（单独放，避免HTML内嵌交互组件的问题）
    opacity = st.slider(
        "", 0.0, 1.0, st.session_state.opacity, 0.05, label_visibility="collapsed"
    )
    st.session_state.opacity = opacity

    # 图像显示（限制高度的3列布局）
    blended = blend_images(img_data["original"], img_data["segmentation"], opacity)

    img_cols = st.columns(3, gap="small")
    with img_cols[0]:
        st.image(img_data["original"], caption="原图", use_container_width=True)
    with img_cols[1]:
        st.image(
            blended, caption=f"叠加 {opacity * 100:.0f}%", use_container_width=True
        )
    with img_cols[2]:
        st.image(img_data["segmentation"], caption="分割", use_container_width=True)

    # 导航按钮
    if len(st.session_state.all_results) > 1:
        nav_cols = st.columns([1, 1])
        with nav_cols[0]:
            if current_idx > 0:
                if st.button("← 上一个", use_container_width=True, key="prev"):
                    st.session_state.selected_index -= 1
                    st.rerun()
        with nav_cols[1]:
            if current_idx < len(st.session_state.all_results) - 1:
                if st.button("下一个 →", use_container_width=True, key="next"):
                    st.session_state.selected_index += 1
                    st.rerun()


def render_loading():
    st.markdown(
        """
    <div style="display:flex;flex-direction:column;align-items:center;padding:60px;">
        <div style="width:36px;height:36px;border:3px solid #F5F5F7;border-top-color:#34C759;border-radius:50%;animation:spin 1s linear infinite;"></div>
        <div style="color:#86868B;font-size:13px;margin-top:12px;">加载模型...</div>
    </div>
    <style>@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }</style>
    """,
        unsafe_allow_html=True,
    )


def main():
    init_session_state()
    render_header()
    st.divider()

    if not st.session_state.model_loaded:
        render_loading()
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
        st.error("请刷新页面重试")
        return

    left_col, right_col = st.columns([1, 3], gap="small")

    with left_col:
        render_left_panel(processor, model)

    with right_col:
        render_right_panel()


if __name__ == "__main__":
    main()
