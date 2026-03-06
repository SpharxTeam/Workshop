# 用户指南

## 流水线模块概览

workshop 包含以下核心模块：

- **ingest**: 解析 `.bag` 文件，提取 RGB 图像、深度图和 IMU 数据
- **quality**: 质量检测（模糊、曝光、丢帧）
- **enhance**: 目标检测（YOLOv8）
- **calibrate**: 相机标定（棋盘格）
- **pack**: 数据集打包
- **delivery**: 数据交付（预留）

## 配置说明

配置文件位于 `common/configs/` 目录，支持全局配置和模块特定配置。