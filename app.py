"""
SimpleGVI - 绿视指数计算工具
Streamlit Web GUI Application

功能:
- 统一图像上传 (单张/多张同一逻辑)
- 处理完成后自动显示首张预览
- 左侧列表切换查看不同图像
- EXIF 方向自动纠正
- 图像自动缩放 (最大 1024px)
- Apple 风格 UI
"""

import os
import tempfile
import logging
import pandas as pd
import streamlit as st
from PIL import Image, ImageOps
import numpy as np

# ============================================================
# 配置常量
# ============================================================
MAX_UPLOAD_SIZE_MB = 50  # 最大上传文件大小 (MB)
MAX_BATCH_FILES = 20  # 最大文件数
MODEL_CACHE_MAX_SIZE = 10  # 缓存最大图像数

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="SimpleGVI - 绿视指数计算工具",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# 样式注入
# ============================================================
def inject_apple_styles():
    """注入 Apple 风格 CSS 样式"""
    try:
        from styles import get_apple_styles

        css_content = get_apple_styles()
        if css_content and isinstance(css_content, str):
            st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)
    except Exception as e:
        logger.warning(f"样式加载失败：{e}")


inject_apple_styles()


# ============================================================
# 模型加载
# ============================================================
@st.cache_resource(show_spinner=False)
def load_models():
    """加载预训练模型 (带缓存)"""
    from modules.gvi_calculator import get_models

    return get_models()


# ============================================================
# 会话状态初始化
# ============================================================
def init_session_state():
    """初始化会话状态变量"""
    defaults = {
        "gvi_result": None,
        "display_image": None,
        "segmentation_rgb": None,
        "opacity": 0.5,
        "uploaded_name": None,
        "original_size": None,
        "processed_size": None,
        "model_loaded": False,
        "all_results": [],  # 所有处理结果
        "all_images": {},  # 所有图像缓存
        "selected_index": 0,  # 当前选中的图像索引
        "processing_complete": False,  # 是否已完成处理
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# ============================================================
# 图像混合函数
# ============================================================
def blend_images(original, overlay, opacity: float):
    """将分割结果以指定透明度叠加到原图上"""
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


# ============================================================
# 统一处理所有图像
# ============================================================
def process_all_uploaded_images(uploaded_files, is_panoramic, processor, model):
    """
    统一处理所有上传的图像（单张/多张使用同一逻辑）
    """
    if len(uploaded_files) > MAX_BATCH_FILES:
        st.warning(
            f"最多支持 {MAX_BATCH_FILES} 个文件，已自动截取前 {MAX_BATCH_FILES} 个"
        )
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
                        "状态": f"❌ 超过大小限制 ({MAX_UPLOAD_SIZE_MB}MB)",
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
                        "状态": "✅ 成功",
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
                    "状态": f"❌ {str(e)}",
                    "index": idx,
                }
            )

    return results, images_cache


# ============================================================
# 加载动画
# ============================================================
def render_loading_animation():
    """渲染 Apple 风格模型加载动画"""
    st.markdown(
        """
    <style>
    @keyframes apple-spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    @keyframes apple-pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.3; } }
    .loading-container { display: flex; flex-direction: column; align-items: center; padding: 80px 40px; background: #FFFFFF; border-radius: 18px; box-shadow: 0 4px 24px rgba(0,0,0,0.04); margin: 60px auto; max-width: 420px; }
    .loading-spinner { width: 48px; height: 48px; border: 3px solid #F5F5F7; border-top-color: #34C759; border-radius: 50%; animation: apple-spin 1s linear infinite; margin-bottom: 24px; }
    .loading-icon { font-size: 56px; margin-bottom: 20px; animation: apple-pulse 2s ease-in-out infinite; }
    .loading-title { color: #1D1D1F; font-size: 20px; font-weight: 600; margin-bottom: 8px; }
    .loading-subtitle { color: #86868B; font-size: 14px; }
    .loading-dots { display: flex; gap: 6px; margin-top: 24px; }
    .loading-dot { width: 6px; height: 6px; background: #34C759; border-radius: 50%; animation: apple-pulse 1.4s ease-in-out infinite; }
    .loading-dot:nth-child(1) { animation-delay: 0s; }
    .loading-dot:nth-child(2) { animation-delay: 0.2s; }
    .loading-dot:nth-child(3) { animation-delay: 0.4s; }
    </style>
    <div class="loading-container">
        <div class="loading-icon">🌿</div>
        <div class="loading-spinner"></div>
        <div class="loading-title">正在初始化模型</div>
        <div class="loading-subtitle">加载 Mask2Former 语义分割引擎</div>
        <div class="loading-dots"><div class="loading-dot"></div><div class="loading-dot"></div><div class="loading-dot"></div></div>
    </div>
    """,
        unsafe_allow_html=True,
    )


