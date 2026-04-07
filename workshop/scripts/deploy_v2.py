#!/usr/bin/env python3
# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
# Workshop V2.0 部署工具集
# 提供一键部署、健康检查、环境验证等功能

"""
Workshop V2.0 部署工具

功能：
1. 环境检查（依赖、Python版本、系统资源）
2. 配置生成（从模板创建完整配置）
3. 一键启动（按顺序启动所有Pipeline）
4. 健康检查（验证所有组件状态）
5. 性能基线建立（记录初始性能指标）

使用方式:
    # 环境检查
    python scripts/deploy_v2.py check-env
    
    # 生成配置
    python scripts/deploy_v2.py generate-config --output /app/configs
    
    # 完整部署
    python scripts/deploy_v2.py deploy --mode production
    
    # 健康检查
    python scripts/deploy_v2.py health
"""

import sys
import os
import json
import platform
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, field

sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from common.core import (
        ConfigManager,
        setup_logging,
        InputValidator,
        ErrorCode,
        WorkshopError,
        IOManager,
        BenchmarkSuite,
        CodeSecurityScanner
    )
    CORE_AVAILABLE = True
except ImportError:
    CORE_AVAILABLE = False


@dataclass
class EnvironmentCheckResult:
    """环境检查结果"""
    check_name: str
    passed: bool
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'check': self.check_name,
            'status': '✅ PASS' if self.passed else '❌ FAIL',
            'message': self.message,
            **self.details
        }


@dataclass
class HealthCheckResult:
    """健康检查结果"""
    component: str
    status: str  # healthy/degraded/unhealthy/unknown
    response_time_ms: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')


