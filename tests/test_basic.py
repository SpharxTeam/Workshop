"""
基本功能测试
测试项目的核心功能是否正常
"""

import sys
import os
import json
import tempfile
from pathlib import Path
import unittest
from unittest.mock import Mock, patch

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestProjectStructure(unittest.TestCase):
    """测试项目结构"""
    
    def test_directory_structure(self):
        """测试目录结构是否完整"""
        required_dirs = [
            "src",
            "src/schemas",
            "src/pipelines", 
            "src/utils",
            "configs",
            "configs/2d_annotation",
            "configs/3d_reconstruction",
            "configs/physics",
            "deploy",
            "scripts",
            "tests"
        ]
        
        for dir_path in required_dirs:
            full_path = project_root / dir_path
            self.assertTrue(full_path.exists(), f"目录不存在: {dir_path}")
            self.assertTrue(full_path.is_dir(), f"不是目录: {dir_path}")
    
    def test_required_files(self):
        """测试必要文件是否存在"""
        required_files = [
            "src/main.py",
            "src/__init__.py",
            "src/schemas/__init__.py",
            "src/schemas/config.py",
            "src/pipelines/__init__.py",
            "src/utils/__init__.py",
            "configs/logging.yaml",
            "docker-compose.yml",
            "Dockerfile",
            "requirements.txt",
            "README.md"
        ]
        
        for file_path in required_files:
            full_path = project_root / file_path
            self.assertTrue(full_path.exists(), f"文件不存在: {file_path}")
            self.assertTrue(full_path.is_file(), f"不是文件: {file_path}")


class TestSchemas(unittest.TestCase):
    """测试数据模型"""
    
    def test_config_schema(self):
        """测试配置模型"""
        from src.schemas.config import PipelineConfig, SAMConfig, COLMAPConfig
        
        # 测试SAMConfig
        sam_config = SAMConfig(
            model_type="vit_h",
            checkpoint_path="/models/sam_vit_h_4b8939.pth",
            device="cuda"
        )
        self.assertEqual(sam_config.model_type, "vit_h")
        self.assertEqual(sam_config.device, "cuda")
        
        # 测试COLMAPConfig
        colmap_config = COLMAPConfig(
            max_image_size=1600,
            max_num_features=8192
        )
        self.assertEqual(colmap_config.max_image_size, 1600)
        self.assertEqual(colmap_config.max_num_features, 8192)
        
        # 测试PipelineConfig
        pipeline_config = PipelineConfig(
            project_name="TestProject",
            project_stage="DEVELOPMENT"
        )
        self.assertEqual(pipeline_config.project_name, "TestProject")
        self.assertEqual(pipeline_config.project_stage, "DEVELOPMENT")
    
    def test_annotation_schema(self):
        """测试标注模型"""
        from src.schemas.annotation import AnnotationObject, BoundingBox2D
        
        # 测试BoundingBox2D
        bbox = BoundingBox2D(x=10, y=20, width=100, height=200)
        self.assertEqual(bbox.x, 10)
        self.assertEqual(bbox.y, 20)
        self.assertEqual(bbox.width, 100)
        self.assertEqual(bbox.height, 200)
        self.assertEqual(bbox.area, 20000)
        
        # 测试AnnotationObject
        annotation = AnnotationObject(
            object_id="obj_001",
            category="chair",
            bbox=[10, 20, 100, 200],
            confidence=0.95,
            attributes={"color": "red", "material": "wood"}
        )
        self.assertEqual(annotation.object_id, "obj_001")
        self.assertEqual(annotation.category, "chair")
        self.assertEqual(annotation.confidence, 0.95)
        self.assertEqual(annotation.attributes["color"], "red")


class TestUtils(unittest.TestCase):
    """测试工具函数"""
    
    def test_file_utils(self):
        """测试文件工具"""
        from src.utils.file_utils import FileUtils
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            # 测试目录创建
            test_dir = tmp_path / "test_subdir"
            FileUtils.ensure_dir(test_dir)
            self.assertTrue(test_dir.exists())
            self.assertTrue(test_dir.is_dir())
            
            # 测试文件写入和读取
            test_file = tmp_path / "test.json"
            test_data = {"key": "value", "number": 42}
            
            # 写入文件
            success = FileUtils.safe_write(test_data, test_file)
            self.assertTrue(success)
            self.assertTrue(test_file.exists())
            
            # 读取文件
            read_data = FileUtils.safe_read(test_file)
            self.assertEqual(read_data["key"], "value")
            self.assertEqual(read_data["number"], 42)
            
            # 测试文件哈希
            file_hash = FileUtils.get_file_hash(test_file)
            self.assertIsNotNone(file_hash)
            self.assertEqual(len(file_hash), 32)  # MD5哈希长度
    
    def test_image_utils(self):
        """测试图像工具"""
        from src.utils.image_utils import ImageLoader, ImageProcessor
        
        # 创建测试图像
        import numpy as np
        test_image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        
        # 测试图像处理
        resized = ImageProcessor.resize_image(test_image, max_size=50)
        self.assertEqual(resized.shape[0] <= 50, True)
        self.assertEqual(resized.shape[1] <= 50, True)
        
        # 测试模糊检测
        is_blurry, blur_score = ImageProcessor.detect_blur(test_image)
        self.assertIsInstance(is_blurry, bool)
        self.assertIsInstance(blur_score, float)


