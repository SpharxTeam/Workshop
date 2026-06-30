# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
# 03_data 模块配置文件
# 说明：数据管理页面

import streamlit as st
import pandas as pd

st.title("📁 数据管理")

st.header("数据集列表")
# 模拟数据集列表
datasets = pd.DataFrame({
    '数据集ID': ['DS001', 'DS002', 'DS003'],
    '创建时间': ['2024-01-15', '2024-01-16', '2024-01-17'],
    '状态': ['已完成', '处理中', '待处理'],
    '大小(GB)': [12.5, 8.2, 15.1]
})

st.dataframe(datasets)

st.header("数据操作")
col1, col2 = st.columns(2)

with col1:
    if st.button("新建数据集"):
        st.info("创建新数据集...")

with col2:
    if st.button("导出数据"):
        st.success("开始导出数据...")