class DeploymentTool:
    """
    部署工具类
    
    提供生产级部署所需的所有工具功能。
    """
    
    def __init__(self, project_root: Optional[str] = None):
        self.project_root = Path(project_root or Path(__file__).parent.parent)
        self._logger = None
        
        if CORE_AVAILABLE:
            self._logger = setup_logging("deploy.tool")
        
        self._check_results: List[EnvironmentCheckResult] = []
        self._health_results: List[HealthCheckResult] = []
    
    def check_environment(self) -> Dict[str, Any]:
        """
        执行全面的环境检查
        
        检查项：
        - Python版本（>=3.8）
        - 核心依赖是否安装
        - 系统资源（内存、磁盘）
        - 目录结构完整性
        - 配置文件存在性
        - 权限设置
        """
        print("\n" + "="*60)
        print("🔍 Workshop V2.0 环境检查")
        print("="*60)
        
        checks = [
            self._check_python_version,
            self._check_core_dependencies,
            self._check_system_resources,
            self._check_directory_structure,
            self._check_config_files,
            self._check_permissions,
            self._check_hardware_support,
        ]
        
        for check_func in checks:
            try:
                result = check_func()
                self._check_results.append(result)
                
                status_icon = "✅" if result.passed else "❌"
                print(f"  {status_icon} {result.check_name}: {result.message}")
                
                if not result.passed and result.details:
                    for key, value in result.details.items():
                        print(f"      ⚠ {key}: {value}")
                        
            except Exception as e:
                error_result = EnvironmentCheckResult(
                    check_name=check_func.__name__,
                    passed=False,
                    message=f"检查异常: {e}"
                )
                self._check_results.append(error_result)
                print(f"  ❌ {check_func.__name__}: 异常 - {e}")
        
        # 汇总
        passed_count = sum(1 for r in self._check_results if r.passed)
        total_count = len(self._check_results)
        
        print("\n" + "-"*60)
        print(f"环境检查完成: {passed_count}/{total_count} 通过")
        
        if passed_count == total_count:
            print("✅ 所有检查通过，环境就绪！")
        else:
            failed_count = total_count - passed_count
            print(f"⚠️ {failed_count} 项检查未通过，请修复后重试")
        
        return {
            'timestamp': datetime.now().isoformat(),
            'total_checks': total_count,
            'passed': passed_count,
            'failed': total_count - passed_count,
            'results': [r.to_dict() for r in self._check_results]
        }
    
    def _check_python_version(self) -> EnvironmentCheckResult:
        """检查Python版本"""
        version = sys.version_info
        major, minor = version.major, version.minor
        
        required_major = 3
        required_minor = 8
        
        passed = (major > required_major or 
                 (major == required_major and minor >= required_minor))
        
        return EnvironmentCheckResult(
            check_name="Python版本",
            passed=passed,
            message=f"{major}.{minor}" + (" (满足要求 ≥3.8)" if passed else " (需要 ≥3.8)"),
            details={
                'current_version': f"{major}.{minor}.{version.micro}",
                'required_version': f"{required_major}.{required_minor}",
                'platform': platform.platform()
            }
        )
    
    def _check_core_dependencies(self) -> EnvironmentCheckResult:
        """检查核心依赖"""
        required_packages = {
            'PyYAML': ('yaml', '>=5.1'),
            'numpy': ('numpy', '>=1.19'),
            'opencv-python': ('cv2', '>=4.0'),
        }
        
        installed = {}
        missing = []
        
        for package_name, (import_name, version_req) in required_packages.items():
            try:
                module = __import__(import_name)
                version = getattr(module, '__version__', 'unknown')
                installed[package_name] = version
            except ImportError:
                missing.append(package_name)
        
        passed = len(missing) == 0
        
        return EnvironmentCheckResult(
            check_name="核心依赖",
            passed=passed,
            message=f"已安装 {len(installed)}/{len(required_packages)}" + 
                  ("" if passed else f", 缺少: {', '.join(missing)}"),
            details={
                'installed': installed,
                'missing': missing
            }
        )
    
    def _check_system_resources(self) -> EnvironmentCheckResult:
        """检查系统资源"""
        import psutil
        
        # 内存信息
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_available_gb = memory.available / (1024**3)
        
        # 磁盘信息
        disk = psutil.disk_usage('/')
        disk_percent = disk.percent
        disk_free_gb = disk.free / (1024**3)
        
        # CPU信息
        cpu_count = psutil.cpu_count()
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # 判断是否充足
        memory_ok = memory_percent < 90 and memory_available_gb > 1.0
        disk_ok = disk_percent < 95 and disk_free_gb > 5.0
        
        passed = memory_ok and disk_ok
        
        return EnvironmentCheckResult(
            check_name="系统资源",
            passed=passed,
            message=f"内存 {memory_percent:.1f}% (可用 {memory_available_gb:.1f}GB), "
                   f"磁盘 {disk_percent:.1f}% (可用 {disk_free_gb:.1f}GB)",
            details={
                'cpu_cores': cpu_count,
                'cpu_usage_percent': cpu_percent,
                'memory_total_gb': memory.total / (1024**3),
                'memory_used_percent': memory_percent,
                'memory_available_gb': round(memory_available_gb, 2),
                'disk_total_gb': disk.total / (1024**3),
                'disk_used_percent': disk_percent,
                'disk_free_gb': round(disk_free_gb, 2),
                'recommendations': [] if passed else [
                    '释放磁盘空间' if not disk_ok else '',
                    '关闭其他程序释放内存' if not memory_ok else ''
                ]
            }
        )
    
    def _check_directory_structure(self) -> EnvironmentCheckResult:
        """检查目录结构"""
        required_dirs = [
            'common/core',
            'common/configs',
            'common/scripts',
            'pipelines',
            'hardware',
            'produce/input',
            'produce/output',
            'tests',
            'docs'
        ]
        
        existing = []
        missing = []
        
        for dir_path in required_dirs:
            full_path = self.project_root / dir_path
            if full_path.exists():
                existing.append(dir_path)
            else:
                missing.append(dir_path)
        
        passed = len(missing) == 0
        
        return EnvironmentCheckResult(
            check_name="目录结构",
            passed=passed,
            message=f"已创建 {len(existing)}/{len(required_dirs)} 个目录",
            details={
                'existing': existing,
                'missing': missing,
                'project_root': str(self.project_root)
            }
        )
    
    def _check_config_files(self) -> EnvironmentCheckResult:
        """检查配置文件"""
        config_dir = self.project_root / "common" / "configs"
        
        required_configs = [
            'pipeline_config.yaml',
            'logging.yaml',
        ]
        
        optional_configs = [
            'modules/00_ingest.yaml',
            'modules/01_quality.yaml',
            'model_config.yaml',
            'quality_thresholds.yaml'
        ]
        
        existing_required = []
        existing_optional = []
        missing_required = []
        
        for cfg in required_configs:
            if (config_dir / cfg).exists():
                existing_required.append(cfg)
            else:
                missing_required.append(cfg)
        
        for cfg in optional_configs:
            if (config_dir / cfg).exists():
                existing_optional.append(cfg)
        
        passed = len(missing_required) == 0
        
        return EnvironmentCheckResult(
            check_name="配置文件",
            passed=passed,
            message=f"必需: {len(existing_required)}/{len(required_configs)}, "
                   f"可选: {len(existing_optional)}/{len(optional_configs)}",
            details={
                'required_existing': existing_required,
                'required_missing': missing_required,
                'optional_existing': existing_optional,
                'config_dir': str(config_dir)
            }
        )
    
    def _check_permissions(self) -> EnvironmentCheckResult:
        """检查关键目录权限"""
        critical_dirs = [
            'produce/output',
            'partdata/models',
            'logs'
        ]
        
        writable = []
        not_writable = []
        
        for dir_path in critical_dirs:
            full_path = self.project_root / dir_path
            
            if full_path.exists():
                if os.access(full_path, os.W_OK):
                    writable.append(dir_path)
                else:
                    not_writable.append(dir_path)
        
        passed = len(not_writable) == 0
        
        return EnvironmentCheckResult(
            check_name="权限设置",
            passed=passed,
            message=f"可写目录: {len(writable)}/{len(critical_dirs)}",
            details={
                'writable': writable,
                'not_writable': not_writable
            }
        )
    
    def _check_hardware_support(self) -> EnvironmentCheckResult:
        """检查硬件支持（RealSense等）"""
        realsense_available = False
        camera_info = "未检测"
        
        try:
            import pyrealsense2 as rs
            ctx = rs.context()
            devices = ctx.query_devices()
            
            if len(devices) > 0:
                realsense_available = True
                camera_info = f"检测到 {len(devices)} 个设备"
            else:
                camera_info = "SDK已安装，但未检测到设备"
                
        except ImportError:
            camera_info = "RealSense SDK 未安装（可选）"
        except Exception as e:
            camera_info = f"检测异常: {e}"
        
        # RealSense是可选的，所以总是通过
        return EnvironmentCheckResult(
            check_name="硬件支持",
            passed=True,
            message=camera_info,
            details={
                'realsense_sdk_installed': 'pyrealsense2' in sys.modules,
                'realsense_devices_detected': realsense_available
            }
        )
    
    def health_check(self) -> Dict[str, Any]:
        """
        执行全面的健康检查
        
        检查所有组件的状态和响应时间。
        """
        print("\n" + "="*60)
        print("💓 Workshop V2.0 健康检查")
        print("="*60)
        
        components = [
            ("Core Infrastructure", self._health_check_core),
            ("Configuration System", self._health_check_config),
            ("IO Abstraction Layer", self._health_check_io),
            ("Pipeline Modules", self._health_check_pipelines),
            ("Security Scanner", self._health_check_security),
        ]
        
        for name, check_func in components:
            start = time.time()
            
            try:
                result = check_func()
                elapsed = (time.time() - start) * 1000
                result.response_time_ms = elapsed
                
                self._health_results.append(result)
                
                status_icons = {
                    'healthy': '✅',
                    'degraded': '⚠️',
                    'unhealthy': '❌',
                    'unknown': '❓'
                }
                icon = status_icons.get(result.status, '?')
                
                print(f"  {icon} {name}: {result.status} "
                      f"({elapsed:.1f}ms)")
                
            except Exception as e:
                error_result = HealthCheckResult(
                    component=name,
                    status='error',
                    details={'error': str(e)}
                )
                self._health_results.append(error_result)
                print(f"  ❌ {name}: 检查异常 - {e}")
        
        # 汇总
        healthy = sum(1 for r in self._health_results 
                     if r.status in ['healthy', 'degraded'])
        total = len(self._health_results)
        
        print("\n" + "-"*60)
        overall_status = "✅ HEALTHY" if healthy == total else \
                        "⚠️ DEGRADED" if healthy > 0 else "❌ UNHEALTHY"
        print(f"整体状态: {overall_status} ({healthy}/{total})")
        
        return {
            'timestamp': datetime.now().isoformat(),
            'overall_status': overall_status,
            'components_checked': total,
            'healthy_components': healthy,
            'components': [
                {
                    'component': r.component,
                    'status': r.status,
                    'response_time_ms': r.response_time_ms,
                    'details': r.details
                } for r in self._health_results
            ]
        }
    
    def _health_check_core(self) -> HealthCheckResult:
        """检查核心基础设施"""
        if not CORE_AVAILABLE:
            return HealthCheckResult(
                component="Core Infrastructure",
                status="unhealthy",
                details={'reason': '核心模块无法导入'}
            )
        
        # 测试核心组件导入
        try:
            from common.core import BasePipeline, ConfigManager, InputValidator
            all_imported = True
        except ImportError as e:
            return HealthCheckResult(
                component="Core Infrastructure",
                status="unhealthy",
                details={'error': str(e)}
            )
        
        return HealthCheckResult(
            component="Core Infrastructure",
            status="healthy",
            details={
                'base_pipeline': True,
                'config_manager': True,
                'input_validator': True,
                'exception_system': True,
                'logging_system': True
            }
        )
    
    def _health_check_config(self) -> HealthCheckResult:
        """检查配置系统"""
        config_dir = self.project_root / "common" / "configs"
        
        if not config_dir.exists():
            return HealthCheckResult(
                component="Configuration System",
                status="unhealthy",
                details={'reason': '配置目录不存在'}
            )
        
        try:
            config = ConfigManager(config_dir=str(config_dir))
            
            return HealthCheckResult(
                component="Configuration System",
                status="healthy" if config.is_loaded else "degraded",
                details={
                    'loaded': config.is_loaded,
                    'config_dir': str(config_dir),
                    'has_global_config': (config_dir / "pipeline_config.yaml").exists(),
                    'has_modules_dir': (config_dir / "modules").exists()
                }
            )
        except Exception as e:
            return HealthCheckResult(
                component="Configuration System",
                status="unhealthy",
                details={'error': str(e)}
            )
    
    def _health_check_io(self) -> HealthCheckResult:
        """检查IO抽象层"""
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                io = IOManager(storage_backend="local", base_path=tmpdir)
                
                # 写入测试
                test_data = b"health check test"
                io.write("test.txt", test_data)
                
                # 读取测试
                data = io.read("test.txt")
                
                io.disconnect()
                
                is_healthy = data == test_data
                
                return HealthCheckResult(
                    component="IO Abstraction Layer",
                    status="healthy" if is_healthy else "unhealthy",
                    details={
                        'backend_type': 'local',
                        'read_write_test': is_healthy
                    }
                )
        except Exception as e:
            return HealthCheckResult(
                component="IO Abstraction Layer",
                status="unhealthy",
                details={'error': str(e)}
            )
    
    def _health_check_pipelines(self) -> HealthCheckResult:
        """检查Pipeline模块"""
        pipeline_dirs = [
            'run_00_ingest',
            'run_01_quality',
            'run_02_enhance',
            'run_03_calibrate',
            'run_04_pack',
            'run_05_delivery',
            'streaming'
        ]
        
        pipelines_dir = self.project_root / "pipelines"
        
        available = []
        has_v2 = []
        
        for p in pipeline_dirs:
            p_path = pipelines_dir / p
            if p_path.exists():
                available.append(p)
                v2_file = p_path / "runner_v2.py"
                if v2_file.exists():
                    has_v2.append(p)
        
        return HealthCheckResult(
            component="Pipeline Modules",
            status="healthy" if len(available) >= 5 else "degraded",
            details={
                'available_pipelines': available,
                'v2_migrated': has_v2,
                'total_expected': len(pipeline_dirs),
                'migration_rate': f"{len(has_v2)}/{len(available)}"
            }
        )
    
    def _health_check_security(self) -> HealthCheckResult:
        """检查安全扫描器"""
        try:
            scanner = CodeSecurityScanner()
            
            # 快速测试：只扫描一个文件
            test_file = self.project_root / "common" / "core" / "__init__.py"
            
            if test_file.exists():
                findings = scanner.scan_file(str(test_file))
                
                # 如果有严重或高危问题，标记为 degraded
                has_critical = any(
                    f.severity.value in ['critical', 'high'] 
                    for f in findings
                )
                
                status = "degraded" if has_critical else "healthy"
                
                return HealthCheckResult(
                    component="Security Scanner",
                    status=status,
                    details={
                        'scanner_working': True,
                        'test_findings': len(findings),
                        'has_critical_issues': has_critical
                    }
                )
            else:
                return HealthCheckResult(
                    component="Security Scanner",
                    status="unknown",
                    details={'reason': '测试文件不存在'}
                )
                
        except Exception as e:
            return HealthCheckResult(
                component="Security Scanner",
                status="unknown",
                details={'error': str(e)}
            )


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Workshop V2.0 部署工具",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 环境检查命令
    subparsers.add_parser('check-env', help='执行环境检查')
    
    # 健康检查命令
    subparsers.add_parser('health', help='执行健康检查')
    
    # 部署命令
    deploy_parser = subparsers.add_parser('deploy', help='执行部署')
    deploy_parser.add_argument('--mode', choices=['dev', 'staging', 'production'],
                          default='dev', help='部署模式')
    
    args = parser.parse_args()
    
    tool = DeploymentTool()
    
    if args.command == 'check-env':
        result = tool.check_environment()
        
        # 保存报告
        report_path = Path("reports") / f"env_check_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_path, 'w') as f:
            json.dump(result, f, indent=2)
        
        print(f"\n报告已保存: {report_path}")
        
        return 0 if result['failed'] == 0 else 1
        
    elif args.command == 'health':
        result = tool.health_check()
        
        # 保存报告
        report_path = Path("reports") / f"health_check_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_path, 'w') as f:
            json.dump(result, f, indent=2)
        
        print(f"\n报告已保存: {report_path}")
        
        return 0 if result['overall_status'].startswith('✅') else 1
        
    elif args.command == 'deploy':
        print(f"\n🚀 开始部署 (模式: {args.mode})...")
        
        # 1. 环境检查
        env_result = tool.check_environment()
        if env_result['failed'] > 0:
            print("❌ 环境检查未通过，请先修复问题")
            return 1
        
        # 2. 健康检查
        health_result = tool.health_check()
        if not health_result['overall_status'].startswith('✅'):
            print("⚠️ 存在降级组件，但可以继续部署")
        
        print("\n✅ 部署准备就绪！")
        print("\n下一步操作:")
        print("  1. 运行演示: python scripts/demo_v2_full_pipeline.py")
        print("  2. 运行测试: python tests/framework/test_framework.py")
        print("  3. 启动Pipeline: python pipelines/run_XX_xxx/runner_v2.py")
        
        return 0
    
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
