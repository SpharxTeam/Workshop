# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
# Workshop 测试框架 - 参考 AgentOS 测试体系设计
# 提供统一的测试基础设施和工具

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass
import time

# 确保项目根目录在路径中
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


@dataclass
class TestResult:
    """测试结果"""
    test_name: str
    passed: bool
    duration: float = 0.0
    error: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class WorkshopTestCase:
    """
    Workshop 测试用例基类 - 参考 AgentOS 测试框架
    
    提供通用的测试工具方法：
    - 临时文件/目录管理
    - Mock 数据生成
    - 断言方法
    - 性能测量
    """
    
    @staticmethod
    def create_temp_dir(prefix: str = "test_") -> Path:
        """创建临时目录"""
        return Path(tempfile.mkdtemp(prefix=prefix))
    
    @staticmethod
    def create_temp_file(
        dir_path: Path,
        filename: str,
        content: str = "",
        suffix: str = ".txt"
    ) -> Path:
        """创建临时文件"""
        file_path = dir_path / f"{filename}{suffix}"
        file_path.write_text(content, encoding='utf-8')
        return file_path
    
    @staticmethod
    def create_sample_config(
        dir_path: Path,
        module_name: str,
        config_data: Optional[Dict] = None
    ) -> Path:
        """创建示例配置文件"""
        config_dir = dir_path / "common" / "configs"
        config_dir.mkdir(parents=True, exist_ok=True)
        
        modules_dir = config_dir / "modules"
        modules_dir.mkdir(parents=True, exist_ok=True)
        
        default_config = {
            'pipeline': {
                'input': '/app/produce/input/raw',
                'output': '/app/produce/output/datasets',
                'log_level': 'INFO'
            },
            'modules': {}
        }
        
        if config_data:
            default_config.update(config_data)
        
        config_file = modules_dir / f"{module_name}.yaml"
        import yaml
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(default_config, f, allow_unicode=True)
        
        # 同时创建全局配置
        global_config = config_dir / "pipeline_config.yaml"
        with open(global_config, 'w', encoding='utf-8') as f:
            yaml.dump(default_config.get('pipeline', {}), f, allow_unicode=True)
        
        return config_file
    
    @staticmethod
    def create_sample_image(
        dir_path: Path,
        filename: str = "test_image",
        width: int = 640,
        height: int = 480
    ) -> Path:
        """创建示例图像文件（使用 numpy 和 cv2）"""
        try:
            import numpy as np
            import cv2
            
            image = np.random.randint(0, 255, (height, width, 3), dtype=np.uint8)
            image_path = dir_path / f"{filename}.jpg"
            cv2.imwrite(str(image_path), image)
            
            return image_path
        except ImportError:
            # 如果没有 opencv，创建一个假文件
            image_path = dir_path / f"{filename}.jpg"
            image_path.write_bytes(b'\x00' * 100)  # 假数据
            return image_path
    
    @staticmethod
    def generate_test_frames(
        output_dir: Path,
        count: int = 10,
        width: int = 640,
        height: int = 480
    ) -> List[Path]:
        """生成测试帧图像"""
        frames = []
        for i in range(count):
            frame_path = WorkshopTestCase.create_sample_image(
                output_dir,
                filename=f"frame_{i:04d}",
                width=width,
                height=height
            )
            frames.append(frame_path)
        return frames
    
    @staticmethod
    def assert_true(condition: bool, message: str = "Assertion failed") -> None:
        """断言为真"""
        if not condition:
            raise AssertionError(message)
    
    @staticmethod
    def assert_equals(expected: Any, actual: Any, message: str = "") -> None:
        """断言相等"""
        if expected != actual:
            msg = f"Expected {expected!r}, got {actual!r}"
            if message:
                msg = f"{message}: {msg}"
            raise AssertionError(msg)
    
    @staticmethod
    def assert_not_none(value: Any, name: str = "value") -> None:
        """断言非空"""
        if value is None:
            raise AssertionError(f"{name} should not be None")
    
    @staticmethod
    def assert_in(needle: Any, haystack: Any, message: str = "") -> None:
        """断言包含"""
        if needle not in haystack:
            msg = f"{needle!r} not in {haystack!r}"
            if message:
                msg = f"{message}: {msg}"
            raise AssertionError(msg)
    
    @staticmethod
    def measure_time(func: Callable, *args, **kwargs) -> tuple:
        """
        测量函数执行时间
        
        Returns:
            (result, duration_seconds)
        """
        start = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start
        return result, duration
    
    @staticmethod
    def cleanup_temp(dir_path: Path) -> None:
        """清理临时目录"""
        if dir_path.exists():
            shutil.rmtree(dir_path)


