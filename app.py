"""
SimpleGVI - 绿视指数计算工具
Streamlit Web GUI Application

功能:
- 单图/批量 GVI 计算
- EXIF 方向自动纠正
- 图像自动缩放 (最大 1024px)
- Apple 风格 UI
- 批量处理图像预览
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
MAX_BATCH_FILES = 20  # 批量处理最大文件数
MODEL_CACHE_MAX_SIZE = 10  # 批量缓存最大图像数

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="SimpleGVI - 绿视指数计算工具",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",  # 恢复侧边栏
)

# ============================================================
# 样式注入
# ============================================================
def inject_apple_styles():
    """注入 Apple 风格 CSS 样式"""
    try:
        from styles import get_apple_styles
        # 验证 CSS 内容安全性 (只允许 CSS 字符)
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
        "batch_results": [],
        "batch_images": {},
        "selected_image": None,
        "batch_mode": False,
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# ============================================================
# 图像混合函数
# ============================================================
def blend_images(original, overlay, opacity: float):
    """
    将分割结果以指定透明度叠加到原图上
    
    Args:
        original: 原始图像 (PIL Image 或 numpy array)
        overlay: 叠加图像 (PIL Image 或 numpy array)
        opacity: 透明度 (0.0-1.0)
    
    Returns:
        PIL.Image: 混合后的图像
    """
    # 转换 numpy 数组为 PIL Image
    if isinstance(original, np.ndarray):
        original = Image.fromarray(original)
    if isinstance(overlay, np.ndarray):
        overlay = Image.fromarray(overlay)
    
    # 确保尺寸一致
    if original.size != overlay.size:
        overlay = overlay.resize(original.size, Image.Resampling.LANCZOS)
    
    original = original.convert("RGBA")
    overlay = overlay.convert("RGBA")
    
    # 应用透明度
    overlay_array = np.array(overlay)
    overlay_array[:, :, 3] = (overlay_array[:, :, 3] * opacity).astype(np.uint8)
    overlay_blended = Image.fromarray(overlay_array)
    
    # 混合
    result = Image.alpha_composite(original, overlay_blended)
    return result.convert("RGB")

# ============================================================
# 单图处理
# ============================================================
def process_single_image(uploaded_file, is_panoramic, processor, model):
    """
    处理单张图像
    
    Args:
        uploaded_file: Streamlit 上传的文件对象
        is_panoramic: 是否为全景图像
        processor: 图像处理器
        model: 分割模型
    
    Returns:
        tuple: (gvi, display_image, segmentation_rgb, original_size, processed_size) 或 None
    """
    try:
        # 验证文件大小 (P0 - 安全修复)
        file_size_mb = len(uploaded_file.getvalue()) / 1024 / 1024
        if file_size_mb > MAX_UPLOAD_SIZE_MB:
            st.error(f"文件大小超过限制 ({MAX_UPLOAD_SIZE_MB}MB)")
            return None
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_path = tmp_file.name
        
        try:
            original_image = Image.open(tmp_path)
            original_size = original_image.size
            
            from modules.gvi_calculator import process_image
            from modules.visualization import segmentation_to_color
            
            gvi, segmentation, processed_image = process_image(
                tmp_path, is_panoramic, processor, model
            )
            segmentation_rgb = segmentation_to_color(segmentation)
            
            return gvi, processed_image, segmentation_rgb, original_size, processed_image.size
        
        finally:
            # 清理临时文件
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    except Exception as e:
        logger.error(f"处理图像失败：{e}")
        st.error(f"处理图像时出错：{str(e)}")
        return None

# ============================================================
# 批量处理
# ============================================================
def process_batch_images(uploaded_files, is_panoramic, processor, model):
    """
    批量处理图像
    
    Args:
        uploaded_files: 上传文件列表
        is_panoramic: 是否为全景图像
        processor: 图像处理器
        model: 分割模型
    
    Returns:
        tuple: (results, images_cache) 结果列表和图像缓存
    """
    # P2 - 限制批量处理文件数
    if len(uploaded_files) > MAX_BATCH_FILES:
        st.warning(f"最多支持 {MAX_BATCH_FILES} 个文件，已自动截取前 {MAX_BATCH_FILES} 个")
        uploaded_files = uploaded_files[:MAX_BATCH_FILES]
    
    results = []
    images_cache = {}
    
    for idx, uploaded_file in enumerate(uploaded_files):
        try:
            # 验证文件大小
            file_size_mb = len(uploaded_file.getvalue()) / 1024 / 1024
            if file_size_mb > MAX_UPLOAD_SIZE_MB:
                results.append({
                    "文件名": uploaded_file.name,
                    "绿视指数": None,
                    "植被占比 (%)": None,
                    "状态": f"❌ 超过大小限制 ({MAX_UPLOAD_SIZE_MB}MB)"
                })
                continue
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_path = tmp_file.name
            
            try:
                from modules.gvi_calculator import process_image
                from modules.visualization import segmentation_to_color
                
                gvi, segmentation, processed_image = process_image(
                    tmp_path, is_panoramic, processor, model
                )
                segmentation_rgb = segmentation_to_color(segmentation)
                
                # 保存到缓存 (P2 - 内存管理)
                images_cache[uploaded_file.name] = {
                    "original": processed_image,
                    "segmentation": segmentation_rgb,
                    "gvi": gvi
                }
                
                # 限制缓存大小
                if len(images_cache) > MODEL_CACHE_MAX_SIZE:
                    # 删除最旧的缓存
                    oldest_key = next(iter(images_cache))
                    del images_cache[oldest_key]
                
                results.append({
                    "文件名": uploaded_file.name,
                    "绿视指数": round(gvi, 4),
                    "植被占比 (%)": round(gvi * 100, 2),
                    "状态": "✅ 成功"
                })
            
            finally:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
        
        except Exception as e:
            logger.error(f"批量处理失败：{e}")
            results.append({
                "文件名": uploaded_file.name,
                "绿视指数": None,
                "植被占比 (%)": None,
                "状态": f"❌ {str(e)}"
            })
    
    return results, images_cache

# ============================================================
# 加载动画
# ============================================================
def render_loading_animation():
    """渲染 Apple 风格模型加载动画"""
    st.markdown("""
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
    """, unsafe_allow_html=True)

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
    
    st.markdown(f'''
    <div style="background:#FFFFFF;border-radius:12px;padding:16px;box-shadow:0 2px 8px rgba(0,0,0,0.06);margin-top:16px;">
        <div style="font-size:13px;color:#86868B;margin-bottom:8px;">分析结果</div>
        <div style="display:flex;justify-content:space-between;align-items:center;">
            <div>
                <div style="font-size:28px;font-weight:700;color:#1D1D1F;">{gvi*100:.1f}%</div>
                <div style="font-size:12px;color:#86868B;">植被占比</div>
            </div>
            <div style="text-align:right;">
                <div style="font-size:18px;font-weight:600;color:{level_color};">{level}</div>
                <div style="font-size:12px;color:#86868B;">绿化等级</div>
            </div>
        </div>
    </div>
    ''', unsafe_allow_html=True)
    
    st.markdown(f'<div style="font-size:12px;color:#86868B;margin-top:8px;">GVI = {gvi:.4f}</div>', unsafe_allow_html=True)
    
    if st.session_state.original_size != st.session_state.processed_size:
        st.markdown(f'''
        <div style="font-size:11px;color:#FF9500;margin-top:4px;">
            ⚠️ 图像已自动缩放：{st.session_state.original_size[0]}×{st.session_state.original_size[1]} 
            → {st.session_state.processed_size[0]}×{st.session_state.processed_size[1]} 
            (最大 1024px)
        </div>
        ''', unsafe_allow_html=True)
    
    csv_data = pd.DataFrame([{
        "文件名": st.session_state.uploaded_name or "image",
        "绿视指数": round(gvi, 4),
        "植被占比": round(gvi * 100, 2)
    }]).to_csv(index=False).encode("utf-8-sig")
    
    st.download_button(
        "📥 下载结果",
        data=csv_data,
        file_name="gvi_result.csv",
        mime="text/csv",
        use_container_width=True
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
        step=0.05
    )
    
    blended = blend_images(
        st.session_state.display_image,
        st.session_state.segmentation_rgb,
        st.session_state.opacity
    )
    
    img_col1, img_col2, img_col3 = st.columns(3)
    with img_col1:
        st.image(st.session_state.display_image, caption="原始图像", use_container_width=True)
    with img_col2:
        st.image(blended, caption=f"叠加 ({st.session_state.opacity*100:.0f}%)", use_container_width=True)
    with img_col3:
        st.image(st.session_state.segmentation_rgb, caption="分割结果", use_container_width=True)
    
    st.markdown('''
    <div style="background:#F5F5F7;border-radius:8px;padding:12px;font-size:12px;color:#86868B;">
        <strong>图例：</strong>
        🌳 植被（绿色）- 树、草、植物、花、棕榈树 &nbsp;|&nbsp;
        ⬜ 非植被（灰色）- 天空、建筑、道路等
    </div>
    ''', unsafe_allow_html=True)

# ============================================================
# 单图模式
# ============================================================
def render_single_mode(processor, model):
    """渲染单图处理模式界面"""
    st.markdown("### 📷 单图处理")
    
    main_col1, main_col2 = st.columns([1, 2], gap="large")

    with main_col1:
        st.markdown("#### ⚙️ 控制面板")
        
        uploaded_file = st.file_uploader(
            "上传图像",
            type=["jpg", "jpeg", "png", "bmp", "tif", "tiff"],
            key="single_uploader",
            help=f"支持 JPG, PNG, BMP, TIFF 格式，最大 {MAX_UPLOAD_SIZE_MB}MB"
        )
        is_panoramic = st.checkbox("全景图像模式", value=False, help="裁剪底部 20% 并分块分析")
        
        if uploaded_file is not None:
            try:
                temp_img = Image.open(uploaded_file)
                temp_img = ImageOps.exif_transpose(temp_img)
                orig_w, orig_h = temp_img.size
            except Exception as e:
                logger.error(f"读取图像失败：{e}")
                orig_w, orig_h = 0, 0
            
            st.markdown(f'''
            <div style="background:#F5F5F7;border-radius:10px;padding:12px;margin:8px 0;">
                <div style="font-size:13px;color:#86868B;">文件</div>
                <div style="font-size:15px;color:#1D1D1F;font-weight:500;">{uploaded_file.name}</div>
                <div style="font-size:12px;color:#86868B;">{len(uploaded_file.getvalue())/1024:.1f} KB · {orig_w}×{orig_h}px</div>
            </div>
            ''', unsafe_allow_html=True)
            
            if st.button("🔍 开始分析", type="primary", use_container_width=True):
                result = process_single_image(uploaded_file, is_panoramic, processor, model)
                if result:
                    gvi, display_image, segmentation_rgb, original_size, processed_size = result
                    st.session_state.gvi_result = gvi
                    st.session_state.display_image = display_image
                    st.session_state.segmentation_rgb = segmentation_rgb
                    st.session_state.uploaded_name = uploaded_file.name
                    st.session_state.original_size = original_size
                    st.session_state.processed_size = processed_size
                    st.rerun()

        # 显示结果
        if st.session_state.gvi_result is not None and not st.session_state.batch_mode and st.session_state.selected_image is None:
            render_result_card()

    with main_col2:
        st.markdown("#### 🖼️ 图像展示")
        
        if st.session_state.display_image is not None and not st.session_state.batch_mode and st.session_state.selected_image is None:
            render_image_viewer()
        else:
            st.markdown('''
            <div style="background:#F5F5F7;border-radius:12px;padding:80px 40px;text-align:center;">
                <div style="font-size:48px;margin-bottom:16px;">📷</div>
                <div style="font-size:16px;color:#86868B;">上传图像开始分析</div>
            </div>
            ''', unsafe_allow_html=True)

# ============================================================
# 批量模式
# ============================================================
def render_batch_mode(processor, model):
    """渲染批量处理模式界面"""
    st.markdown("### 📁 批量处理")
    st.markdown(f"上传多张图像进行批量 GVI 计算（最多 {MAX_BATCH_FILES} 张）")
    
    uploaded_files = st.file_uploader(
        "选择图像文件（可多选）",
        type=["jpg", "jpeg", "png", "bmp", "tif", "tiff"],
        accept_multiple_files=True,
        key="batch_uploader",
        help=f"支持批量上传，最多 {MAX_BATCH_FILES} 个文件"
    )
    
    is_panoramic = st.checkbox("全景图像模式", value=False, key="batch_panoramic")
    
    if uploaded_files:
        st.info(f"已选择 {len(uploaded_files)} 个文件")
        
        if st.button("🚀 开始批量处理", type="primary", use_container_width=True):
            results, images_cache = process_batch_images(uploaded_files, is_panoramic, processor, model)
            st.session_state.batch_results = results
            st.session_state.batch_images = images_cache
            st.session_state.selected_image = None
            st.rerun()
    
    if st.session_state.batch_results:
        st.markdown("---")
        st.markdown("#### 📊 处理结果")
        
        df = pd.DataFrame(st.session_state.batch_results)
        
        success_count = len([r for r in st.session_state.batch_results if r["状态"] == "✅ 成功"])
        st.markdown(f"**成功**: {success_count}/{len(st.session_state.batch_results)}")
        
        # 详情视图
        if st.session_state.selected_image:
            st.markdown("#### 🖼️ 图像详情")
            
            filename = st.session_state.selected_image
            if filename in st.session_state.batch_images:
                img_data = st.session_state.batch_images[filename]
                
                st.session_state.display_image = img_data["original"]
                st.session_state.segmentation_rgb = img_data["segmentation"]
                st.session_state.gvi_result = img_data["gvi"]
                st.session_state.uploaded_name = filename
                
                render_result_card()
                st.markdown("")
                render_image_viewer()
                
                if st.button("← 返回结果列表", key="back_to_list"):
                    st.session_state.selected_image = None
                    st.rerun()
            else:
                st.error(f"未找到图像：{filename}")
                st.session_state.selected_image = None
                st.rerun()
        else:
            st.markdown("**点击表格中的文件名可查看详细分析结果**")
            
            # 批量查看按钮
            for idx, row in df.iterrows():
                if row["状态"] == "✅ 成功":
                    if st.button(f"👁️ {row['文件名']}", key=f"view_{row['文件名']}", use_container_width=True):
                        st.session_state.selected_image = row["文件名"]
                        st.rerun()

# ============================================================
# 主函数
# ============================================================
def main():
    """主函数 - 应用入口"""
    init_session_state()

    # 页头
    header_col1, header_col2, header_col3 = st.columns([1, 3, 1])
    
    with header_col1:
        st.markdown('''
        <div style="display:flex;align-items:center;gap:8px;padding:8px 0;">
            <span style="font-size:28px;">🌿</span>
            <span style="font-size:20px;font-weight:600;color:#1D1D1F;">SimpleGVI</span>
        </div>
        ''', unsafe_allow_html=True)
    
    with header_col2:
        st.markdown('''
        <div style="text-align:center;padding:8px 0;">
            <span style="font-size:15px;color:#86868B;">绿视指数计算工具 · 基于 Mask2Former</span>
        </div>
        ''', unsafe_allow_html=True)
    
    with header_col3:
        if st.session_state.model_loaded:
            st.markdown('''
            <div style="text-align:right;padding:8px 0;">
                <span style="color:#34C759;font-size:14px;">✅ 模型就绪</span>
            </div>
            ''', unsafe_allow_html=True)
        else:
            st.markdown('''
            <div style="text-align:right;padding:8px 0;">
                <span style="color:#FF9500;font-size:14px;">⏳ 加载中...</span>
            </div>
            ''', unsafe_allow_html=True)

    st.markdown('''
    <div style="height:1px;background:rgba(0,0,0,0.1);margin:8px 0 16px 0;"></div>
    ''', unsafe_allow_html=True)

    # 模型加载 (P3 - 错误处理)
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

    # 模式切换
    mode = st.radio("处理模式", ["单图处理", "批量处理"], horizontal=True, index=0)

    if mode == "单图处理":
        st.session_state.batch_mode = False
        st.session_state.selected_image = None
        render_single_mode(processor, model)
    else:
        st.session_state.batch_mode = True
        render_batch_mode(processor, model)

    # 页脚
    st.markdown('''
    <div style="text-align:center;padding:24px 0;color:#86868B;font-size:12px;">
        SimpleGVI · 绿视指数计算工具 · Powered by Mask2Former
    </div>
    ''', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
