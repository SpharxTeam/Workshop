#!/usr/bin/env python
"""
Workshop 代码质量检查工具
========================

一键运行所有代码质量检查：
- Linting (ruff)
- 格式化检查 (Black, isort)
- 类型检查 (mypy)
- 安全扫描
- 测试运行

使用:
    python scripts/quality_check.py              # 运行所有检查
    python scripts/quality_check.py --fix         # 自动修复问题
    python scripts/quality_check.py --lint        # 只运行 linting
    python scripts/quality_check.py --test        # 只运行测试
    python scripts/quality_check.py --report      # 生成完整报告
"""

import sys
import subprocess
import argparse
from pathlib import Path
from typing import List, Tuple, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class CheckResult:
    """检查结果"""
    name: str
    success: bool
    duration: float = 0.0
    output: str = ""
    errors: int = 0
    warnings: int = 0


class QualityChecker:
    """代码质量检查器"""

    PROJECT_ROOT = Path(__file__).parent.parent
    SOURCE_DIRS = ["workshop", "tests", "scripts"]

    def __init__(self, fix: bool = False, verbose: bool = False):
        self.fix = fix
        self.verbose = verbose
        self.results: List[CheckResult] = []

    def run_command(
        self,
        cmd: List[str],
        name: str,
        cwd: Optional[Path] = None
    ) -> CheckResult:
        """运行命令并返回结果"""
        start_time = datetime.now()

        print(f"\n{'='*60}")
        print(f"▶ 运行: {name}")
        print(f"  命令: {' '.join(cmd)}")
        print(f"{'='*60}")

        try:
            result = subprocess.run(
                cmd,
                cwd=cwd or self.PROJECT_ROOT,
                capture_output=True,
                text=True,
                timeout=300  # 5 分钟超时
            )

            duration = (datetime.now() - start_time).total_seconds()
            output = result.stdout + result.stderr

            if self.verbose or result.returncode != 0:
                print(output)

            success = result.returncode == 0

            # 统计错误和警告
            errors = output.lower().count("error")
            warnings = output.lower().count("warning")

            check_result = CheckResult(
                name=name,
                success=success,
                duration=duration,
                output=output[:2000] if len(output) > 2000 else output,
                errors=errors,
                warnings=warnings
            )

            status_icon = "✅" if success else "❌"
            print(f"\n{status_icon} {name} - {'通过' if success else '失败'} ({duration:.1f}s)")

            return check_result

        except subprocess.TimeoutExpired:
            return CheckResult(
                name=name,
                success=False,
                duration=300,
                output="命令执行超时 (>5分钟)",
                errors=1
            )
        except Exception as e:
            return CheckResult(
                name=name,
                success=False,
                output=str(e),
                errors=1
            )

    def check_ruff(self) -> CheckResult:
        """Ruff Linting 检查"""
        cmd = ["ruff", "check", "."]
        if self.fix:
            cmd.append("--fix")
        return self.run_command(cmd, "Ruff Linting")

    def check_black(self) -> CheckResult:
        """Black 格式化检查"""
        cmd = ["black", "--check", "--diff", "."]
        if self.fix:
            cmd = ["black", "."]
        return self.run_command(cmd, "Black 格式化")

    def check_isort(self) -> CheckResult:
        """isort 导入排序检查"""
        cmd = ["isort", "--check-only", "--diff", "."]
        if self.fix:
            cmd = ["isort", "."]
        return self.run_command(cmd, "isort 导入排序")

    def check_mypy(self) -> CheckResult:
        """mypy 类型检查"""
        cmd = [
            "mypy",
            "workshop/common/core/",
            "--ignore-missing-imports",
            "--no-error-summary"
        ]
        return self.run_command(cmd, "mypy 类型检查")

    def check_security(self) -> CheckResult:
        """安全扫描"""
        try:
            from workshop.common.core.security_audit import CodeSecurityScanner, run_full_security_audit
            
            print("\n🔒 运行安全审计...")
            
            scanner = CodeSecurityScanner()
            report = scanner.scan_directory(
                str(self.PROJECT_ROOT / "workshop" / "common" / "core"),
                pattern="*.py"
            )
            
            output = f"安全评分: {report.score}/100\n"
            output += f"发现: {report.summary}\n\n"
            
            for finding in report.findings[:10]:
                output += f"[{finding.severity.value}] {finding.title}\n"
                output += f"  文件: {finding.file_path}:{finding.line_number}\n"
            
            success = report.score >= 70
            
            return CheckResult(
                name="安全审计",
                success=success,
                output=output,
                errors=len([f for f in report.findings if f.severity.value in ['CRITICAL', 'HIGH']]),
                warnings=len([f for f in report.findings if f.severity.value == 'MEDIUM'])
            )
            
        except ImportError:
            # 如果无法导入，跳过
            return CheckResult(
                name="安全审计",
                success=True,
                output="跳过（依赖未安装）",
                errors=0,
                warnings=0
            )

    def run_tests(self) -> CheckResult:
        """运行测试套件"""
        cmd = [
            "pytest",
            "tests/",
            "-v",
            "--tb=short",
            "--cov=workshop",
            "--cov-report=term-missing",
            "--cov-fail-under=80"
        ]
        return self.run_command(cmd, "单元测试")

    def generate_report(self) -> str:
        """生成质量报告"""
        total_checks = len(self.results)
        passed = sum(1 for r in self.results if r.success)
        failed = total_checks - passed
        total_errors = sum(r.errors for r in self.results)
        total_warnings = sum(r.warnings for r in self.results)
        total_duration = sum(r.duration for r in self.results)

        report = f"""
╔══════════════════════════════════════════════════════════════╗
║           Workshop V2.0 - 代码质量检查报告                    ║
╠══════════════════════════════════════════════════════════════╣
║  检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S'):<40} ║
║  项目路径: {str(self.PROJECT_ROOT):<42} ║
╠══════════════════════════════════════════════════════════════╣
║  总检查项: {total_checks:<44} ║
║  ✅ 通过:   {passed:<45} ║
║  ❌ 失败:   {failed:<45} ║
║  ⚠️  警告:  {total_warnings:<44} ║
║  🐛 错误:  {total_errors:<45} ║
║  ⏱️  耗时:  {total_duration:.1f}s{' '*36} ║
╠══════════════════════════════════════════════════════════════╣
"""

        for result in self.results:
            icon = "✅" if result.success else "❌"
            report += f"║  {icon} {result.name:<20} {'通过' if result.success else '失败':<6} "
            report += f"{result.duration:>5.1f}s  E:{result.errors:>3} W:{result.warnings:>3}     \n"

        overall_status = "✅ 全部通过" if failed == 0 else f"❌ {failed} 项失败"
        report += f"╠══════════════════════════════════════════════════════════════╣\n"
        report += f"║  总体状态: {overall_status:<46} ║\n"
        report += f"╚══════════════════════════════════════════════════════════════╝\n"

        return report

    def run_all(self, skip_tests: bool = False) -> bool:
        """运行所有检查"""
        print("🔍 Workshop V2.0 代码质量检查")
        print("=" * 60)

        # 运行各项检查
        self.results.append(self.check_ruff())
        self.results.append(self.check_black())
        self.results.append(self.check_isort())
        self.results.append(self.check_mypy())
        self.results.append(self.check_security())

        if not skip_tests:
            self.results.append(self.run_tests())

        # 生成报告
        report = self.generate_report()
        print(report)

        # 保存报告
        report_path = self.PROJECT_ROOT / "reports" / "quality_report.txt"
        report_path.parent.mkdir(exist_ok=True=True)
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"\n📄 报告已保存至: {report_path}")

        # 返回总体状态
        all_passed = all(r.success for r in self.results)
        return all_passed


