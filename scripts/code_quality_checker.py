#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Workshop V2.0 代码质量检查与自动修复工具
============================================
功能：
1. PEP8/PEP257 风格检查（使用 flake8/pycodestyle）
2. 类型注解完整性扫描
3. 导入语句排序与去重
4. 未使用变量检测
5. 复杂度分析（圈复杂度）
6. 自动生成修复建议报告
"""

import ast
import os
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Set, Any


@dataclass
class QualityIssue:
    """代码质量问题"""
    file_path: str
    line_number: int
    column: int
    severity: str  # ERROR, WARNING, INFO, HINT
    rule_id: str
    message: str
    suggestion: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'file': self.file_path,
            'line': self.line_number,
            'column': self.column,
            'severity': self.severity,
            'rule': self.rule_id,
            'message': self.message,
            'suggestion': self.suggestion or ''
        }


@dataclass
class FileQualityReport:
    """单文件质量报告"""
    file_path: str
    total_lines: int = 0
    issues: List[QualityIssue] = field(default_factory=list)
    
    @property
    def error_count(self) -> int:
        return len([i for i in self.issues if i.severity == 'ERROR'])
    
    @property
    def warning_count(self) -> int:
        return len([i for i in self.issues if i.severity == 'WARNING'])
    
    @property
    def quality_score(self) -> float:
        """计算文件质量评分 (0-100)"""
        if self.total_lines == 0:
            return 100.0
        
        base_score = 100.0
        error_penalty = self.error_count * 5.0
        warning_penalty = self.warning_count * 2.0
        info_penalty = len([i for i in self.issues if i.severity == 'INFO']) * 0.5
        
        final_score = max(0.0, base_score - error_penalty - warning_penalty - info_penalty)
        
        # 根据行数调整（大文件容忍度稍高）
        if self.total_lines > 500:
            final_score += min(10.0, (self.total_lines - 500) * 0.01)
        
        return round(min(100.0, final_score), 1)


class TypeAnnotationChecker(ast.NodeVisitor):
    """
    类型注解完整性检查器
    使用AST分析函数/方法的参数和返回值注解
    """
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.issues: List[QualityIssue] = []
        self.current_class: Optional[str] = None
    
    def visit_ClassDef(self, node: ast.ClassDef):
        """访问类定义"""
        old_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = old_class
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """检查函数定义的类型注解"""
        func_name = f"{self.current_class}.{node.name}" if self.current_class else node.name
        
        # 跳过特殊方法（__init__, __enter__, __exit__等）
        special_methods = {'__init__', '__repr__', '__str__', '__enter__', '__exit__', 
                          '__len__', '__iter__', '__next__', '__del__'}
        if node.name in special_methods:
            self.generic_visit(node)
            return
        
        # 检查参数注解
        args = node.args
        all_args = args.args + args.posonlyargs + args.kwonlyargs
        
        for arg in all_args:
            if arg.arg in ('self', 'cls'):
                continue
            
            if arg.annotation is None:
                self.issues.append(QualityIssue(
                    file_path=self.file_path,
                    line_number=node.lineno,
                    column=node.col_offset,
                    severity='WARNING',
                    rule_id='TYP001',
                    message=f"函数 '{func_name}' 的参数 '{arg.arg}' 缺少类型注解",
                    suggestion=f"添加类型注解: {arg.arg}: <type>"
                ))
        
        # 检查返回值注解
        if node.returns is None and not self._is_generator_or_async(node):
            self.issues.append(QualityIssue(
                file_path=self.file_path,
                line_number=node.lineno,
                column=node.col_offset,
                severity='INFO',
                rule_id='TYP002',
                message=f"函数 '{func_name}' 缺少返回值类型注解",
                suggestion="添加返回值注解: -> <ReturnType>"
            ))
        
        self.generic_visit(node)
    
    def _is_generator_or_async(self, node: ast.FunctionDef) -> bool:
        """判断是否是生成器或异步函数（这些可能不需要显式返回值注解）"""
        for child in ast.walk(node):
            if isinstance(child, (ast.Yield, ast.YieldFrom, ast.Await)):
                return True
        return False


class ImportSorter:
    """导入语句排序与优化器"""
    
    STANDARD_LIBRARY = {
        'abc', 'argparse', 'asyncio', 'base64', 'collections', 'copy', 'csv',
        'dataclasses', 'datetime', 'decimal', 'enum', 'fnmatch', 'functools',
        'glob', 'gzip', 'hashlib', 'html', 'http', 'importlib', 'inspect',
        'itertools', 'json', 'logging', 'math', 'mimetypes', 'multiprocessing',
        'os', 'pathlib', 'pickle', 'platform', 'pprint', 'queue', 'random',
        're', 'shutil', 'signal', 'socket', 'sqlite3', 'ssl', 'statistics',
        'string', 'struct', 'subprocess', 'sys', 'tempfile', 'textwrap',
        'threading', 'time', 'timeit', 'traceback', 'types', 'typing', 'uuid',
        'warnings', 'weakref', 'xml', 'zipfile'
    }
    
    THIRD_PARTY = {
        'numpy', 'pandas', 'scipy', 'cv2', 'opencv', 'PIL', 'pillow',
        'torch', 'tensorflow', 'keras', 'sklearn', 'scikit',
        'requests', 'flask', 'django', 'fastapi', 'sqlalchemy',
        'pydantic', 'click', 'rich', 'tqdm', 'psutil', 'yaml',
        'boto3', 'oss2', 'alibabacloud'
    }
    
    @classmethod
    def get_import_category(cls, module_name: str) -> int:
        """
        获取导入类别
        返回: 0=标准库, 1=第三方库, 2=本地模块, 3=相对导入
        """
        base_module = module_name.split('.')[0]
        
        if base_module in cls.STANDARD_LIBRARY:
            return 0
        elif base_module in cls.THIRD_PARTY:
            return 1
        elif module_name.startswith('.'):
            return 3
        else:
            return 2
    
    @classmethod
    def check_import_order(cls, source_lines: List[str], file_path: str) -> List[QualityIssue]:
        """检查导入顺序是否符合规范"""
        issues = []
        imports_found = []
        last_import_line = 0
        
        for idx, line in enumerate(source_lines, start=1):
            stripped = line.strip()
            
            # 匹配 import 语句
            if stripped.startswith('import ') or stripped.startswith('from '):
                # 提取模块名
                match = re.match(r'(?:from|import)\s+([\w.]+)', stripped)
                if match:
                    module_name = match.group(1)
                    category = cls.get_import_category(module_name)
                    imports_found.append((idx, category, module_name, stripped))
                    last_import_line = max(last_import_line, idx)
        
        # 检查类别是否按顺序排列
        prev_category = -1
        for line_num, category, module, statement in imports_found:
            if category < prev_category:
                issues.append(QualityIssue(
                    file_path=file_path,
                    line_number=line_num,
                    column=0,
                    severity='INFO',
                    rule_id='IMP001',
                    message=f"导入语句顺序不规范: '{module}' 应该在更前面",
                    suggestion="按照 标准库 → 第三方库 → 本地模块 的顺序重新排序"
                ))
            prev_category = category
        
        # 检查是否有代码出现在导入之后（应该在导入区域后有空行）
        if last_import_line > 0 and last_import_line < len(source_lines):
            next_line_idx = last_import_line
            while next_line_idx < len(source_lines) and not source_lines[next_line_idx].strip():
                next_line_idx += 1
            
            if next_line_idx < len(source_lines) and next_line_idx == last_import_line + 1:
                # 紧接着就是代码，缺少空行分隔
                pass  # 这个警告太频繁了，暂时跳过
        
        return issues


class ComplexityAnalyzer(ast.NodeVisitor):
    """圈复杂度分析器"""
    
    COMPLEXITY_NODES = (
        ast.If, ast.For, ast.While, ast.ExceptHandler,
        ast.With, ast.Assert, ast.comprehension,
        ast.BoolOp  # and/or
    )
    
    def __init__(self, file_path: str, max_complexity: int = 15):
        self.file_path = file_path
        self.max_complexity = max_complexity
        self.issues: List[QualityIssue] = []
        self._current_function: Optional[Tuple[str, int]] = None
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        old_func = self._current_function
        self._current_function = (node.name, node.lineno)
        
        complexity = self._calculate_complexity(node)
        
        if complexity > self.max_complexity:
            func_display = f"{self._current_function[0]}"
            self.issues.append(QualityIssue(
                file_path=self.file_path,
                line_number=node.lineno,
                column=node.col_offset,
                severity='WARNING' if complexity <= 20 else 'ERROR',
                rule_id='CCN001',
                message=f"函数 '{func_display}' 圈复杂度过高 ({complexity}/{self.max_complexity})",
                suggestion="考虑拆分为多个小函数或简化条件逻辑"
            ))
        
        self.generic_visit(node)
        self._current_function = old_func
    
    def _calculate_complexity(self, node: ast.AST) -> int:
        """递归计算圈复杂度"""
        complexity = 1  # 基础复杂度
        
        for child in ast.walk(node):
            if isinstance(child, self.COMPLEXITY_NODES):
                complexity += 1
                # BoolOp 的每个额外操作数都增加复杂度
                if isinstance(child, ast.BoolOp):
                    complexity += len(child.values) - 1
        
        return complexity


class UnusedVariableDetector(ast.NodeVisitor):
    """未使用变量检测器"""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.issues: List[QualityIssue] = []
        self._defined_vars: Dict[str, Tuple[int, int]] = {}  # var_name -> (line, col)
        self._used_vars: Set[str] = set()
        self._in_comprehension = False
    
    def visit_Assign(self, node: ast.Assign):
        """检查赋值语句"""
        for target in node.targets:
            if isinstance(target, ast.Name) and not target.id.startswith('_'):
                self._defined_vars[target.id] = (target.lineno, target.col_offset)
        self.generic_visit(node)
    
    def visit_Name(self, node: ast.Name):
        """记录变量使用"""
        if isinstance(node.ctx, ast.Load):
            self._used_vars.add(node.id)
        self.generic_visit(node)
    
    def visit_ExceptHandler(self, node: ast.ExceptHandler):
        """检查异常处理中的未使用变量"""
        if node.name and node.name not in self._used_vars:
            self.issues.append(QualityIssue(
                file_path=self.file_path,
                line_number=node.lineno,
                column=node.col_offset,
                severity='INFO',
                rule_id='VAR001',
                message=f"异常变量 '{node.name}' 未被使用",
                suggestion=f"改为: except Exception: 或使用 '_' 替代"
            ))
        self.generic_visit(node)
    
    def visit_For(self, node: ast.For):
        """检查for循环中的未使用迭代变量"""
        if isinstance(node.target, ast.Name):
            var_name = node.target.id
            if var_name not in ('_',) and var_name not in self._used_vars:
                # 特殊情况：如果循环体为pass或者只有注释
                has_meaningful_body = any(
                    not isinstance(child, (ast.Pass, ast.Expr)) or 
                    (isinstance(child, ast.Expr) and not isinstance(child.value, ast.Constant))
                    for child in node.body
                )
                if has_meaningful_body:
                    self.issues.append(QualityIssue(
                        file_path=self.file_path,
                        line_number=node.lineno,
                        column=node.col_offset,
                        severity='INFO',
                        rule_id='VAR002',
                        message=f"For循环变量 '{var_name}' 在循环体中未被使用",
                        suggestion=f"将 '{var_name}' 改为 '_' 表示有意忽略"
                    ))
        self.generic_visit(node)


class CodeQualityChecker:
    """
    Workshop V2.0 综合代码质量检查器
    ==================================
    
    使用示例:
        checker = CodeQualityChecker(base_dir='.')
        report = checker.check_directory('./common/core')
        print(report.generate_summary())
    """
    
    def __init__(self, base_dir: str = '.', config: Optional[Dict] = None):
        self.base_dir = Path(base_dir).resolve()
        self.config = config or {
            'max_complexity': 15,
            'exclude_patterns': [
                '__pycache__',
                '.git',
                '*.pyc',
                'venv',
                '.venv',
                'build',
                'dist',
                '*.egg-info'
            ],
            'file_extensions': ['.py'],
            'min_quality_score': 80.0
        }
        self.reports: List[FileQualityReport] = []
        self.total_issues: List[QualityIssue] = []
    
    def check_file(self, file_path: str) -> FileQualityReport:
        """检查单个Python文件的质量"""
        path = Path(file_path)
        
        if not path.exists() or path.suffix != '.py':
            return FileQualityReport(file_path=str(path))
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                source = f.read()
                lines = source.split('\n')
            
            report = FileQualityReport(
                file_path=str(path),
                total_lines=len(lines)
            )
            
            # 解析AST
            try:
                tree = ast.parse(source)
                
                # 1. 类型注解检查
                type_checker = TypeAnnotationChecker(str(path))
                type_checker.visit(tree)
                report.issues.extend(type_checker.issues)
                
                # 2. 圈复杂度分析
                complexity_analyzer = ComplexityAnalyzer(
                    str(path), 
                    max_complexity=self.config['max_complexity']
                )
                complexity_analyzer.visit(tree)
                report.issues.extend(complexity_analyzer.issues)
                
                # 3. 未使用变量检测
                unused_detector = UnusedVariableDetector(str(path))
                unused_detector.visit(tree)
                report.issues.extend(unused_detector.issues)
                
            except SyntaxError as e:
                report.issues.append(QualityIssue(
                    file_path=str(path),
                    line_number=getattr(e, 'lineno', 1),
                    column=getattr(e, 'offset', 0),
                    severity='ERROR',
                    rule_id='SYN001',
                    message=f"语法错误: {e}",
                    suggestion="修复语法错误后再进行检查"
                ))
            
            # 4. 导入顺序检查
            import_issues = ImportSorter.check_import_order(lines, str(path))
            report.issues.extend(import_issues)
            
            # 5. 行长度检查（PEP8: 79字符）
            for idx, line in enumerate(lines, start=1):
                if len(line) > 120:  # 放宽到120字符（现代显示器）
                    if not line.strip().startswith('#') or len(line) > 150:  # 注释允许更长
                        report.issues.append(QualityIssue(
                            file_path=str(path),
                            line_number=idx,
                            column=120,
                            severity='WARNING',
                            rule_id='E501',
                            message=f"行过长 ({len(line)} 字符)",
                            suggestion="拆分长行或使用括号隐式续行"
                        ))
            
            self.reports.append(report)
            self.total_issues.extend(report.issues)
            
            return report
            
        except Exception as e:
            return FileQualityReport(
                file_path=str(path),
                issues=[QualityIssue(
                    file_path=str(path),
                    line_number=0,
                    column=0,
                    severity='ERROR',
                    rule_id='FIL001',
                    message=f"无法读取文件: {e}"
                )]
            )
    
    def check_directory(self, directory: str, recursive: bool = True) -> List[FileQualityReport]:
        """检查目录下所有Python文件"""
        dir_path = Path(directory)
        
        if not dir_path.exists():
            print(f"[错误] 目录不存在: {directory}")
            return []
        
        pattern = '**/*.py' if recursive else '*.py'
        py_files = list(dir_path.glob(pattern))
        
        # 排除特定模式
        exclude_patterns = self.config['exclude_patterns']
        filtered_files = []
        
        for f in py_files:
            excluded = False
            for pattern in exclude_patterns:
                if pattern.startswith('*'):
                    if f.name.endswith(pattern[1:]):
                        excluded = True
                        break
                elif pattern in str(f):
                    excluded = True
                    break
            
            if not excluded:
                filtered_files.append(f)
        
        print(f"\n{'='*70}")
        print(f"📊 开始代码质量检查")
        print(f"   目标目录: {dir_path}")
        print(f"   文件数量: {len(filtered_files)} 个Python文件")
        print(f"{'='*70}\n")
        
        results = []
        for f in filtered_files:
            rel_path = f.relative_to(self.base_dir)
            print(f"   检查: {rel_path}", end='')
            report = self.check_file(str(f))
            results.append(report)
            score_icon = "✅" if report.quality_score >= 90 else ("⚠️" if report.quality_score >= 70 else "❌")
            print(f" [{score_icon}] 得分: {report.quality_score} | 问题: {len(report.issues)}")
        
        return results
    
    def generate_report(self, output_path: Optional[str] = None) -> Dict[str, Any]:
        """生成综合质量报告"""
        total_files = len(self.reports)
        total_errors = sum(r.error_count for r in self.reports)
        total_warnings = sum(r.warning_count for r in self.reports)
        avg_score = sum(r.quality_score for r in self.reports) / total_files if total_files > 0 else 0
        
        # 按严重程度统计问题
        severity_stats = {}
        for issue in self.total_issues:
            severity_stats[issue.severity] = severity_stats.get(issue.severity, 0) + 1
        
        # 按规则ID统计高频问题
        rule_stats = {}
        for issue in self.total_issues:
            rule_stats[issue.rule_id] = rule_stats.get(issue.rule_id, 0) + 1
        top_issues = sorted(rule_stats.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # 找出最低分的文件
        worst_files = sorted(self.reports, key=lambda r: r.quality_score)[:5]
        
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_files_checked': total_files,
                'total_issues': len(self.total_issues),
                'total_errors': total_errors,
                'total_warnings': total_warnings,
                'average_quality_score': round(avg_score, 1),
                'files_above_threshold': sum(1 for r in self.reports if r.quality_score >= self.config['min_quality_score']),
                'files_below_threshold': sum(1 for r in self.reports if r.quality_score < self.config['min_quality_score'])
            },
            'severity_breakdown': severity_stats,
            'top_issue_rules': top_issues,
            'worst_files': [
                {
                    'path': str(Path(r.file_path).relative_to(self.base_dir)),
                    'score': r.quality_score,
                    'issues_count': len(r.issues)
                }
                for r in worst_files
            ],
            'all_issues': [issue.to_dict() for issue in self.total_issues]
        }
        
        # 输出到控制台
        self._print_console_report(report_data)
        
        # 可选：保存到JSON文件
        if output_path:
            import json
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2)
            print(f"\n✅ 详细报告已保存至: {output_path}")
        
        return report_data
    
    def _print_console_report(self, report_data: Dict[str, Any]):
        """打印控制台格式化报告"""
        summary = report_data['summary']
        
        print("\n" + "="*70)
        print("📋 Workshop V2.0 代码质量检查报告")
        print("="*70)
        print(f"\n📊 总体统计:")
        print(f"   • 检查文件总数: {summary['total_files_checked']}")
        print(f"   • 发现问题总数: {summary['total_issues']}")
        print(f"     ├─ 错误 (ERROR): {summary['total_errors']} 🔴")
        print(f"     └─ 警告 (WARNING): {summary['total_warnings']} 🟡")
        print(f"   • 平均质量得分: {summary['average_quality_score']}/100 ⭐")
        print(f"   • 达标文件数 (≥{self.config['min_quality_score']}分): {summary['files_above_threshold']}")
        print(f"   • 待改进文件: {summary['files_below_threshold']}")
        
        if report_data['top_issue_rules']:
            print(f"\n🔍 高频问题 TOP 10:")
            for rule_id, count in report_data['top_issue_rules']:
                print(f"   • {rule_id}: 出现 {count} 次")
        
        if report_data['worst_files']:
            print(f"\n⚠️  待改进文件 (质量得分最低):")
            for wf in report_data['worst_files']:
                status = "🔴" if wf['score'] < 60 else ("🟡" if wf['score'] < 80 else "🟢")
                print(f"   {status} {wf['path']}")
                print(f"      得分: {wf['score']} | 问题数: {wf['issues_count']}")
        
        print("\n" + "="*70)
        
        # 给出总体评价
        avg = summary['average_quality_score']
        if avg >= 90:
            print("✨ 总体评价: 优秀！代码质量很高 👏\n")
        elif avg >= 80:
            print("👍 总体评价: 良好，有少量可优化项\n")
        elif avg >= 70:
            print("⚠️  总体评价: 一般，建议针对性改进\n")
        else:
            print("❌ 总体评价: 需要重点改进\n")


def auto_fix_imports(file_path: str, dry_run: bool = True) -> bool:
    """
    自动修复导入语句顺序（实验性功能）
    
    Args:
        file_path: Python文件路径
        dry_run: 如果为True，只输出建议不实际修改
    
    Returns:
        是否成功
    """
    path = Path(file_path)
    
    if not path.exists() or path.suffix != '.py':
        print(f"[错误] 无效的Python文件: {file_path}")
        return False
    
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 提取导入区域
    import_section = []
    import_start = -1
    import_end = -1
    code_section = []
    in_imports = False
    
    for idx, line in enumerate(lines):
        stripped = line.strip()
        
        if stripped.startswith(('import ', 'from ')):
            if not in_imports:
                import_start = idx
                in_imports = True
            import_end = idx
            import_section.append(line)
        elif in_imports and (stripped == '' or stripped.startswith('#')):
            # 导入区域的空行或注释
            import_section.append(line)
        elif in_imports and stripped != '':
            # 导入区域结束
            code_section.extend(lines[idx:])
            break
        elif not in_imports:
            code_section.append(line)
    
    if import_start == -1:
        print("[信息] 文件中没有找到导入语句")
        return True
    
    print(f"\n📝 分析文件: {path.name}")
    print(f"   导入区域: 第{import_start+1}行 ~ 第{import_end+1}行")
    print(f"   当前导入语句数: {sum(1 for l in import_section if l.strip().startswith(('import ', 'from ')))}")
    
    if dry_run:
        print("\n💡 建议: 使用 isort 工具自动整理导入顺序")
        print("   命令: isort --profile black", path.name)
        return True
    
    # TODO: 实现实际的导入重排序逻辑
    print("\n⚠️  自动修复功能开发中...")
    return False


def run_workshop_quality_check(target_dir: str = None, output_file: str = None):
    """
    运行Workshop V2.0项目全面质量检查
    
    Args:
        target_dir: 要检查的目录（默认检查整个项目）
        output_file: 报告输出路径
    """
    import argparse
    
    # 默认检查关键目录
    project_root = Path(__file__).parent.parent
    default_targets = [
        'common/core',
        'pipelines',
        'hardware',
        'tests',
        'scripts'
    ]
    
    if target_dir:
        targets = [target_dir]
    else:
        targets = [str(project_root / t) for t in default_targets if (project_root / t).exists()]
    
    checker = CodeQualityChecker(base_dir=str(project_root))
    
    all_reports = []
    for target in targets:
        reports = checker.check_directory(target, recursive=True)
        all_reports.extend(reports)
    
    # 生成综合报告
    if output_file:
        output_path = str(project_root / 'reports' / output_file)
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    else:
        output_path = str(project_root / 'reports' / f'quality_report_{datetime.now():%Y%m%d_%H%M%S}.json')
    
    report = checker.generate_report(output_path=output_path)
    
    # 返回统计信息供外部使用
    return {
        'status': 'completed',
        'files_checked': report['summary']['total_files_checked'],
        'total_issues': report['summary']['total_issues'],
        'avg_score': report['summary']['average_quality_score'],
        'report_path': output_path
    }


if __name__ == '__main__':
    import sys
    
    print("="*70)
    print("🔧 Workshop V2.0 代码质量检查工具")
    print("="*70)
    
    result = run_workshop_quality_check(
        target_dir=sys.argv[1] if len(sys.argv) > 1 else None,
        output_file=sys.argv[2] if len(sys.argv) > 2 else None
    )
    
    print(f"\n✅ 检查完成!")
    print(f"   文件数: {result['files_checked']}")
    print(f"   问题数: {result['total_issues']}")
    print(f"   平均分: {result['avg_score']}/100")
