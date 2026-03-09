"""
SimpleGVI - 绿视指数计算工具
Streamlit Web GUI Application
"""

import os
import tempfile
import pandas as pd
import streamlit as st
from PIL import Image
import numpy as np

# 设置页面配置（必须在第一个Streamlit命令）
st.set_page_config(
    page_title="SimpleGVI - 绿视指数计算工具",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# 模型加载（带缓存）
# ============================================================
@st.cache_resource(show_spinner=False)
def load_models():
    """
    加载Mask2Former模型（带缓存，只加载一次）
    """
    from modules.gvi_calculator import get_models

    return get_models()


# ============================================================
# 会话状态初始化
# ============================================================
def init_session_state():
    """初始化会话状态"""
    if "results" not in st.session_state:
        st.session_state.results = []
    if "processed_count" not in st.session_state:
        st.session_state.processed_count = 0


# ============================================================
# 图像处理函数
# ============================================================
def process_single_image(uploaded_file, is_panoramic, processor, model):
    """
    处理单张图像

    参数:
        uploaded_file: Streamlit上传的文件对象
        is_panoramic: 是否为全景图像
        processor: 图像处理器
        model: 分割模型

    返回:
        tuple: (gvi, segmentation, original_image, segmentation_rgb) 或 None（如果出错）
    """
    try:
        # 创建临时文件保存上传的图像
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=os.path.splitext(uploaded_file.name)[1]
        ) as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_path = tmp_file.name

        try:
            # 打开原始图像用于显示
            original_image = Image.open(tmp_path)

            # 处理图像并计算GVI
            from modules.gvi_calculator import process_image
            from modules.visualization import segmentation_to_color

            with st.spinner("正在分析图像，请稍候..."):
                gvi, segmentation = process_image(
                    tmp_path, is_panoramic, processor, model
                )

            # 转换分割结果为彩色图像
            segmentation_rgb = segmentation_to_color(segmentation)

            return gvi, segmentation, original_image, segmentation_rgb

        finally:
            # 清理临时文件
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    except Exception as e:
        st.error(f"处理图像时出错: {str(e)}")
        return None


def process_batch_images(uploaded_files, is_panoramic, processor, model):
    """
    批量处理图像

    参数:
        uploaded_files: Streamlit上传的文件列表
        is_panoramic: 是否为全景图像
        processor: 图像处理器
        model: 分割模型

    返回:
        list: 处理结果列表
    """
    from modules.gvi_calculator import process_image

    results = []
    total_files = len(uploaded_files)

    progress_bar = st.progress(0)
    status_text = st.empty()

    for idx, uploaded_file in enumerate(uploaded_files):
        # 更新进度
        progress = (idx + 1) / total_files
        progress_bar.progress(progress)
        status_text.text(f"正在处理: {uploaded_file.name} ({idx + 1}/{total_files})")

        try:
            # 创建临时文件
            with tempfile.NamedTemporaryFile(
                delete=False, suffix=os.path.splitext(uploaded_file.name)[1]
            ) as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_path = tmp_file.name

            try:
                # 处理图像
                gvi, segmentation = process_image(
                    tmp_path, is_panoramic, processor, model
                )

                # 保存结果
                results.append(
                    {
                        "文件名": uploaded_file.name,
                        "绿视指数 (GVI)": round(gvi, 4),
                        "植被占比 (%)": round(gvi * 100, 2),
                        "图像类型": "全景图像" if is_panoramic else "普通图像",
                    }
                )

            finally:
                # 清理临时文件
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)

        except Exception as e:
            results.append(
                {
                    "文件名": uploaded_file.name,
                    "绿视指数 (GVI)": None,
                    "植被占比 (%)": None,
                    "图像类型": "全景图像" if is_panoramic else "普通图像",
                    "错误": str(e),
                }
            )

    # 清除进度显示
    progress_bar.empty()
    status_text.empty()

    return results