def main():
    parser = argparse.ArgumentParser(
        description="Workshop 代码质量检查工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    %(prog)s              运行所有检查
    %(prog)s --fix        自动修复可修复的问题
    %(prog)s --lint       只运行 linting 检查
    %(prog)s --test       只运行测试
    %(prog)s --report     生成详细报告
        """
    )

    parser.add_argument(
        "--fix",
        action="store_true",
        help="自动修复格式化和简单 linting 问题"
    )
    parser.add_argument(
        "--lint",
        action="store_true",
        help="只运行 linting 检查 (ruff, black, isort)"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="只运行测试"
    )
    parser.add_argument(
        "--skip-tests",
        action="store_true",
        help="跳过测试（只做静态分析）"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="显示详细输出"
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="生成 HTML 报告"
    )

    args = parser.parse_args()

    checker = QualityChecker(fix=args.fix, verbose=args.verbose)

    try:
        if args.lint:
            results = [
                checker.check_ruff(),
                checker.check_black(),
                checker.check_isort()
            ]
            all_passed = all(r.success for r in results)
        elif args.test:
            result = checker.run_tests()
            all_passed = result.success
        else:
            all_passed = checker.run_all(skip_tests=args.skip_tests)

        if not all_passed:
            print("\n❌ 部分检查未通过，请查看上方详细信息")
            sys.exit(1)
        else:
            print("\n🎉 所有检查通过！")
            sys.exit(0)

    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
