"""
SimpleGVI - 绿视指数计算工具
Streamlit Web GUI Application
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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="SimpleGVI",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)


def inject_apple_styles():
    try:
        from styles import get_apple_styles

        css_content = get_apple_styles()
        if css_content and isinstance(css_content, str):
            st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)
    except Exception as e:
        logger.warning(f"样式加载失败：{e}")


inject_apple_styles()


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
        "processing_complete": False,
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
            if file_size_mb > MAX_UPLOAD_SIZE_MB:
                results.append(
                    {
                        "文件名": uploaded_file.name,
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
                    "状态": f"❌ 错误",
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


def render_result_card():
    gvi = st.session_state.gvi_result

    if gvi >= 0.3:
        level, level_color = "优秀", "#34C759"
    elif gvi >= 0.15:
        level, level_color = "良好", "#FF9500"
    else:
        level, level_color = "较低", "#FF3B30"

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(
            f"<div style='font-size:32px;font-weight:700;color:#1D1D1F;'>{gvi * 100:.1f}%</div>",
            unsafe_allow_html=True,
        )
        st.caption("植被占比")
    with col2:
        st.markdown(
            f"<div style='font-size:20px;font-weight:600;color:{level_color};text-align:right;'>{level}</div>",
            unsafe_allow_html=True,
        )
        st.caption("绿化等级")

    if st.session_state.original_size != st.session_state.processed_size:
        st.caption(
            f"⚠️ 已缩放：{st.session_state.original_size[0]}×{st.session_state.original_size[1]} → {st.session_state.processed_size[0]}×{st.session_state.processed_size[1]}"
        )


def render_image_viewer():
    opacity = st.slider("透明度", 0.0, 1.0, st.session_state.opacity, 0.05)

    blended = blend_images(
        st.session_state.display_image,
        st.session_state.segmentation_rgb,
        opacity,
    )

    col1, col2, col3 = st.columns(3, gap="small")
    with col1:
        st.image(
            st.session_state.display_image, caption="原始", use_container_width=True
        )
    with col2:
        st.image(
            blended, caption=f"叠加 ({opacity * 100:.0f}%)", use_container_width=True
        )
    with col3:
        st.image(
            st.session_state.segmentation_rgb, caption="分割", use_container_width=True
        )


def render_unified_interface(processor, model):
    left_col, right_col = st.columns([1, 2], gap="medium")

    with left_col:
        uploaded_files = st.file_uploader(
            "上传图像",
            type=["jpg", "jpeg", "png", "bmp", "tif", "tiff"],
            accept_multiple_files=True,
            key="image_uploader",
            label_visibility="collapsed",
        )
        is_panoramic = st.checkbox("全景模式", value=False)

        if uploaded_files:
            st.caption(f"{len(uploaded_files)} 个文件")

            if st.button("开始分析", type="primary", use_container_width=True):
                with st.spinner("处理中..."):
                    results, images_cache = process_all_uploaded_images(
                        uploaded_files, is_panoramic, processor, model
                    )
                    st.session_state.all_results = results
                    st.session_state.all_images = images_cache
                    st.session_state.selected_index = 0
                    st.session_state.processing_complete = True
                    st.rerun()

        if st.session_state.processing_complete and st.session_state.all_results:
            st.divider()
            results = st.session_state.all_results
            success = len([r for r in results if r["状态"] == "✅"])
            st.caption(f"结果：{success}/{len(results)} 成功")

            for idx, result in enumerate(results):
                if result["状态"] == "✅":
                    label = f"{result['文件名'][:20]}{'...' if len(result['文件名']) > 20 else ''}  {result['绿视指数'] * 100:.0f}%"
                    if st.button(label, key=f"result_{idx}", use_container_width=True):
                        st.session_state.selected_index = idx
                        st.rerun()

            if success > 0:
                df = pd.DataFrame(
                    [
                        {
                            "文件名": r["文件名"],
                            "绿视指数": r["绿视指数"],
                            "植被占比 (%)": r["植被占比 (%)"],
                        }
                        for r in results
                        if r["状态"] == "✅"
                    ]
                )
                csv = df.to_csv(index=False).encode("utf-8-sig")
                st.download_button(
                    "下载 CSV", csv, "gvi_results.csv", use_container_width=True
                )

    with right_col:
        if st.session_state.processing_complete and st.session_state.all_results:
            current_idx = st.session_state.selected_index

            if current_idx < len(st.session_state.all_results):
                result = st.session_state.all_results[current_idx]
                filename = result["文件名"]

                if filename in st.session_state.all_images:
                    img_data = st.session_state.all_images[filename]

                    st.session_state.gvi_result = img_data["gvi"]
                    st.session_state.display_image = img_data["original"]
                    st.session_state.segmentation_rgb = img_data["segmentation"]
                    st.session_state.uploaded_name = filename

                    render_result_card()
                    st.divider()
                    render_image_viewer()

                    nav_col1, nav_col2, nav_col3 = st.columns([1, 1, 1])
                    with nav_col1:
                        if current_idx > 0:
                            if st.button(
                                "← 上一张", use_container_width=True, key="prev_img"
                            ):
                                st.session_state.selected_index -= 1
                                st.rerun()
                    with nav_col3:
                        if current_idx < len(st.session_state.all_results) - 1:
                            if st.button(
                                "下一张 →", use_container_width=True, key="next_img"
                            ):
                                st.session_state.selected_index += 1
                                st.rerun()
        else:
            st.info("上传图像后开始分析")


def main():
    init_session_state()

    c1, c2, c3 = st.columns([1, 3, 1])
    with c1:
        st.markdown(
            "<span style='font-size:20px;font-weight:600;'>🌿 SimpleGVI</span>",
            unsafe_allow_html=True,
        )
    with c2:
        pass
    with c3:
        status = "✅ 就绪" if st.session_state.model_loaded else "⏳ 加载中"
        st.markdown(
            f"<span style='font-size:13px;color:{'#34C759' if st.session_state.model_loaded else '#FF9500'};'>{status}</span>",
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