class TestPipelines(unittest.TestCase):
    """测试流水线模块"""
    
    @patch('subprocess.run')
    def test_colmap_integration(self, mock_subprocess):
        """测试COLMAP集成（模拟）"""
        from src.pipelines._03_3d_reconstruction.colmap_integration import COLMAPProcessor
        
        # 模拟subprocess.run返回
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.stdout = "COLMAP output"
        mock_subprocess.return_value = mock_process
        
        # 测试命令运行
        processor = COLMAPProcessor()
        
        # 由于我们模拟了subprocess，这里主要测试接口是否存在
        self.assertTrue(hasattr(processor, 'run_command'))
        self.assertTrue(hasattr(processor, 'feature_extraction'))
        self.assertTrue(hasattr(processor, 'sparse_reconstruction'))
    
    def test_pipeline_imports(self):
        """测试流水线模块导入"""
        # 测试主要流水线模块可以导入
        try:
            from src.pipelines import get_pipeline_module, list_pipelines
            from src.pipelines.pipeline_controller import PipelineController
            from src.pipelines.pipeline_manager import PipelineManager
            
            self.assertTrue(callable(get_pipeline_module))
            self.assertTrue(callable(list_pipelines))
            
            pipelines = list_pipelines()
            self.assertIsInstance(pipelines, dict)
            self.assertIn('preprocess', pipelines)
            self.assertIn('annotation_2d', pipelines)
            
        except ImportError as e:
            self.fail(f"流水线模块导入失败: {e}")


class TestMainProgram(unittest.TestCase):
    """测试主程序"""
    
    def test_main_import(self):
        """测试主程序导入"""
        try:
            from src.main import main
            self.assertTrue(callable(main))
        except ImportError as e:
            self.fail(f"主程序导入失败: {e}")
    
    def test_health_check(self):
        """测试健康检查"""
        from src.main import health_check
        import asyncio
        
        # 运行健康检查
        result = asyncio.run(health_check())
        self.assertIsInstance(result, bool)
        
        # 健康检查应该返回True（表示检查通过）或False
        # 实际结果取决于运行环境，这里只测试函数能否正常执行


class TestConfiguration(unittest.TestCase):
    """测试配置文件"""
    
    def test_config_files(self):
        """测试配置文件存在且可读"""
        config_files = [
            "configs/logging.yaml",
            "configs/pipeline_2d.yaml",
            "configs/2d_annotation/sam.yaml",
            "configs/3d_reconstruction/colmap.yaml",
            "configs/physics/blender.yaml"
        ]
        
        for config_file in config_files:
            full_path = project_root / config_file
            if full_path.exists():
                # 测试文件可读
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    self.assertGreater(len(content), 0, f"配置文件为空: {config_file}")
                except Exception as e:
                    self.fail(f"配置文件无法读取 {config_file}: {e}")
            else:
                # 如果文件不存在，记录警告但不失败（某些配置文件可能可选）
                print(f"警告: 配置文件不存在: {config_file}")


def run_all_tests():
    """运行所有测试"""
    # 创建测试套件
    loader = unittest.TestLoader()
    
    # 添加测试类
    test_classes = [
        TestProjectStructure,
        TestSchemas,
        TestUtils,
        TestPipelines,
        TestMainProgram,
        TestConfiguration
    ]
    
    suites = []
    for test_class in test_classes:
        suite = loader.loadTestsFromTestCase(test_class)
        suites.append(suite)
    
    # 创建总测试套件
    all_tests = unittest.TestSuite(suites)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(all_tests)
    
    # 返回测试结果
    return result.wasSuccessful()


if __name__ == "__main__":
    print("运行SpharxWorkshop项目测试...")
    print("=" * 60)
    
    success = run_all_tests()
    
    print("=" * 60)
    if success:
        print("✅ 所有测试通过！")
        sys.exit(0)
    else:
        print("❌ 部分测试失败")
        sys.exit(1)
        