# ============================================================
# 结果卡片
# ============================================================
def render_result_card():
    """渲染 GVI 结果卡片"""
    gvi = st.session_state.gvi_result

    if gvi >= 0.3:
        level, level_color = "优秀", "#34C759"
    elif gvi >= 0.15:
        level, level_color = "良好", "#FF9500"
    else:
        level, level_color = "较低", "#FF3B30"

    st.markdown(
        f"""
    <div style="background:#FFFFFF;border-radius:12px;padding:16px;box-shadow:0 2px 8px rgba(0,0,0,0.06);margin-top:16px;">
        <div style="font-size:13px;color:#86868B;margin-bottom:8px;">分析结果</div>
        <div style="display:flex;justify-content:space-between;align-items:center;">
            <div>
                <div style="font-size:28px;font-weight:700;color:#1D1D1F;">{gvi * 100:.1f}%</div>
                <div style="font-size:12px;color:#86868B;">植被占比</div>
            </div>
            <div style="text-align:right;">
                <div style="font-size:18px;font-weight:600;color:{level_color};">{level}</div>
                <div style="font-size:12px;color:#86868B;">绿化等级</div>
            </div>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f'<div style="font-size:12px;color:#86868B;margin-top:8px;">GVI = {gvi:.4f}</div>',
        unsafe_allow_html=True,
    )

    if st.session_state.original_size != st.session_state.processed_size:
        st.markdown(
            f"""
        <div style="font-size:11px;color:#FF9500;margin-top:4px;">
            ⚠️ 图像已自动缩放：{st.session_state.original_size[0]}×{st.session_state.original_size[1]} 
            → {st.session_state.processed_size[0]}×{st.session_state.processed_size[1]} 
            (最大 1024px)
        </div>
        """,
            unsafe_allow_html=True,
        )

    csv_data = (
        pd.DataFrame(
            [
                {
                    "文件名": st.session_state.uploaded_name or "image",
                    "绿视指数": round(gvi, 4),
                    "植被占比": round(gvi * 100, 2),
                }
            ]
        )
        .to_csv(index=False)
        .encode("utf-8-sig")
    )

    st.download_button(
        "📥 下载结果",
        data=csv_data,
        file_name="gvi_result.csv",
        mime="text/csv",
        use_container_width=True,
    )


# ============================================================
# 图像查看器
# ============================================================
def render_image_viewer():
    """渲染图像叠加查看器"""
    st.session_state.opacity = st.slider(
        "植被图层透明度",
        min_value=0.0,
        max_value=1.0,
        value=st.session_state.opacity,
        step=0.05,
    )

    blended = blend_images(
        st.session_state.display_image,
        st.session_state.segmentation_rgb,
        st.session_state.opacity,
    )

    img_col1, img_col2, img_col3 = st.columns(3, gap="large")
    with img_col1:
        st.image(
            st.session_state.display_image, caption="原始图像", use_container_width=True
        )
    with img_col2:
        st.image(
            blended,
            caption=f"叠加 ({st.session_state.opacity * 100:.0f}%)",
            use_container_width=True,
        )
    with img_col3:
        st.image(
            st.session_state.segmentation_rgb,
            caption="分割结果",
            use_container_width=True,
        )

    st.markdown(
        """
    <div style="background:#F5F5F7;border-radius:8px;padding:12px;font-size:12px;color:#86868B;">
        <strong>图例：</strong>
        🌳 植被（绿色）- 树、草、植物、花、棕榈树 &nbsp;|&nbsp;
        ⬜ 非植被（灰色）- 天空、建筑、道路等
    </div>
    """,
        unsafe_allow_html=True,
    )


# ============================================================
# 统一图像上传与处理界面
# ============================================================
def render_unified_interface(processor, model):
    """渲染统一的图像处理界面（单张/多张同一逻辑）"""
    main_col1, main_col2 = st.columns([1, 2], gap="large")

    # ========== 左侧：上传与控制 ==========
    with main_col1:
        st.markdown("#### ⚙️ 控制面板")

        uploaded_files = st.file_uploader(
            "上传图像",
            type=["jpg", "jpeg", "png", "bmp", "tif", "tiff"],
            accept_multiple_files=True,
            key="image_uploader",
            help=f"支持 JPG, PNG, BMP, TIFF 格式，可单选或多选，最大 {MAX_UPLOAD_SIZE_MB}MB",
        )
        is_panoramic = st.checkbox(
            "全景图像模式", value=False, help="裁剪底部 20% 并分块分析"
        )

        if uploaded_files:
            file_count = len(uploaded_files)
            total_size_kb = sum(len(f.getvalue()) for f in uploaded_files) / 1024

            st.markdown(
                f"""
            <div style="background:#F5F5F7;border-radius:10px;padding:12px;margin:8px 0;">
                <div style="font-size:13px;color:#86868B;">已选择</div>
                <div style="font-size:15px;color:#1D1D1F;font-weight:500;">{file_count} 个图像</div>
                <div style="font-size:12px;color:#86868B;">{total_size_kb:.1f} KB</div>
            </div>
            """,
                unsafe_allow_html=True,
            )

            if st.button("🔍 开始分析", type="primary", use_container_width=True):
                with st.spinner("正在处理图像..."):
                    results, images_cache = process_all_uploaded_images(
                        uploaded_files, is_panoramic, processor, model
                    )
                    st.session_state.all_results = results
                    st.session_state.all_images = images_cache
                    st.session_state.selected_index = 0
                    st.session_state.processing_complete = True
                    st.rerun()

        # 显示处理结果列表
        if st.session_state.processing_complete and st.session_state.all_results:
            st.markdown("---")
            st.markdown(f"#### 📊 处理结果 ({len(st.session_state.all_results)} 个)")

            success_count = len(
                [r for r in st.session_state.all_results if r["状态"] == "✅ 成功"]
            )
            st.markdown(
                f"**成功**: {success_count}/{len(st.session_state.all_results)}"
            )

            # 结果显示列表
            for idx, result in enumerate(st.session_state.all_results):
                if result["状态"] == "✅ 成功":
                    # 选中高亮
                    is_selected = st.session_state.selected_index == idx
                    bg_color = "#F5F5F7" if is_selected else "#FFFFFF"
                    border_color = "#34C759" if is_selected else "transparent"

                    if st.button(
                        f"{result['文件名']}\nGVI: {result['绿视指数'] * 100:.1f}%",
                        key=f"result_{idx}",
                        use_container_width=True,
                    ):
                        st.session_state.selected_index = idx
                        st.rerun()

            # 下载所有结果
            if success_count > 0:
                df = pd.DataFrame(
                    [
                        {
                            "文件名": r["文件名"],
                            "绿视指数": r["绿视指数"],
                            "植被占比 (%)": r["植被占比 (%)"],
                        }
                        for r in st.session_state.all_results
                        if r["状态"] == "✅ 成功"
                    ]
                )
                csv_data = df.to_csv(index=False).encode("utf-8-sig")
                st.download_button(
                    "📥 下载全部结果",
                    data=csv_data,
                    file_name="gvi_all_results.csv",
                    mime="text/csv",
                    use_container_width=True,
                )

    # ========== 右侧：图像预览 ==========
    with main_col2:
        st.markdown("#### 🖼️ 图像预览")

        # 根据选中索引显示对应图像
        if st.session_state.processing_complete and st.session_state.all_results:
            current_idx = st.session_state.selected_index

            if current_idx < len(st.session_state.all_results):
                current_result = st.session_state.all_results[current_idx]
                filename = current_result["文件名"]

                if filename in st.session_state.all_images:
                    img_data = st.session_state.all_images[filename]

                    # 更新会话状态
                    st.session_state.gvi_result = img_data["gvi"]
                    st.session_state.display_image = img_data["original"]
                    st.session_state.segmentation_rgb = img_data["segmentation"]
                    st.session_state.uploaded_name = filename

                    # 显示结果卡片
                    render_result_card()
                    st.markdown("")

                    # 显示图像查看器
                    render_image_viewer()

                    # 导航按钮
                    nav_col1, nav_col2, nav_col3 = st.columns(3)
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
                    st.error(f"未找到图像：{filename}")
            else:
                st.warning("无效的图像索引")
        else:
            st.markdown(
                """
            <div style="background:#F5F5F7;border-radius:12px;padding:80px 40px;text-align:center;">
                <div style="font-size:48px;margin-bottom:16px;">📷</div>
                <div style="font-size:16px;color:#86868B;">上传图像开始分析</div>
            </div>
            """,
                unsafe_allow_html=True,
            )


# ============================================================
# 主函数
# ============================================================
def main():
    """主函数 - 应用入口"""
    init_session_state()

    # 页头
    header_col1, header_col2, header_col3 = st.columns([1, 3, 1])

    with header_col1:
        st.markdown(
            """
        <div style="display:flex;align-items:center;gap:8px;padding:8px 0;">
            <span style="font-size:28px;">🌿</span>
            <span style="font-size:20px;font-weight:600;color:#1D1D1F;">SimpleGVI</span>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with header_col2:
        st.markdown(
            """
        <div style="text-align:center;padding:8px 0;">
            <span style="font-size:15px;color:#86868B;">绿视指数计算工具 · 基于 Mask2Former</span>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with header_col3:
        if st.session_state.model_loaded:
            st.markdown(
                """
            <div style="text-align:right;padding:8px 0;">
                <span style="color:#34C759;font-size:14px;">✅ 模型就绪</span>
            </div>
            """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                """
            <div style="text-align:right;padding:8px 0;">
                <span style="color:#FF9500;font-size:14px;">⏳ 加载中...</span>
            </div>
            """,
                unsafe_allow_html=True,
            )

    st.markdown(
        '<div style="height:1px;background:rgba(0,0,0,0.1);margin:8px 0 16px 0;"></div>',
        unsafe_allow_html=True,
    )

    # 模型加载
    if not st.session_state.model_loaded:
        render_loading_animation()
        try:
            processor, model = load_models()
            st.session_state.model_loaded = True
            st.session_state.processor = processor
            st.session_state.model = model
            st.rerun()
        except Exception as e:
            logger.error(f"模型加载失败：{e}")
            st.error(f"❌ 模型加载失败：{str(e)}")
            st.info("请确保已安装必要的依赖并可以访问 HuggingFace 模型仓库。")
            return
        return

    # 获取模型
    try:
        processor = st.session_state.processor
        model = st.session_state.model
    except KeyError:
        st.error("模型未正确加载，请刷新页面。")
        return

    # 统一处理界面（不再区分单张/批量模式）
    render_unified_interface(processor, model)

    # 页脚
    st.markdown(
        """
    <div style="text-align:center;padding:24px 0;color:#86868B;font-size:12px;">
        SimpleGVI · 绿视指数计算工具 · Powered by Mask2Former
    </div>
    """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