class TestRunner:
    """
    测试运行器 - 参考 AgentOS 测试框架
    
    功能：
    - 自动发现和执行测试
    - 收集测试结果
    - 生成测试报告
    """
    
    def __init__(self):
        self._results: List[TestResult] = []
        self._passed = 0
        self._failed = 0
        self._total_duration = 0.0
    
    def run_test(self, test_name: str, test_func: Callable) -> TestResult:
        """运行单个测试"""
        start = time.time()
        
        try:
            test_func()
            duration = time.time() - start
            
            result = TestResult(
                test_name=test_name,
                passed=True,
                duration=duration
            )
            self._passed += 1
            
        except Exception as e:
            duration = time.time() - start
            
            result = TestResult(
                test_name=test_name,
                passed=False,
                duration=duration,
                error=str(e),
                details={'exception_type': type(e).__name__}
            )
            self._failed += 1
        
        self._results.append(result)
        self._total_duration += duration
        
        status = "✓ PASS" if result.passed else "✗ FAIL"
        print(f"[{status}] {result.test_name} ({duration:.3f}s)")
        
        if not result.passed:
            print(f"       Error: {result.error}")
        
        return result
    
    def run_test_suite(self, suite_name: str, tests: List[tuple]) -> Dict[str, Any]:
        """
        运行测试套件
        
        Args:
            suite_name: 套件名称
            tests: 测试列表 [(name, func), ...]
            
        Returns:
            测试报告字典
        """
        print(f"\n{'='*60}")
        print(f"Test Suite: {suite_name}")
        print(f"{'='*60}")
        
        for test_name, test_func in tests:
            self.run_test(test_name, test_func)
        
        report = self.generate_report()
        
        print(f"\n{'='*60}")
        print(f"Results: {report['summary']}")
        print(f"{'='*60}\n")
        
        return report
    
    def generate_report(self) -> Dict[str, Any]:
        """生成测试报告"""
        total = len(self._results)
        pass_rate = (self._passed / total * 100) if total > 0 else 0
        
        return {
            'total': total,
            'passed': self._passed,
            'failed': self._failed,
            'pass_rate': f"{pass_rate:.1f}%",
            'total_duration': f"{self._total_duration:.3f}s",
            'summary': (
                f"{self._passed}/{total} passed "
                f"({pass_rate:.1f}%) in {self._total_duration:.3f}s"
            ),
            'results': [
                {
                    'name': r.test_name,
                    'passed': r.passed,
                    'duration': r.duration,
                    'error': r.error
                }
                for r in self._results
            ]
        }
    
    def save_report_json(self, filepath: str) -> None:
        """保存 JSON 报告"""
        report = self.generate_report()
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"Test report saved to: {filepath}")


def run_all_tests():
    """运行所有测试套件"""
    runner = TestRunner()
    
    # 导入并运行各个测试模块
    try:
        from tests.unit.core.test_exceptions import test_exception_system
        from tests.unit.core.test_config_manager import test_config_manager
        from tests.unit.core.test_base_pipeline import test_base_pipeline
        from tests.unit.core.test_input_validator import test_input_validator
        from tests.unit.pipelines.test_ingest_v2 import test_ingest_pipeline
        from tests.unit.pipelines.test_quality_v2 import test_quality_pipeline
        
        runner.run_test_suite("Core Infrastructure", [
            ("Exception System", test_exception_system),
            ("Config Manager", test_config_manager),
            ("Base Pipeline", test_base_pipeline),
            ("Input Validator", test_input_validator),
        ])
        
        runner.run_test_suite("Pipeline Modules", [
            ("Ingest Pipeline v2", test_ingest_pipeline),
            ("Quality Pipeline v2", test_quality_pipeline),
        ])
        
    except ImportError as e:
        print(f"Warning: Could not import some test modules: {e}")
    
    return runner


if __name__ == "__main__":
    runner = run_all_tests()
    report = runner.generate_report()
    
    print("\n" + "="*60)
    print("FINAL TEST REPORT")
    print("="*60)
    print(f"Total Tests:  {report['total']}")
    print(f"Passed:       {report['passed']}")
    print(f"Failed:       {report['failed']}")
    print(f"Pass Rate:    {report['pass_rate']}")
    print(f"Duration:     {report['total_duration']}")
    print("="*60 + "\n")
    
    sys.exit(0 if report['failed'] == 0 else 1)
