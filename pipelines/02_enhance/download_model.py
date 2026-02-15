#!/usr/bin/env python3
"""
简化版模型下载工具：从多个镜像源尝试下载模型文件，只检查文件是否存在且非空。
使用 wget 命令以提高稳定性。
"""
import os
import sys
import subprocess
import time

# 模型镜像源配置（按优先级排序）
MODEL_SOURCES = {
    "yolov8n.pt": [
        "https://github.com/ultralytics/assets/releases/download/v8.3.0/{filename}",
        "https://ghproxy.com/https://github.com/ultralytics/assets/releases/download/v8.3.0/{filename}",
        "https://kgithub.com/ultralytics/assets/releases/download/v8.3.0/{filename}",
        "https://cdn.jsdelivr.net/gh/ultralytics/assets@latest/{filename}",
        # 可添加其他备用源，如阿里云OSS（若有）
    ],
    # 可扩展其他模型
}

def download_with_wget(url, dest, retries=3):
    """使用 wget 下载，支持重试"""
    for i in range(retries):
        cmd = ["wget", "-O", dest, "--timeout=30", "--tries=1", url]
        print(f"尝试 wget [{i+1}/{retries}]: {url}")
        result = subprocess.run(cmd, capture_output=True)
        if result.returncode == 0:
            return True
        print(f"wget 失败: {result.stderr.decode().strip()}")
        if i < retries - 1:
            time.sleep(2)
    return False

def main():
    model_name = sys.argv[1] if len(sys.argv) > 1 else "yolov8n.pt"
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "."
    output_path = os.path.join(output_dir, model_name)

    if model_name not in MODEL_SOURCES:
        print(f"错误: 未知模型 '{model_name}'，支持的模型: {list(MODEL_SOURCES.keys())}")
        sys.exit(1)

    os.makedirs(output_dir, exist_ok=True)

    # 如果文件已存在且非空，跳过下载
    if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
        print(f"文件已存在且非空: {output_path}")
        sys.exit(0)

    sources = MODEL_SOURCES[model_name]
    print(f"开始下载模型: {model_name}")
    print(f"目标路径: {output_path}")
    print(f"将尝试 {len(sources)} 个镜像源...")

    for idx, src_template in enumerate(sources, 1):
        url = src_template.format(filename=model_name)
        print(f"\n镜像源 [{idx}/{len(sources)}]: {url}")
        if download_with_wget(url, output_path):
            # 检查文件是否有效
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                print(f"✅ 下载成功: {output_path}")
                sys.exit(0)
            else:
                print("下载的文件为空，尝试下一个镜像")
                if os.path.exists(output_path):
                    os.remove(output_path)
        # 否则继续尝试下一个

    print("\n❌ 所有镜像源均下载失败")
    sys.exit(1)

if __name__ == "__main__":
    main()