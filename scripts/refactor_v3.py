#!/usr/bin/env python
"""
Workshop V3.0 深度重构自动化脚本
================================

参考 AgentOS 和 Deepness 架构，对 Workshop 进行全面重构

使用:
    python scripts/refactor_v3.py --dry-run    # 预览变更
    python scripts/refactor_v3.py --execute    # 执行重构
    python scripts/refactor_v3.py --verify     # 验证重构结果
"""

import os
import sys
import shutil
from pathlib import Path
from typing import List, Tuple, Dict
from dataclasses import dataclass
from datetime import datetime


@dataclass
class FileMigration:
    """文件迁移记录"""
    src: str
    dst: str
    action: str  # move, copy, create
    description: str


class WorkshopRefactorV3:
    """Workshop V3.0 重构工具"""

    PROJECT_ROOT = Path(__file__).parent.parent

    # 核心模块迁移映射
    CORE_MIGRATIONS = [
        # Abstractions 层
        FileMigration(
            src="common/core/base_pipeline.py",
            dst="workshop/core/abstractions/pipeline.py",
            action="move",
            description="Pipeline ABC → core/abstractions"
        ),
        FileMigration(
            src="common/core/io_abstraction.py",
            dst="workshop/core/abstractions/storage.py",
            action="move",
            description="IO 抽象 → core/abstractions"
        ),
        FileMigration(
            src="common/core/exceptions.py",
            dst="workshop/core/abstractions/models.py",
            action="move",
            description="异常模型 → core/abstractions"
        ),
        
        # Services 层
        FileMigration(
            src="common/core/config_manager.py",
            dst="workshop/core/services/config_service.py",
            action="move",
            description="ConfigManager → ConfigService"
        ),
        FileMigration(
            src="common/core/logging_setup.py",
            dst="workshop/core/services/logging_service.py",
            action="move",
            description="日志设置 → LoggingService"
        ),
        
        # Security 层
        FileMigration(
            src="common/core/input_validator.py",
            dst="workshop/core/security/validation_service.py",
            action="move",
            description="输入验证 → ValidationService"
        ),
        FileMigration(
            src="common/core/security_audit.py",
            dst="workshop/core/security/security_service.py",
            action="move",
            description="安全审计 → SecurityService"
        ),
        
        # Observability 层
        FileMigration(
            src="common/core/metrics.py",
            dst="workshop/core/observability/metrics_service.py",
            action="move",
            description="指标服务 → MetricsService"
        ),
        FileMigration(
            src="common/core/performance.py",
            dst="workshop/core/observability/performance.py",
            action="move",
            description="性能工具 → Observability"
        ),
    ]

    # Commons 层迁移
    COMMONS_MIGRATIONS = [
        FileMigration(
            src="common/scripts/",
            dst="commons/scripts/",
            action="move",
            description="通用脚本 → commons/"
        ),
        FileMigration(
            src="common/schemas/",
            dst="commons/schemas/",
            action="move",
            description="数据模式 → commons/"
        ),
        FileMigration(
            src="common/dashboard/",
            dst="services/dashboard/",
            action="move",
            description="仪表板 → services/"
        ),
        FileMigration(
            src="common/configs/",
            dst="config/application/",
            action="move",
            description="应用配置 → config/application/"
        ),
    ]

    # 新增模块
    NEW_MODULES = [
        "workshop/orchestration/",
        "workshop/orchestration/__init__.py",
        "workshop/orchestration/scheduler.py",
        "workshop/orchestration/task_queue.py",
        "workshop/orchestration/workflow_engine.py",
        
        "workshop/core/observability/tracing_service.py",
        
        "services/gateway/",
        "services/monitor/",
        "services/exporter/",
        
        "commons/platform/",
        "commons/tests/",
    ]

    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.migration_log: List[Dict] = []
        self.error_log: List[str] = []

    def create_directory(self, path: Path) -> bool:
        """创建目录"""
        try:
            if self.dry_run:
                print(f"[DRY-RUN] 创建目录：{path}")
            else:
                path.mkdir(parents=True, exist_ok=True)
                print(f"✅ 创建目录：{path}")
            return True
        except Exception as e:
            error_msg = f"创建目录失败 {path}: {e}"
            self.error_log.append(error_msg)
            print(f"❌ {error_msg}")
            return False

    def move_file(self, src: Path, dst: Path) -> bool:
        """移动文件"""
        try:
            if not src.exists():
                error_msg = f"源文件不存在：{src}"
                self.error_log.append(error_msg)
                print(f"⚠️  {error_msg}")
                return False

            if self.dry_run:
                print(f"[DRY-RUN] 移动：{src} → {dst}")
            else:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(src), str(dst))
                print(f"✅ 移动：{src} → {dst}")
            
            self.migration_log.append({
                'action': 'move',
                'src': str(src),
                'dst': str(dst)
            })
            return True

        except Exception as e:
            error_msg = f"移动文件失败 {src} → {dst}: {e}"
            self.error_log.append(error_msg)
            print(f"❌ {error_msg}")
            return False

    def create_file(self, path: Path, content: str = "") -> bool:
        """创建文件"""
        try:
            if self.dry_run:
                print(f"[DRY-RUN] 创建文件：{path}")
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"✅ 创建文件：{path}")
            return True
        except Exception as e:
            error_msg = f"创建文件失败 {path}: {e}"
            self.error_log.append(error_msg)
            print(f"❌ {error_msg}")
            return False

    def execute_migration(self, migrations: List[FileMigration]) -> int:
        """执行迁移"""
        success_count = 0
        
        for migration in migrations:
            src = self.PROJECT_ROOT / migration.src
            dst = self.PROJECT_ROOT / migration.dst

            if migration.action == "move":
                if self.move_file(src, dst):
                    success_count += 1
            elif migration.action == "create":
                if self.create_file(dst, migration.description):
                    success_count += 1

        return success_count

    def create_new_modules(self) -> int:
        """创建新模块"""
        success_count = 0
        
        for module in self.NEW_MODULES:
            path = self.PROJECT_ROOT / module
            
            if module.endswith('/'):
                if self.create_directory(path):
                    success_count += 1
            else:
                if self.create_file(path, f"# {module}\n# Auto-generated by refactor_v3.py\n"):
                    success_count += 1

        return success_count

    def create_init_files(self) -> int:
        """创建 __init__.py 文件"""
        init_files = [
            "workshop/core/__init__.py",
            "workshop/core/abstractions/__init__.py",
            "workshop/core/services/__init__.py",
            "workshop/core/security/__init__.py",
            "workshop/core/observability/__init__.py",
            
            "commons/__init__.py",
            "commons/utils/__init__.py",
            "commons/scripts/__init__.py",
            "commons/schemas/__init__.py",
            
            "services/__init__.py",
            "services/gateway/__init__.py",
            "services/monitor/__init__.py",
            "services/exporter/__init__.py",
        ]
        
        success_count = 0
        for init_file in init_files:
            path = self.PROJECT_ROOT / init_file
            module_name = init_file.replace('/', '.').rstrip('.__init__.py')
            
            content = f'''"""
{module_name}
{'=' * len(module_name)}

Auto-generated by refactor_v3.py
"""

__all__ = []
'''
            if self.create_file(path, content):
                success_count += 1
        
        return success_count

    def verify_structure(self) -> bool:
        """验证重构后的结构"""
        print("\n" + "="*60)
        print("🔍 验证重构后的项目结构...")
        print("="*60)
        
        required_dirs = [
            "workshop/core",
            "workshop/core/abstractions",
            "workshop/core/services",
            "workshop/core/security",
            "workshop/core/observability",
            "commons",
            "services",
        ]
        
        all_exist = True
        for dir_path in required_dirs:
            path = self.PROJECT_ROOT / dir_path
            exists = path.exists() and path.is_dir()
            status = "✅" if exists else "❌"
            print(f"{status} {dir_path}")
            if not exists:
                all_exist = False
        
        return all_exist

    def generate_report(self) -> str:
        """生成重构报告"""
        report = f"""
╔══════════════════════════════════════════════════════════╗
║        Workshop V3.0 重构执行报告                         ║
╠══════════════════════════════════════════════════════════╣
║  执行时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S'):<42} ║
║  模式：{'预览 (Dry-run)' if self.dry_run else '执行 (Execute)':<46} ║
╠══════════════════════════════════════════════════════════╣
║  迁移统计:                                               ║
║    核心模块迁移：{len(self.CORE_MIGRATIONS):<36} ║
║    Commons 迁移：{len(self.COMMONS_MIGRATIONS):<37} ║
║    新增模块：{len(self.NEW_MODULES):<39} ║
╠══════════════════════════════════════════════════════════╣
║  执行结果:                                               ║
║    成功迁移：{len(self.migration_log):<39} ║
║    失败操作：{len(self.error_log):<39} ║
╚══════════════════════════════════════════════════════════╝
"""
        
        if self.migration_log:
            report += "\n📦 迁移详情:\n"
            for item in self.migration_log[:20]:  # 只显示前 20 个
                report += f"  • {item['src']} → {item['dst']}\n"
        
        if self.error_log:
            report += "\n❌ 错误详情:\n"
            for error in self.error_log:
                report += f"  • {error}\n"
        
        return report

    def run(self) -> bool:
        """运行重构"""
        print("╔══════════════════════════════════════════════════╗")
        print("║    Workshop V3.0 深度重构工具                     ║")
        print("╠══════════════════════════════════════════════════╣")
        print(f"║  项目根目录：{str(self.PROJECT_ROOT):<36} ║")
        print(f"║  模式：{'预览 (Dry-run)' if self.dry_run else '执行 (Execute)':<40} ║")
        print("╚══════════════════════════════════════════════════╝")
        print()

        # Step 1: 创建新目录结构
        print("\n📁 Step 1: 创建新目录结构...")
        self.create_new_modules()
        
        # Step 2: 创建 __init__.py 文件
        print("\n📄 Step 2: 创建 __init__.py 文件...")
        self.create_init_files()
        
        # Step 3: 迁移核心模块
        print("\n🔄 Step 3: 迁移核心模块...")
        core_success = self.execute_migration(self.CORE_MIGRATIONS)
        print(f"✅ 核心模块迁移完成：{core_success}/{len(self.CORE_MIGRATIONS)}")
        
        # Step 4: 迁移 Commons 模块
        print("\n🔄 Step 4: 迁移 Commons 模块...")
        commons_success = self.execute_migration(self.COMMONS_MIGRATIONS)
        print(f"✅ Commons 迁移完成：{commons_success}/{len(self.COMMONS_MIGRATIONS)}")
        
        # Step 5: 验证结构
        print("\n🔍 Step 5: 验证重构后的结构...")
        verified = self.verify_structure()
        
        # Step 6: 生成报告
        print("\n📊 Step 6: 生成重构报告...")
        report = self.generate_report()
        print(report)
        
        # 保存报告
        if not self.dry_run:
            report_path = self.PROJECT_ROOT / "docs" / "REFACTORING_V3_EXECUTION_REPORT.md"
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(f"# Workshop V3.0 重构执行报告\n\n{report}\n")
            print(f"\n📄 报告已保存至：{report_path}")
        
        return verified and len(self.error_log) == 0


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Workshop V3.0 深度重构工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    %(prog)s --dry-run     # 预览变更
    %(prog)s --execute     # 执行重构
    %(prog)s --verify      # 验证结构
        """
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="预览变更，不实际执行"
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="执行重构"
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="验证重构后的结构"
    )
    
    args = parser.parse_args()
    
    if args.execute:
        refactor = WorkshopRefactorV3(dry_run=False)
        success = refactor.run()
        sys.exit(0 if success else 1)
    elif args.verify:
        refactor = WorkshopRefactorV3(dry_run=True)
        success = refactor.verify_structure()
        sys.exit(0 if success else 1)
    else:
        # 默认 dry-run
        refactor = WorkshopRefactorV3(dry_run=True)
        success = refactor.run()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
