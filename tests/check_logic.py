#!/usr/bin/env python3
"""
代码逻辑检查脚本
检查关键逻辑路径和潜在问题
"""

import ast
import re
from pathlib import Path
from typing import List, Dict, Set
import logging

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)


class CodeLogicChecker:
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.toolchain_root = self.project_root / "toolchain"
        self.issues = []
        
    def check_unused_imports(self, filepath: Path):
        """检查未使用的导入"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read(), filename=str(filepath))
            
            # 收集所有导入
            imports = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for name in node.names:
                        imports.add(name.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        for name in node.names:
                            imports.add(f"{node.module}.{name.name}")
            
            # 收集所有使用的名称
            used_names = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Name):
                    used_names.add(node.id)
                elif isinstance(node, ast.Attribute):
                    # 简化处理：只检查属性访问的第一部分
                    parts = []
                    current = node
                    while isinstance(current, ast.Attribute):
                        parts.append(current.attr)
                        current = current.value
                    if isinstance(current, ast.Name):
                        parts.append(current.id)
                        used_names.add(parts[-1])  # 根名称
            
            # 这里简化了检查，实际应该更复杂
            # 暂时只记录检查
            if imports:
                logger.debug(f"  检查导入: {filepath.relative_to(self.toolchain_root)}")
                
        except Exception as e:
            logger.warning(f"  无法分析导入: {filepath}: {e}")
    
    def check_hardcoded_paths(self, filepath: Path):
        """检查硬编码的路径"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 查找硬编码的绝对路径
            hardcoded_patterns = [
                r'"/home/[^"]+"',          # /home/ 开头的路径
                r"'/home/[^']+'",
                r'"/root/[^"]+"',          # /root/ 开头的路径
                r'"/etc/[^"]+"',           # /etc/ 开头的路径
                r'"/var/[^"]+"',           # /var/ 开头的路径
                r'"/usr/[^"]+"',           # /usr/ 开头的路径
                r'C:\\\\.*',               # Windows路径
            ]
            
            issues = []
            for pattern in hardcoded_patterns:
                matches = re.findall(pattern, content)
                for match in matches:
                    # 排除合理的路径（如Docker中的路径）
                    if "/home/SpharxWorkshop" in match:
                        continue  # 这是我们的标准路径
                    issues.append(match)
            
            if issues:
                self.issues.append({
                    "file": str(filepath.relative_to(self.toolchain_root)),
                    "type": "hardcoded_path",
                    "message": f"发现硬编码路径: {', '.join(issues[:3])}",
                    "severity": "warning"
                })
                
        except Exception as e:
            logger.warning(f"  无法检查硬编码路径: {filepath}: {e}")
    
    def check_error_handling(self, filepath: Path):
        """检查错误处理"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查是否有try-except块
            if "try:" in content:
                # 统计try-except数量
                try_count = content.count("try:")
                except_count = content.count("except ")
                
                if try_count > except_count:
                    self.issues.append({
                        "file": str(filepath.relative_to(self.toolchain_root)),
                        "type": "error_handling",
                        "message": f"try块({try_count})多于except块({except_count})",
                        "severity": "warning"
                    })
            
            # 检查是否有裸的except（没有指定异常类型）
            if "except:" in content or "except :" in content:
                self.issues.append({
                    "file": str(filepath.relative_to(self.toolchain_root)),
                    "type": "bare_except",
                    "message": "发现裸的except语句（应指定异常类型）",
                    "severity": "warning"
                })
                
        except Exception as e:
            logger.warning(f"  无法检查错误处理: {filepath}: {e}")
    
    def check_config_consistency(self):
        """检查配置文件一致性"""
        logger.info("🔗 检查配置一致性...")
        
        # 检查环境变量模板中的路径是否与代码中一致
        env_file = self.toolchain_root / ".env.template"
        if env_file.exists():
            with open(env_file, 'r', encoding='utf-8') as f:
                env_content = f.read()
            
            # 检查关键路径变量
            required_vars = ["SPHARX_INPUT_DIR", "SPHARX_OUTPUT_DIR", "SPHARX_WORKSPACE_DIR"]
            
            for var in required_vars:
                pattern = rf'{var}=([^\n]+)'
                match = re.search(pattern, env_content)
                if match:
                    value = match.group(1).strip()
                    # 检查是否为默认值
                    if "/home/SpharxWorkshop" not in value:
                        self.issues.append({
                            "file": ".env.template",
                            "type": "config_consistency",
                            "message": f"{var}的值可能不正确: {value}",
                            "severity": "warning"
                        })
                else:
                    self.issues.append({
                        "file": ".env.template",
                        "type": "config_consistency", 
                        "message": f"缺少必要变量: {var}",
                        "severity": "error"
                    })
    
    def check_main_script(self):
        """检查主脚本完整性"""
        logger.info("🎯 检查主脚本...")
        
        main_file = self.toolchain_root / "src/main.py"
        if main_file.exists():
            with open(main_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查必要的函数
            required_functions = ["main()", "run_pipeline", "health_check"]
            missing_funcs = []
            
            for func in required_functions:
                if func not in content:
                    missing_funcs.append(func)
            
            if missing_funcs:
                self.issues.append({
                    "file": "src/main.py",
                    "type": "main_script",
                    "message": f"缺少必要函数: {', '.join(missing_funcs)}",
                    "severity": "error"
                })
            
            # 检查是否支持manager命令
            if "manager" not in content:
                self.issues.append({
                    "file": "src/main.py", 
                    "type": "main_script",
                    "message": "缺少manager命令支持",
                    "severity": "warning"
                })
    
    def run_all_checks(self):
        """运行所有逻辑检查"""
        logger.info("=" * 60)
        logger.info("开始代码逻辑检查")
        logger.info("=" * 60)
        
        # 检查Python文件
        python_files = list(self.toolchain_root.rglob("*.py"))
        
        for py_file in python_files:
            if py_file.is_file():
                rel_path = py_file.relative_to(self.toolchain_root)
                logger.debug(f"检查: {rel_path}")
                
                self.check_unused_imports(py_file)
                self.check_hardcoded_paths(py_file)
                self.check_error_handling(py_file)
        
        # 特殊检查
        self.check_config_consistency()
        self.check_main_script()
        
        return self.generate_report()
    
    def generate_report(self):
        """生成逻辑检查报告"""
        logger.info("=" * 60)
        logger.info("📋 逻辑检查结果")
        logger.info("=" * 60)
        
        # 按严重程度分组
        errors = [issue for issue in self.issues if issue["severity"] == "error"]
        warnings = [issue for issue in self.issues if issue["severity"] == "warning"]
        
        if errors:
            logger.info("❌ 发现逻辑错误:")
            for error in errors[:5]:
                logger.info(f"  • [{error['type']}] {error['file']}: {error['message']}")
        
        if warnings:
            logger.info("\n⚠️  发现逻辑警告:")
            for warning in warnings[:5]:
                logger.info(f"  • [{warning['type']}] {warning['file']}: {warning['message']}")
        
        if not errors and not warnings:
            logger.info("✅ 代码逻辑检查通过，未发现明显问题。")
            return True
        else:
            logger.info(f"\n📊 总计: {len(errors)} 个错误, {len(warnings)} 个警告")
            return len(errors) == 0


def main():
    """主函数"""
    import sys
    
    # 确定项目根目录
    current_dir = Path.cwd()
    if (current_dir / "toolchain").exists():
        project_root = current_dir
    elif (current_dir.parent / "toolchain").exists():
        project_root = current_dir.parent
    else:
        logger.error("❌ 无法找到toolchain目录")
        sys.exit(1)
    
    checker = CodeLogicChecker(project_root)
    success = checker.run_all_checks()
    
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()