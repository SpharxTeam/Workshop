#!/usr/bin/env python3
"""
SpharxWorkshop 项目完整性检查脚本
"""

import os
import sys
import json
import yaml
import ast
from pathlib import Path
from typing import Dict, List, Tuple, Set
import logging

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

class ProjectChecker:
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.toolchain_root = self.project_root / "toolchain"
        self.library_root = self.project_root / "library"
        
        self.errors = []
        self.warnings = []
        self.stats = {
            "files_checked": 0,
            "directories_checked": 0,
            "errors_found": 0,
            "warnings_found": 0
        }
    
    def check_directory_structure(self):
        """检查目录结构完整性"""
        logger.info("🔍 检查目录结构...")
        
        # Toolchain 必须存在的目录
        toolchain_required = [
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
        
        # Toolchain 必须存在的文件
        toolchain_files = [
            ".env.template",
            "docker-compose.yml",
            "Dockerfile",
            "requirements.txt",
            "README.md",
            "src/main.py",
            "src/__init__.py",
            "src/pipelines/__init__.py",
            "src/schemas/__init__.py",
            "src/schemas/config.py",
            "src/utils/__init__.py",
            "src/utils/logging.py",
            "configs/logging.yaml",
            "configs/2d_annotation/sam.yaml",
            "configs/3d_reconstruction/colmap.yaml",
            "configs/physics/blender.yaml",
            "deploy/01-init-server.sh",
            "deploy/02-clone-repos.sh",
            "deploy/03-setup-directories.sh",
            "scripts/run_2d_pipeline.sh"
        ]
        
        # 检查目录
        for dir_path in toolchain_required:
            full_path = self.toolchain_root / dir_path
            if full_path.exists():
                logger.debug(f"  ✓ 目录存在: {dir_path}/")
                self.stats["directories_checked"] += 1
            else:
                self.errors.append(f"目录不存在: toolchain/{dir_path}")
                logger.error(f"  ✗ 目录缺失: {dir_path}/")
        
        # 检查文件
        for file_path in toolchain_files:
            full_path = self.toolchain_root / file_path
            if full_path.exists():
                # 检查文件是否为空
                if full_path.stat().st_size == 0:
                    self.warnings.append(f"文件为空: toolchain/{file_path}")
                    logger.warning(f"  ⚠ 文件为空: {file_path}")
                else:
                    logger.debug(f"  ✓ 文件存在: {file_path}")
                self.stats["files_checked"] += 1
            else:
                self.errors.append(f"文件不存在: toolchain/{file_path}")
                logger.error(f"  ✗ 文件缺失: {file_path}")
        
        # Library 检查
        if self.library_root.exists():
            library_required = [
                "dataset_specification",
                "dataset_specification/schema",
                "dataset_specification/examples",
                "protocols",
                "tools",
                "references"
            ]
            
            library_files = [
                "README.md",
                "dataset_specification/SPHARX_PHYSICS_WORLD_DATASET_SPECIFICATION.md"
            ]
            
            for dir_path in library_required:
                full_path = self.library_root / dir_path
                if full_path.exists():
                    logger.debug(f"  ✓ Library目录存在: {dir_path}/")
                else:
                    self.warnings.append(f"Library目录不存在: library/{dir_path}")
                    logger.warning(f"  ⚠ Library目录缺失: {dir_path}/")
            
            for file_path in library_files:
                full_path = self.library_root / file_path
                if full_path.exists():
                    if full_path.stat().st_size == 0:
                        self.warnings.append(f"Library文件为空: {file_path}")
                    logger.debug(f"  ✓ Library文件存在: {file_path}")
                else:
                    self.warnings.append(f"Library文件不存在: {file_path}")
                    logger.warning(f"  ⚠ Library文件缺失: {file_path}")
        else:
            self.warnings.append("Library仓库目录不存在，可能未创建")
    
    def check_python_syntax(self):
        """检查Python文件语法"""
        logger.info("🐍 检查Python语法...")
        
        # 查找所有Python文件
        python_files = list(self.toolchain_root.rglob("*.py"))
        
        for py_file in python_files:
            try:
                # 尝试编译
                with open(py_file, 'r', encoding='utf-8') as f:
                    source = f.read()
                ast.parse(source)
                logger.debug(f"  ✓ 语法正确: {py_file.relative_to(self.toolchain_root)}")
            except SyntaxError as e:
                self.errors.append(f"Python语法错误: {py_file.relative_to(self.toolchain_root)}: {e}")
                logger.error(f"  ✗ 语法错误: {py_file.relative_to(self.toolchain_root)}: {e}")
            except Exception as e:
                self.warnings.append(f"Python文件读取失败: {py_file}: {e}")
                logger.warning(f"  ⚠ 读取失败: {py_file.relative_to(self.toolchain_root)}")
    
    def check_imports(self):
        """检查模块导入"""
        logger.info("📦 检查模块导入...")
        
        # 测试主要模块导入
        test_imports = [
            ("src.main", "main"),
            ("src.schemas.config", "PipelineConfig"),
            ("src.utils.logging", "setup_logging"),
            ("src.pipelines", "get_pipeline_module"),
        ]
        
        # 临时修改Python路径
        import sys
        sys.path.insert(0, str(self.toolchain_root))
        
        for module_name, item_name in test_imports:
            try:
                exec(f"from {module_name} import {item_name}")
                logger.debug(f"  ✓ 导入成功: {module_name}.{item_name}")
            except ImportError as e:
                self.errors.append(f"导入失败: {module_name}.{item_name}: {e}")
                logger.error(f"  ✗ 导入失败: {module_name}.{item_name}: {e}")
            except Exception as e:
                self.warnings.append(f"导入异常: {module_name}.{item_name}: {e}")
                logger.warning(f"  ⚠ 导入异常: {module_name}.{item_name}: {e}")
    
    def check_config_files(self):
        """检查配置文件格式"""
        logger.info("⚙️  检查配置文件...")
        
        config_files = [
            "configs/logging.yaml",
            "configs/2d_annotation/sam.yaml",
            "configs/3d_reconstruction/colmap.yaml",
            "configs/physics/blender.yaml"
        ]
        
        for config_file in config_files:
            full_path = self.toolchain_root / config_file
            if full_path.exists():
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        yaml.safe_load(f)
                    logger.debug(f"  ✓ YAML格式正确: {config_file}")
                except yaml.YAMLError as e:
                    self.errors.append(f"YAML格式错误: {config_file}: {e}")
                    logger.error(f"  ✗ YAML格式错误: {config_file}: {e}")
    
    def check_docker_files(self):
        """检查Docker相关文件"""
        logger.info("🐳 检查Docker文件...")
        
        docker_files = [
            "docker-compose.yml",
            "Dockerfile"
        ]
        
        for docker_file in docker_files:
            full_path = self.toolchain_root / docker_file
            if full_path.exists():
                if full_path.stat().st_size == 0:
                    self.errors.append(f"Docker文件为空: {docker_file}")
                    logger.error(f"  ✗ Docker文件为空: {docker_file}")
                else:
                    # 简单检查内容
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if "FROM" in content and docker_file == "Dockerfile":
                            logger.debug(f"  ✓ Dockerfile包含FROM指令")
                        elif "version:" in content and docker_file == "docker-compose.yml":
                            logger.debug(f"  ✓ docker-compose.yml包含version")
            else:
                self.errors.append(f"Docker文件不存在: {docker_file}")
    
    def check_requirements(self):
        """检查requirements.txt"""
        logger.info("📋 检查requirements.txt...")
        
        req_file = self.toolchain_root / "requirements.txt"
        if req_file.exists():
            with open(req_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                packages = [line.strip().split('==')[0].split('>=')[0] 
                           for line in lines if line.strip() and not line.startswith('#')]
                
                if len(packages) < 5:
                    self.warnings.append("requirements.txt中包数量较少")
                    logger.warning(f"  ⚠ 只有 {len(packages)} 个包，可能不全")
                else:
                    logger.debug(f"  ✓ 找到 {len(packages)} 个Python包")
        else:
            self.errors.append("requirements.txt不存在")
    
    def check_shell_scripts(self):
        """检查Shell脚本"""
        logger.info("💻 检查Shell脚本...")
        
        shell_scripts = [
            "deploy/01-init-server.sh",
            "deploy/02-clone-repos.sh", 
            "deploy/03-setup-directories.sh",
            "scripts/run_2d_pipeline.sh"
        ]
        
        for script in shell_scripts:
            full_path = self.toolchain_root / script
            if full_path.exists():
                # 检查shebang
                with open(full_path, 'r', encoding='utf-8') as f:
                    first_line = f.readline().strip()
                    if not first_line.startswith("#!/bin/bash"):
                        self.warnings.append(f"Shell脚本缺少shebang: {script}")
                        logger.warning(f"  ⚠ 缺少shebang: {script}")
                    else:
                        logger.debug(f"  ✓ Shell脚本格式正确: {script}")
            else:
                self.errors.append(f"Shell脚本不存在: {script}")
    
    def check_env_template(self):
        """检查环境变量模板"""
        logger.info("🌍 检查环境变量模板...")
        
        env_file = self.toolchain_root / ".env.template"
        if env_file.exists():
            with open(env_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
                required_vars = [
                    "PROJECT_NAME",
                    "OSS_ENDPOINT", 
                    "OSS_BUCKET",
                    "OSS_ACCESS_KEY_ID",
                    "OSS_ACCESS_KEY_SECRET",
                    "SPHARX_INPUT_DIR",
                    "SPHARX_OUTPUT_DIR"
                ]
                
                missing_vars = []
                for var in required_vars:
                    if var not in content:
                        missing_vars.append(var)
                
                if missing_vars:
                    self.errors.append(f".env.template缺少必要变量: {', '.join(missing_vars)}")
                    logger.error(f"  ✗ 缺少必要变量: {', '.join(missing_vars)}")
                else:
                    logger.debug("  ✓ .env.template包含所有必要变量")
        else:
            self.errors.append(".env.template不存在")
    
    def run_all_checks(self):
        """运行所有检查"""
        logger.info("=" * 60)
        logger.info("开始项目完整性检查")
        logger.info("=" * 60)
        
        self.check_directory_structure()
        self.check_python_syntax()
        self.check_imports()
        self.check_config_files()
        self.check_docker_files()
        self.check_requirements()
        self.check_shell_scripts()
        self.check_env_template()
        
        # 更新统计
        self.stats["errors_found"] = len(self.errors)
        self.stats["warnings_found"] = len(self.warnings)
        
        return self.generate_report()
    
    def generate_report(self):
        """生成检查报告"""
        logger.info("=" * 60)
        logger.info("📊 检查结果汇总")
        logger.info("=" * 60)
        
        logger.info(f"📁 检查统计:")
        logger.info(f"  目录检查: {self.stats['directories_checked']}")
        logger.info(f"  文件检查: {self.stats['files_checked']}")
        logger.info(f"  错误数量: {self.stats['errors_found']}")
        logger.info(f"  警告数量: {self.stats['warnings_found']}")
        
        if self.errors:
            logger.info("\n❌ 发现错误:")
            for error in self.errors[:10]:  # 只显示前10个错误
                logger.info(f"  • {error}")
            
            if len(self.errors) > 10:
                logger.info(f"  ... 还有 {len(self.errors)-10} 个错误")
        
        if self.warnings:
            logger.info("\n⚠️  发现警告:")
            for warning in self.warnings[:10]:  # 只显示前10个警告
                logger.info(f"  • {warning}")
            
            if len(self.warnings) > 10:
                logger.info(f"  ... 还有 {len(self.warnings)-10} 个警告")
        
        if not self.errors and not self.warnings:
            logger.info("\n🎉 恭喜！所有检查通过，项目结构完整。")
            return True
        elif self.errors:
            logger.info(f"\n🔧 发现 {len(self.errors)} 个错误需要修复。")
            return False
        else:
            logger.info(f"\n👍 项目基本完整，但有 {len(self.warnings)} 个警告需要注意。")
            return True


def main():
    """主函数"""
    # 检查当前目录
    current_dir = Path.cwd()
    
    # 确定项目根目录
    if (current_dir / "toolchain").exists():
        project_root = current_dir
    elif (current_dir.parent / "toolchain").exists():
        project_root = current_dir.parent
    else:
        logger.error("❌ 无法找到toolchain目录，请在项目根目录或toolchain目录下运行此脚本")
        sys.exit(1)
    
    checker = ProjectChecker(project_root)
    success = checker.run_all_checks()
    
    # 保存报告
    report = {
        "timestamp": datetime.now().isoformat(),
        "project_root": str(project_root),
        "stats": checker.stats,
        "errors": checker.errors,
        "warnings": checker.warnings,
        "success": success
    }
    
    report_file = project_root / "project_check_report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    logger.info(f"\n📄 详细报告已保存: {report_file}")
    
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    from datetime import datetime
    main()