#!/usr/bin/env python3
"""
项目错误检查脚本
"""

import subprocess
import sys
from pathlib import Path

def check_python_syntax():
    """检查Python语法"""
    print("🔍 检查Python语法...")
    
    src_dir = Path("src")
    errors = []
    
    for py_file in src_dir.rglob("*.py"):
        try:
            # 尝试编译文件
            with open(py_file, 'r', encoding='utf-8') as f:
                compile(f.read(), str(py_file), 'exec')
            print(f"  ✅ {py_file.relative_to(src_dir)}")
        except SyntaxError as e:
            errors.append(f"{py_file}:{e.lineno}: {e.msg}")
            print(f"  ❌ {py_file.relative_to(src_dir)}: {e.msg}")
    
    return errors

def check_imports():
    """检查导入错误"""
    print("\n🔍 检查导入依赖...")
    
    test_code = """
import sys
import os
from pathlib import Path

# 测试导入项目模块
sys.path.insert(0, 'src')
try:
    from pipelines import get_pipeline_module
    print("  ✅ pipelines 模块导入成功")
except ImportError as e:
    print(f"  ❌ pipelines 模块导入失败: {e}")

try:
    from schemas import PipelineConfig
    print("  ✅ schemas 模块导入成功")
except ImportError as e:
    print(f"  ❌ schemas 模块导入失败: {e}")

try:
    from utils.logging import setup_logging
    print("  ✅ utils 模块导入成功")
except ImportError as e:
    print(f"  ❌ utils 模块导入失败: {e}")
"""
    
    result = subprocess.run([sys.executable, "-c", test_code], 
                          capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print("  ⚠️  警告:", result.stderr)

def check_directory_structure():
    """检查目录结构"""
    print("\n📁 检查目录结构...")
    
    required_dirs = [
        "src",
        "src/pipelines",
        "src/schemas", 
        "src/utils",
        "configs",
        "configs/2d_annotation",
        "configs/3d_reconstruction",
        "configs/physics",
        "deploy",
        "scripts",
        "docs"
    ]
    
    missing_dirs = []
    for dir_path in required_dirs:
        if Path(dir_path).exists():
            print(f"  ✅ {dir_path}/")
        else:
            missing_dirs.append(dir_path)
            print(f"  ❌ {dir_path}/ (缺失)")
    
    return missing_dirs

def check_required_files():
    """检查必需文件"""
    print("\n📄 检查必需文件...")
    
    required_files = [
        "src/main.py",
        "src/pipelines/__init__.py",
        "src/pipelines/pipeline_controller.py",
        "src/schemas/__init__.py",
        "src/schemas/config.py",
        "src/utils/logging.py",
        "docker-compose.yml",
        "Dockerfile",
        "requirements.txt",
        ".env.template",
        "README.md"
    ]
    
    missing_files = []
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"  ✅ {file_path}")
        else:
            missing_files.append(file_path)
            print(f"  ❌ {file_path} (缺失)")
    
    return missing_files

def main():
    """主检查函数"""
    print("="*60)
    print("SpharxWorkshop 项目完整性检查")
    print("="*60)
    
    all_errors = []
    
    # 执行各项检查
    syntax_errors = check_python_syntax()
    if syntax_errors:
        all_errors.extend(syntax_errors)
    
    check_imports()
    
    missing_dirs = check_directory_structure()
    if missing_dirs:
        all_errors.append(f"缺失目录: {', '.join(missing_dirs)}")
    
    missing_files = check_required_files()
    if missing_files:
        all_errors.append(f"缺失文件: {', '.join(missing_files)}")
    
    # 总结
    print("\n" + "="*60)
    print("检查结果总结:")
    print("="*60)
    
    if all_errors:
        print(f"❌ 发现 {len(all_errors)} 个问题:")
        for error in all_errors:
            print(f"  • {error}")
        sys.exit(1)
    else:
        print("✅ 所有检查通过！项目结构完整。")

if __name__ == "__main__":
    main()