# ============================================================
# UI 组件
# ============================================================
def render_sidebar():
    """渲染侧边栏配置"""
    with st.sidebar:
        st.title("⚙️ 设置")
        st.markdown("---")

        # 模式选择
        mode = st.radio(
            "处理模式",
            options=["单图处理", "批量处理"],
            index=0,
            help="选择单张图像处理或批量处理多张图像",
        )

        st.markdown("---")

        # 图像类型设置
        is_panoramic = st.checkbox(
            "全景图像模式",
            value=False,
            help="启用此项将使用全景图像处理算法（裁剪底部20%并分块分析）",
        )

        # 显示分割结果设置
        show_segmentation = st.checkbox(
            "显示分割可视化", value=True, help="显示语义分割结果的可视化对比图"
        )

        st.markdown("---")

        # 清除结果按钮
        if st.button("🗑️ 清除结果", use_container_width=True):
            st.session_state.results = []
            st.session_state.processed_count = 0
            st.success("已清除所有结果！")
            st.rerun()

        st.markdown("---")

        # 关于信息
        with st.expander("ℹ️ 关于 SimpleGVI"):
            st.markdown("""
            **SimpleGVI** 是一个绿视指数(GVI)计算工具。

            **绿视指数**衡量城市环境中可见绿化的比例，通过计算图像中植被区域占整个图像的百分比来定量化视野中的绿色元素。

            **技术原理:**
            - 使用 Mask2Former 模型进行语义分割
            - 自动识别植被区域（包括树(tree:4)、草(grass:9)、植物(plant:17)、花(flower:66)、棕榈树(palm:72)等类别）
            - 计算植被像素占比作为GVI值
            """)

    return mode, is_panoramic, show_segmentation


def render_single_mode(is_panoramic, show_segmentation, processor, model):
    """渲染单图处理模式"""
    st.header("📷 单图处理")
    st.markdown("上传单张图像计算绿视指数(GVI)")

    # 文件上传
    uploaded_file = st.file_uploader(
        "选择图像文件",
        type=["jpg", "jpeg", "png", "bmp", "tif", "tiff"],
        help="支持的格式: JPG, JPEG, PNG, BMP, TIF, TIFF",
        key="single_uploader",
    )

    if uploaded_file is not None:
        # 显示文件信息
        col_info1, col_info2, col_info3 = st.columns(3)
        with col_info1:
            st.metric("文件名", uploaded_file.name)
        with col_info2:
            file_size = len(uploaded_file.getvalue()) / 1024  # KB
            st.metric("文件大小", f"{file_size:.1f} KB")
        with col_info3:
            st.metric("图像类型", "全景图像" if is_panoramic else "普通图像")

        st.markdown("---")

        # 处理图像
        result = process_single_image(uploaded_file, is_panoramic, processor, model)

        if result:
            gvi, segmentation, original_image, segmentation_rgb = result

            # 显示GVI结果
            st.subheader("📊 分析结果")

            col_gvi1, col_gvi2, col_gvi3 = st.columns(3)
            with col_gvi1:
                st.metric("绿视指数 (GVI)", f"{gvi:.4f}")
            with col_gvi2:
                st.metric("植被占比", f"{gvi * 100:.2f}%")
            with col_gvi3:
                if gvi >= 0.3:
                    level = "🟢 优秀"
                elif gvi >= 0.15:
                    level = "🟡 良好"
                else:
                    level = "🔴 较低"
                st.metric("绿化等级", level)

            st.markdown("---")

            # 显示分割可视化
            if show_segmentation:
                st.subheader("🔍 分割可视化")

                col1, col2 = st.columns(2)
                with col1:
                    st.image(
                        original_image, caption="原始图像", use_container_width=True
                    )
                with col2:
                    st.image(
                        segmentation_rgb,
                        caption="分割结果 (绿色区域为植被)",
                        use_container_width=True,
                    )

                st.markdown("""
                **图例说明:**
                - 🌳 **五种植物类别**（绿色系）：树(tree)、草(grass)、植物(plant)、花(flower)、棕榈树(palm)
                - ⬜ **非植物**（灰色）：天空、建筑物、道路、交通工具等所有其他类别
                """)

            # 下载按钮
            st.markdown("---")
            st.subheader("💾 下载结果")

            # 准备下载数据
            result_df = pd.DataFrame(
                [
                    {
                        "文件名": uploaded_file.name,
                        "绿视指数 (GVI)": round(gvi, 4),
                        "植被占比 (%)": round(gvi * 100, 2),
                        "图像类型": "全景图像" if is_panoramic else "普通图像",
                    }
                ]
            )

            csv = result_df.to_csv(index=False).encode("utf-8-sig")
            st.download_button(
                label="📥 下载CSV结果",
                data=csv,
                file_name=f"gvi_result_{uploaded_file.name.split('.')[0]}.csv",
                mime="text/csv",
                use_container_width=True,
            )


