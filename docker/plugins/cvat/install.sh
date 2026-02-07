#!/bin/bash
# CVAT自定义插件安装脚本

echo "Installing Spharx CVAT plugins..."

# 创建插件目录
mkdir -p /home/django/plugins/spharx_auto_label
mkdir -p /home/django/plugins/spharx_export_tools

# 复制插件文件
cp -r /tmp/spharx_plugins/auto_label/* /home/django/plugins/spharx_auto_label/
cp -r /tmp/spharx_plugins/export_tools/* /home/django/plugins/spharx_export_tools/

# 设置权限
chown -R django:django /home/django/plugins/
chmod +x /home/django/plugins/*/install.sh

echo "CVAT plugins installed successfully!"