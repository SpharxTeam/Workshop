# Copyright (c) 2026 SPHARX . All Rights Reserved.
# From data intelligence emerges.
# 始于数据，终于智能。

"""数据采集页面"""
import streamlit as st

st.title("📷 数据采集监控")

st.header("相机状态")
# 相机状态显示
cameras = ["cam1", "cam2", "cam3"]
for cam in cameras:
    with st.expander(f"相机 {cam}"):
        st.text("状态: 在线")
        st.text("分辨率: 640x480")
        st.text("帧率: 30 FPS")

st.header("采集控制")
if st.button("开始采集"):
    st.success("开始数据采集...")
    
if st.button("停止采集"):
    st.warning("停止数据采集...")