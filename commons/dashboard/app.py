# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
# 监控面板主应用
# 说明：监控面板主应用

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import logging

# 配置页面
st.set_page_config(
    page_title="Workshop 监控面板",
    page_icon="📊",
    layout="wide"
)

# 页面标题
st.title("📊 Workshop 数据处理监控面板")

# 侧边栏
st.sidebar.header("导航")
page = st.sidebar.selectbox(
    "选择页面",
    ["实时监控", "数据概览", "处理状态", "系统配置"]
)

if page == "实时监控":
    st.header("🎥 实时数据监控")
    
    # 模拟实时数据
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("处理中会话", "3", "+1")
    with col2:
        st.metric("今日处理帧数", "1,247", "+156")
    with col3:
        st.metric("系统健康度", "98%", "正常")
    
    # 实时图表
    st.subheader("处理速率趋势")
    # 这里应该连接到实际的监控数据源
    
elif page == "数据概览":
    st.header("📂 数据统计概览")
    
    # 数据表格
    data = {
        '数据类型': ['彩色图像', '深度图像', 'IMU数据', '标注数据'],
        '总数量': [15420, 15420, 46260, 8934],
        '今日新增': [156, 156, 468, 89],
        '存储大小(GB)': [12.5, 8.3, 0.2, 1.1]
    }
    df = pd.DataFrame(data)
    st.table(df)
    
elif page == "处理状态":
    st.header("⚙️ 管道处理状态")
    
    # 管道状态卡片
    pipes = ["00_ingest", "01_quality", "02_enhance", "03_calibrate", "04_pack", "05_delivery"]
    
    for i, pipe in enumerate(pipes):
        with st.expander(f"Pipeline {pipe}"):
            st.progress((i + 1) * 15)
            st.text(f"状态: 运行中")
            st.text(f"处理速度: {(i + 1) * 2} FPS")

elif page == "系统配置":
    st.header("🔧 系统配置")
    
    # 配置选项
    st.subheader("相机配置")
    camera_count = st.number_input("相机数量", min_value=1, max_value=10, value=2)
    fps = st.slider("帧率(FPS)", min_value=15, max_value=60, value=30)
    
    st.subheader("处理配置")
    enable_privacy = st.checkbox("启用隐私保护", value=True)
    quality_threshold = st.slider("质量阈值", min_value=0.0, max_value=1.0, value=0.7)

# 页脚
st.markdown("---")
st.caption(f"最后更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")