def render_batch_mode(is_panoramic, processor, model):
    """渲染批量处理模式"""
    st.header("📁 批量处理")
    st.markdown("上传多张图像进行批量GVI计算")

    # 文件上传（允许多个文件）
    uploaded_files = st.file_uploader(
        "选择图像文件（可多选）",
        type=["jpg", "jpeg", "png", "bmp", "tif", "tiff"],
        accept_multiple_files=True,
        help="支持批量上传，一次可选择多个图像文件",
        key="batch_uploader",
    )

    if uploaded_files:
        st.info(f"已选择 {len(uploaded_files)} 个文件")

        # 显示文件列表
        with st.expander("📋 查看文件列表"):
            file_data = []
            for f in uploaded_files:
                file_size = len(f.getvalue()) / 1024
                file_data.append({"文件名": f.name, "大小 (KB)": f"{file_size:.1f}"})
            st.dataframe(file_data, use_container_width=True)

        # 开始处理按钮
        if st.button("🚀 开始批量处理", type="primary", use_container_width=True):
            # 处理图像
            results = process_batch_images(
                uploaded_files, is_panoramic, processor, model
            )

            # 保存到会话状态
            st.session_state.results = results
            st.session_state.processed_count = len(
                [r for r in results if r.get("绿视指数 (GVI)") is not None]
            )

        # 显示结果
        if st.session_state.results:
            st.markdown("---")
            st.subheader("📊 处理结果")

            # 统计信息
            total = len(st.session_state.results)
            success = len(
                [
                    r
                    for r in st.session_state.results
                    if r.get("绿视指数 (GVI)") is not None
                ]
            )
            failed = total - success

            col_stat1, col_stat2, col_stat3 = st.columns(3)
            with col_stat1:
                st.metric("总文件数", total)
            with col_stat2:
                st.metric("成功处理", success)
            with col_stat3:
                st.metric("处理失败", failed)

            # 结果显示表格
            df = pd.DataFrame(st.session_state.results)
            st.dataframe(df, use_container_width=True)

            # 统计图表
            if success > 0:
                st.markdown("---")
                st.subheader("📈 统计分析")

                # 计算统计数据
                gvi_values = [
                    r["绿视指数 (GVI)"]
                    for r in st.session_state.results
                    if r.get("绿视指数 (GVI)") is not None
                ]
                if gvi_values:
                    col_chart1, col_chart2 = st.columns(2)
                    with col_chart1:
                        st.metric("平均GVI", f"{np.mean(gvi_values):.4f}")
                        st.metric("最高GVI", f"{np.max(gvi_values):.4f}")
                        st.metric("最低GVI", f"{np.min(gvi_values):.4f}")
                    with col_chart2:
                        st.metric("GVI标准差", f"{np.std(gvi_values):.4f}")
                        st.metric("中位数GVI", f"{np.median(gvi_values):.4f}")

                    # 直方图
                    import plotly.express as px

                    fig = px.histogram(
                        x=[v * 100 for v in gvi_values],
                        nbins=20,
                        labels={"x": "植被占比 (%)"},
                        title="GVI分布直方图",
                        color_discrete_sequence=["#2ecc71"],
                    )
                    st.plotly_chart(fig, use_container_width=True)

            # 下载按钮
            st.markdown("---")
            st.subheader("💾 导出结果")

            csv = df.to_csv(index=False).encode("utf-8-sig")
            st.download_button(
                label="📥 下载CSV结果文件",
                data=csv,
                file_name="gvi_results.csv",
                mime="text/csv",
                use_container_width=True,
            )


# ============================================================
# 主函数
# ============================================================
def main():
    """主函数"""
    # 初始化会话状态
    init_session_state()

    # 页面标题
    st.title("🌿 SimpleGVI")
    st.subheader("绿视指数计算工具")
    st.markdown("基于 Mask2Former 语义分割模型计算图像绿视指数(GVI)")
    st.markdown("---")

    # 加载模型
    try:
        with st.spinner("正在加载AI模型，请稍候..."):
            processor, model = load_models()
        st.success("✅ 模型加载成功！")
    except Exception as e:
        st.error(f"❌ 模型加载失败: {str(e)}")
        st.info("请确保已安装必要的依赖并可以访问 HuggingFace 模型仓库。")
        return

    st.markdown("---")

    # 渲染侧边栏并获取配置
    mode, is_panoramic, show_segmentation = render_sidebar()

    # 根据模式渲染不同界面
    if mode == "单图处理":
        render_single_mode(is_panoramic, show_segmentation, processor, model)
    else:
        render_batch_mode(is_panoramic, processor, model)

    # 页脚
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666; padding: 20px;'>
            <p>SimpleGVI - 绿视指数计算工具</p>
            <p style='font-size: 12px;'>Powered by Mask2Former Semantic Segmentation</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
