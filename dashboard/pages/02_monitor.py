"""系统监控页面"""
import streamlit as st
import psutil
import time

st.title("🖥️ 系统监控")

# 系统资源
col1, col2, col3, col4 = st.columns(4)

with col1:
    cpu_percent = psutil.cpu_percent()
    st.metric("CPU使用率", f"{cpu_percent}%", 
              delta=f"{cpu_percent-50}%" if cpu_percent > 50 else None)

with col2:
    memory = psutil.virtual_memory()
    st.metric("内存使用率", f"{memory.percent}%", 
              delta=f"{memory.percent-70}%" if memory.percent > 70 else None)

with col3:
    disk = psutil.disk_usage('/')
    st.metric("磁盘使用率", f"{disk.percent}%", 
              delta=f"{disk.percent-80}%" if disk.percent > 80 else None)

with col4:
    st.metric("网络IO", "正常", "稳定")

# 资源使用图表
st.subheader("资源使用趋势")
# 这里应该集成实际的监控图表