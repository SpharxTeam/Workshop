#!/bin/bash

# Copyright (c) 2026 SPHARX . All Rights Reserved.
# From data intelligence emerges.
# 始于数据，终于智能。


# RealSense 驱动安装脚本
# 支持 Ubuntu 18.04/20.04/22.04

set -e

echo "🔧 开始安装 RealSense 驱动..."

# 检查操作系统
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    echo "❌ 仅支持 Linux 系统"
    exit 1
fi

# 检查发行版
if ! command -v lsb_release &> /dev/null; then
    echo "❌ 无法识别 Linux 发行版"
    exit 1
fi

DISTRO=$(lsb_release -sc)
echo "✅ 检测到发行版: $DISTRO"

# 注册公钥
echo "🔐 注册 Intel RealSense 公钥..."
sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-key F6E65AC044F831AC80A06380C8B3A55A6F3EFCDE || \
sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-key F6E65AC044F831AC80A06380C8B3A55A6F3EFCDE

# 添加软件源
echo "📦 添加 RealSense 软件源..."
sudo add-apt-repository "deb https://librealsense.intel.com/Debian/apt-repo $(lsb_release -cs) main" -u

# 更新包列表
echo "🔄 更新包列表..."
sudo apt-get update

# 安装核心包
echo "📥 安装 RealSense 核心包..."
sudo apt-get install -y librealsense2-dkms librealsense2-utils

# 安装开发包
echo "📥 安装 RealSense 开发包..."
sudo apt-get install -y librealsense2-dev librealsense2-dbg

# 安装 Python 绑定
echo "📥 安装 Python 绑定..."
pip3 install pyrealsense2

# 验证安装
echo "✅ 验证安装..."
realsense-viewer --version

# 检查 USB 权限
echo "🔧 配置 USB 权限..."
sudo usermod -a -G dialout $USER
sudo usermod -a -G plugdev $USER

# 重新插拔规则
echo 'SUBSYSTEM=="usb", ATTR{idVendor}=="8086", MODE="0666"' | sudo tee /etc/udev/rules.d/99-realsense-libusb.rules
sudo udevadm control --reload-rules && sudo udevadm trigger

echo ""
echo "🎉 RealSense 驱动安装完成！"
echo ""
echo "请执行以下操作："
echo "1. 重新登录或重启系统使权限生效"
echo "2. 重新插拔 RealSense 设备"
echo "3. 运行 'realsense-viewer' 测试设备连接"