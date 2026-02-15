#!/bin/bash

# 相机同步测试脚本

set -e

echo "🧪 开始相机同步测试..."

# 检查依赖
echo "🔍 检查依赖..."
if ! python3 -c "import pyrealsense2" &> /dev/null; then
    echo "❌ 未安装 pyrealsense2，请先运行 install_drivers.sh"
    exit 1
fi

# 运行同步测试
echo "🚀 运行同步测试程序..."
python3 -c "
import sys
sys.path.append('../..')

try:
    from hardware.camera.sync_controller import SyncController, CameraConfig, SyncMode
    from hardware.camera.sync_validator import SyncValidator
    import time
    import logging
    
    # 配置日志
    logging.basicConfig(level=logging.INFO)
    
    print('创建同步控制器...')
    controller = SyncController()
    
    # 添加测试相机配置
    cam1_config = CameraConfig('test_cam1', SyncMode.MASTER)
    cam2_config = CameraConfig('test_cam2', SyncMode.SLAVE)
    
    controller.add_camera('test_cam1', cam1_config)
    controller.add_camera('test_cam2', cam2_config)
    
    print('创建同步验证器...')
    validator = SyncValidator(window_size=50)
    
    print('启动同步系统...')
    controller.start_sync()
    
    # 运行测试
    print('运行同步测试 10 秒钟...')
    time.sleep(10)
    
    # 停止同步
    controller.stop_sync()
    
    # 输出测试结果
    print('\\n📊 测试结果:')
    print('同步状态:', controller.get_sync_status())
    print('验证报告:', validator.get_validation_report())
    
    print('\\n✅ 同步测试完成!')
    
except ImportError as e:
    print(f'❌ 导入模块失败: {e}')
    print('请确保在正确的目录下运行此脚本')
except Exception as e:
    print(f'❌ 测试过程中出现错误: {e}')
"

echo ""
echo "🏁 同步测试结束"