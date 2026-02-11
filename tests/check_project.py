#!/usr/bin/env python3
"""
项目完整性自动检查脚本
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Tuple

class ProjectChecker:
    def __init__(self, project_root: str = "."):
        self.root = Path(project_root)
        self.results = {
            "directories": [],
            "files": [],
            "modules": [],
            "configs": []
        }
    
    def check_structure(self):
        """检查项目结构"""
        print("[DIR] 检查项目结构...")
        
        # 必需目录
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
        
        for dir_path in required_dirs:
            full_path = self.root / dir_path
            exists = full_path.exists() and full_path.is_dir()
            self.results["directories"].append({
                "path": dir_path,
                "required": True,
                "exists": exists
            })
            
            status = "[OK]" if exists else "[MISSING]"
            print(f"  {status} {dir_path}/")
    
    def check_files(self):
        """检查必需文件"""
        print("\n[FILE] 检查必需文件...")
        
        required_files = [
            # 核心文件
            "src/main.py",
            "docker-compose.yml",
            "Dockerfile",
            "requirements.txt",
            ".env.template",
            "README.md",
            
            # 流水线文件
            "src/pipelines/__init__.py",
            "src/pipelines/pipeline_controller.py",
            "src/pipelines/pipeline_manager.py",
            
            # 数据模型
            "src/schemas/__init__.py",
            "src/schemas/config.py",
            "src/schemas/base.py",
            "src/schemas/task.py",
            "src/schemas/scene.py",
            "src/schemas/annotation.py",
            
            # 工具
            "src/utils/logging.py",
            "src/utils/__init__.py",
            
            # 配置
            "configs/logging.yaml",
            "configs/2d_annotation/sam.yaml",
            "configs/3d_reconstruction/colmap.yaml",
            
            # 部署脚本
            "deploy/01-init-server.sh",
            "deploy/02-clone-repos.sh",
            "deploy/03-setup-directories.sh",
            
            # 运维脚本
            "scripts/run_2d_pipeline.sh"
        ]
        
        for file_path in required_files:
            full_path = self.root / file_path
            exists = full_path.exists() and full_path.is_file()
            self.results["files"].append({
                "path": file_path,
                "required": True,
                "exists": exists,
                "size": full_path.stat().st_size if exists else 0
            })
            
            if exists:
                size_kb = full_path.stat().st_size / 1024
                status = "[OK]"
                size_info = f"({size_kb:.1f} KB)"
            else:
                status = "[MISSING]"
                size_info = ""
            
            print(f"  {status} {file_path} {size_info}")
    
    def check_python_modules(self):
        """检查Python模块可导入性"""
        print("\n[PYTHON] 检查Python模块导入...")
        
        modules_to_test = [
            ("src.main", "main"),
            ("src.pipelines", "get_pipeline_module"),
            ("src.schemas", "PipelineConfig"),
            ("src.utils.logging", "setup_logging")
        ]
        
        import sys
        sys.path.insert(0, str(self.root))
        
        for module_path, attribute in modules_to_test:
            try:
                module = __import__(module_path, fromlist=[attribute])
                if hasattr(module, attribute):
                    self.results["modules"].append({
                        "module": module_path,
                        "attribute": attribute,
                        "importable": True
                    })
                    print(f"  [OK] {module_path}.{attribute}")
                else:
                    self.results["modules"].append({
                        "module": module_path,
                        "attribute": attribute,
                        "importable": False
                    })
                    print(f"  [ERROR] {module_path}.{attribute} (属性不存在)")
            except ImportError as e:
                self.results["modules"].append({
                    "module": module_path,
                    "attribute": attribute,
                    "importable": False,
                    "error": str(e)
                })
                print(f"  [ERROR] {module_path}.{attribute} (导入失败: {e})")
    
    def check_configs(self):
        """检查配置文件"""
        print("\n[CONFIG] 检查配置文件...")
        
        configs_to_check = [
            (".env.template", "PROJECT_NAME"),
            ("docker-compose.yml", "version:"),
            ("Dockerfile", "FROM python"),
            ("requirements.txt", "pydantic")
        ]
        
        for config_file, expected_content in configs_to_check:
            full_path = self.root / config_file
            if full_path.exists():
                try:
                    content = full_path.read_text(encoding='utf-8')
                    if expected_content in content:
                        self.results["configs"].append({
                            "file": config_file,
                            "valid": True,
                            "has_content": True
                        })
                        print(f"  [OK] {config_file} (内容完整)")
                    else:
                        self.results["configs"].append({
                            "file": config_file,
                            "valid": False,
                            "has_content": True,
                            "missing": expected_content
                        })
                        print(f"  [WARN] {config_file} (缺少预期内容)")
                except Exception as e:
                    self.results["configs"].append({
                        "file": config_file,
                        "valid": False,
                        "error": str(e)
                    })
                    print(f"  [ERROR] {config_file} (读取失败: {e})")
            else:
                self.results["configs"].append({
                    "file": config_file,
                    "valid": False,
                    "exists": False
                })
                print(f"  [MISSING] {config_file} (文件不存在)")
    
    def generate_report(self):
        """生成检查报告"""
        print("\n" + "="*60)
        print("=== 项目完整性检查报告 ===")
        print("="*60)
        
        # 统计
        total_dirs = len(self.results["directories"])
        missing_dirs = sum(1 for d in self.results["directories"] if not d["exists"])
        
        total_files = len(self.results["files"])
        missing_files = sum(1 for f in self.results["files"] if not f["exists"])
        
        total_modules = len(self.results["modules"])
        importable_modules = sum(1 for m in self.results["modules"] if m["importable"])
        
        total_configs = len(self.results["configs"])
        valid_configs = sum(1 for c in self.results["configs"] if c.get("valid", False))
        
        # 总体进度
        dir_progress = (total_dirs - missing_dirs) / total_dirs if total_dirs > 0 else 0
        file_progress = (total_files - missing_files) / total_files if total_files > 0 else 0
        module_progress = importable_modules / total_modules if total_modules > 0 else 0
        config_progress = valid_configs / total_configs if total_configs > 0 else 0
        
        overall_progress = (dir_progress + file_progress + module_progress + config_progress) / 4
        
        print(f"\n[PROGRESS] 总体进度: {overall_progress:.1%}")
        print(f"   [DIR] 目录结构: {dir_progress:.1%} ({total_dirs - missing_dirs}/{total_dirs})")
        print(f"   [FILE] 核心文件: {file_progress:.1%} ({total_files - missing_files}/{total_files})")
        print(f"   [PYTHON] Python模块: {module_progress:.1%} ({importable_modules}/{total_modules})")
        print(f"   [CONFIG] 配置文件: {config_progress:.1%} ({valid_configs}/{total_configs})")
        
        # 建议
        print("\n[NEXT] 下一步建议:")
        
        if missing_dirs > 0:
            print(f"   1. 创建缺失的 {missing_dirs} 个目录")
            for d in self.results["directories"]:
                if not d["exists"]:
                    print(f"      - {d['path']}")
        
        if missing_files > 0:
            print(f"   2. 创建缺失的 {missing_files} 个核心文件")
            for f in self.results["files"]:
                if not f["exists"] and f.get("required", False):
                    print(f"      - {f['path']}")
        
        if total_modules - importable_modules > 0:
            print(f"   3. 修复 {total_modules - importable_modules} 个导入问题")
            for m in self.results["modules"]:
                if not m["importable"]:
                    print(f"      - {m['module']}.{m['attribute']}")
        
        # 保存报告
        report_file = self.root / "PROJECT_STATUS_REPORT.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print("\n[REPORT] 详细报告已保存:", report_file)
        print("="*60)
        
        return overall_progress

def main():
    """主函数"""
    checker = ProjectChecker()
    
    print("="*60)
    print("=== SpharxWorkshop 项目完整性检查 ===")
    print("="*60)
    
    checker.check_structure()
    checker.check_files()
    checker.check_python_modules()
    checker.check_configs()
    
    progress = checker.generate_report()
    
    if progress > 0.8:
        print("[GOOD] 项目结构良好，可以继续开发！")
    elif progress > 0.5:
        print("[WARN] 项目基本完整，但需要补充一些文件")
    else:
        print("[ERROR] 项目结构不完整，请先完善基础结构")
    
    return 0 if progress > 0.7 else 1

if __name__ == "__main__":
    exit(main())