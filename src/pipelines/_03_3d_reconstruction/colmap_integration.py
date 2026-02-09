"""
COLMAP 3D重建集成模块
将COLMAP工具集成到Python流水线中
"""

import os
import subprocess
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import shutil
import numpy as np

from src.utils.file_utils import FileUtils, PathResolver
from src.schemas.config import COLMAPConfig

logger = logging.getLogger(__name__)


class COLMAPIntegrationError(Exception):
    """COLMAP集成错误"""
    pass


class COLMAPProcessor:
    """
    COLMAP处理器
    封装COLMAP的完整3D重建流程
    """
    
    def __init__(self, config: COLMAPConfig = None):
        """
        初始化COLMAP处理器
        
        Args:
            config: COLMAP配置
        """
        self.config = config or COLMAPConfig()
        self.file_utils = FileUtils()
        self.path_resolver = PathResolver()
        
        # COLMAP二进制路径
        self.colmap_bin = self._find_colmap_binary()
        if not self.colmap_bin:
            raise COLMAPIntegrationError("COLMAP二进制文件未找到，请确保已正确安装")
        
        logger.info(f"COLMAP处理器初始化完成，二进制路径: {self.colmap_bin}")
    
    def _find_colmap_binary(self) -> Optional[Path]:
        """查找COLMAP二进制文件"""
        # 尝试多个可能的路径
        possible_paths = [
            "/usr/local/bin/colmap",
            "/usr/bin/colmap",
            "/opt/colmap/bin/colmap",
            "/home/spharx/.local/bin/colmap",
            shutil.which("colmap")
        ]
        
        for path_str in possible_paths:
            if path_str:
                path = Path(path_str)
                if path.exists() and os.access(path, os.X_OK):
                    logger.info(f"找到COLMAP二进制文件: {path}")
                    return path
        
        logger.warning("未找到COLMAP二进制文件")
        return None
    
    def run_command(self, command: List[str], cwd: Path = None, 
                   timeout: int = 3600) -> Tuple[bool, str]:
        """
        运行COLMAP命令
        
        Args:
            command: 命令列表
            cwd: 工作目录
            timeout: 超时时间（秒）
            
        Returns:
            (是否成功, 输出信息)
        """
        try:
            logger.info(f"运行命令: {' '.join(command)}")
            
            process = subprocess.run(
                command,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False
            )
            
            if process.returncode == 0:
                logger.info("命令执行成功")
                return True, process.stdout
            else:
                error_msg = f"命令执行失败 (code={process.returncode}): {process.stderr}"
                logger.error(error_msg)
                return False, error_msg
                
        except subprocess.TimeoutExpired:
            error_msg = f"命令执行超时 (timeout={timeout}s)"
            logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"命令执行异常: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def create_workspace(self, scene_id: str) -> Path:
        """
        创建COLMAP工作空间
        
        Args:
            scene_id: 场景ID
            
        Returns:
            工作空间路径
        """
        workspace_dir = Path(f"/home/SpharxWorkshop/workspace/processing/colmap/{scene_id}")
        workspace_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建子目录
        subdirs = ["sparse", "dense", "stereo", "database", "images"]
        for subdir in subdirs:
            (workspace_dir / subdir).mkdir(exist_ok=True)
        
        logger.info(f"创建COLMAP工作空间: {workspace_dir}")
        return workspace_dir
    
    def feature_extraction(self, workspace_dir: Path, image_dir: Path) -> bool:
        """
        特征提取阶段
        
        Args:
            workspace_dir: 工作空间目录
            image_dir: 图像目录
            
        Returns:
            是否成功
        """
        logger.info("开始特征提取...")
        
        # 复制图像到工作空间
        images_workspace_dir = workspace_dir / "images"
        self._copy_images_to_workspace(image_dir, images_workspace_dir)
        
        # 构建特征提取命令
        db_path = workspace_dir / "database" / "database.db"
        
        command = [
            str(self.colmap_bin),
            "feature_extractor",
            "--database_path", str(db_path),
            "--image_path", str(images_workspace_dir),
            "--ImageReader.camera_model", self.config.camera_model,
            "--ImageReader.single_camera", "1",
            "--SiftExtraction.max_image_size", str(self.config.max_image_size),
            "--SiftExtraction.max_num_features", str(self.config.max_num_features),
            "--SiftExtraction.edge_threshold", "10",
            "--SiftExtraction.peak_threshold", "0.00667"
        ]
        
        success, output = self.run_command(command, cwd=workspace_dir)
        
        if success:
            logger.info("特征提取完成")
            # 检查数据库文件
            if db_path.exists() and db_path.stat().st_size > 0:
                return True
            else:
                logger.error("数据库文件创建失败")
                return False
        else:
            logger.error("特征提取失败")
            return False
    
    def feature_matching(self, workspace_dir: Path, mode: str = "exhaustive") -> bool:
        """
        特征匹配阶段
        
        Args:
            workspace_dir: 工作空间目录
            mode: 匹配模式 ("exhaustive", "sequential", "vocab_tree")
            
        Returns:
            是否成功
        """
        logger.info(f"开始特征匹配 (模式: {mode})...")
        
        db_path = workspace_dir / "database" / "database.db"
        
        # 构建特征匹配命令
        if mode == "exhaustive":
            command = [
                str(self.colmap_bin),
                "exhaustive_matcher",
                "--database_path", str(db_path)
            ]
        elif mode == "sequential":
            command = [
                str(self.colmap_bin),
                "sequential_matcher",
                "--database_path", str(db_path),
                "--SequentialMatching.overlap", "20",
                "--SequentialMatching.quadratic_overlap", "1"
            ]
        elif mode == "vocab_tree":
            vocab_tree_path = self._get_vocab_tree_path()
            if not vocab_tree_path:
                logger.warning("词汇树文件未找到，使用穷举匹配")
                return self.feature_matching(workspace_dir, "exhaustive")
            
            command = [
                str(self.colmap_bin),
                "vocab_tree_matcher",
                "--database_path", str(db_path),
                "--VocabTreeMatching.vocab_tree_path", str(vocab_tree_path)
            ]
        else:
            logger.error(f"不支持的匹配模式: {mode}")
            return False
        
        success, output = self.run_command(command, cwd=workspace_dir)
        
        if success:
            logger.info("特征匹配完成")
            return True
        else:
            logger.error("特征匹配失败")
            return False
    
    def sparse_reconstruction(self, workspace_dir: Path) -> bool:
        """
        稀疏重建阶段
        
        Args:
            workspace_dir: 工作空间目录
            
        Returns:
            是否成功
        """
        logger.info("开始稀疏重建...")
        
        db_path = workspace_dir / "database" / "database.db"
        image_path = workspace_dir / "images"
        sparse_path = workspace_dir / "sparse"
        
        # 创建稀疏目录
        sparse_path.mkdir(exist_ok=True)
        
        # 增量重建
        command = [
            str(self.colmap_bin),
            "mapper",
            "--database_path", str(db_path),
            "--image_path", str(image_path),
            "--output_path", str(sparse_path),
            "--Mapper.ba_global_max_num_iterations", "30",
            "--Mapper.ba_global_max_refinements", "5",
            "--Mapper.ba_global_points_threshold", "1.0"
        ]
        
        success, output = self.run_command(command, cwd=workspace_dir, timeout=7200)
        
        if success:
            logger.info("稀疏重建完成")
            
            # 检查重建结果
            sparse_models = list(sparse_path.glob("*/cameras.bin"))
            if len(sparse_models) > 0:
                logger.info(f"找到 {len(sparse_models)} 个稀疏模型")
                
                # 选择最好的模型（通常是第一个）
                best_model = sparse_path / "0"
                if best_model.exists():
                    # 转换模型为文本格式以便查看
                    self._convert_model_to_text(best_model, sparse_path / "0_text")
                    return True
                else:
                    logger.error("最佳模型目录不存在")
                    return False
            else:
                logger.error("未找到稀疏重建模型")
                return False
        else:
            logger.error("稀疏重建失败")
            return False
    
    def dense_reconstruction(self, workspace_dir: Path) -> bool:
        """
        稠密重建阶段
        
        Args:
            workspace_dir: 工作空间目录
            
        Returns:
            是否成功
        """
        logger.info("开始稠密重建...")
        
        sparse_path = workspace_dir / "sparse" / "0"
        dense_path = workspace_dir / "dense"
        
        if not sparse_path.exists():
            logger.error("稀疏重建结果不存在")
            return False
        
        # 1. 图像去畸变
        logger.info("步骤1: 图像去畸变...")
        image_path = workspace_dir / "images"
        undistorted_path = dense_path / "images"
        
        command = [
            str(self.colmap_bin),
            "image_undistorter",
            "--image_path", str(image_path),
            "--input_path", str(sparse_path),
            "--output_path", str(dense_path),
            "--output_type", "COLMAP"
        ]
        
        success, output = self.run_command(command, cwd=workspace_dir)
        if not success:
            logger.error("图像去畸变失败")
            return False
        
        # 2. 立体匹配
        logger.info("步骤2: 立体匹配...")
        stereo_path = workspace_dir / "stereo"
        
        command = [
            str(self.colmap_bin),
            "patch_match_stereo",
            "--workspace_path", str(dense_path),
            "--workspace_format", "COLMAP",
            "--PatchMatchStereo.max_image_size", str(self.config.max_image_size),
            "--PatchMatchStereo.window_radius", "5",
            "--PatchMatchStereo.window_step", "1",
            "--PatchMatchStereo.num_samples", "15",
            "--PatchMatchStereo.num_iterations", "5"
        ]
        
        success, output = self.run_command(command, cwd=workspace_dir, timeout=10800)
        if not success:
            logger.error("立体匹配失败")
            return False
        
        # 3. 融合点云
        logger.info("步骤3: 点云融合...")
        fused_path = dense_path / "fused.ply"
        
        command = [
            str(self.colmap_bin),
            "stereo_fusion",
            "--workspace_path", str(dense_path),
            "--workspace_format", "COLMAP",
            "--input_type", "geometric",
            "--output_path", str(fused_path)
        ]
        
        success, output = self.run_command(command, cwd=workspace_dir, timeout=3600)
        if not success:
            logger.error("点云融合失败")
            return False
        
        logger.info("稠密重建完成")
        return True
    
    def mesh_reconstruction(self, workspace_dir: Path) -> bool:
        """
        网格重建阶段
        
        Args:
            workspace_dir: 工作空间目录
            
        Returns:
            是否成功
        """
        logger.info("开始网格重建...")
        
        dense_path = workspace_dir / "dense"
        fused_path = dense_path / "fused.ply"
        mesh_path = dense_path / "meshed.ply"
        
        if not fused_path.exists():
            logger.error("稠密点云不存在")
            return False
        
        # 泊松表面重建
        command = [
            str(self.colmap_bin),
            "poisson_mesher",
            "--input_path", str(fused_path),
            "--output_path", str(mesh_path),
            "--PoissonMeshing.trim", "10",
            "--PoissonMeshing.point_weight", "4"
        ]
        
        success, output = self.run_command(command, cwd=workspace_dir, timeout=1800)
        
        if success:
            logger.info("网格重建完成")
            return True
        else:
            logger.warning("网格重建失败，但点云已生成")
            return False
    
    def process_scene(self, scene_id: str, image_dir: Path) -> Dict[str, Any]:
        """
        处理完整场景的3D重建
        
        Args:
            scene_id: 场景ID
            image_dir: 图像目录
            
        Returns:
            重建结果
        """
        logger.info(f"开始3D重建场景: {scene_id}")
        
        result = {
            "scene_id": scene_id,
            "success": False,
            "stages": {},
            "outputs": {},
            "errors": []
        }
        
        try:
            # 1. 创建工作空间
            workspace_dir = self.create_workspace(scene_id)
            result["workspace_dir"] = str(workspace_dir)
            
            # 2. 特征提取
            result["stages"]["feature_extraction"] = {
                "status": "processing",
                "start_time": self._get_timestamp()
            }
            
            if not self.feature_extraction(workspace_dir, image_dir):
                result["stages"]["feature_extraction"]["status"] = "failed"
                result["errors"].append("特征提取失败")
                return result
            
            result["stages"]["feature_extraction"]["status"] = "completed"
            result["stages"]["feature_extraction"]["end_time"] = self._get_timestamp()
            
            # 3. 特征匹配
            result["stages"]["feature_matching"] = {
                "status": "processing",
                "start_time": self._get_timestamp()
            }
            
            if not self.feature_matching(workspace_dir, "exhaustive"):
                result["stages"]["feature_matching"]["status"] = "failed"
                result["errors"].append("特征匹配失败")
                return result
            
            result["stages"]["feature_matching"]["status"] = "completed"
            result["stages"]["feature_matching"]["end_time"] = self._get_timestamp()
            
            # 4. 稀疏重建
            result["stages"]["sparse_reconstruction"] = {
                "status": "processing",
                "start_time": self._get_timestamp()
            }
            
            if not self.sparse_reconstruction(workspace_dir):
                result["stages"]["sparse_reconstruction"]["status"] = "failed"
                result["errors"].append("稀疏重建失败")
                return result
            
            result["stages"]["sparse_reconstruction"]["status"] = "completed"
            result["stages"]["sparse_reconstruction"]["end_time"] = self._get_timestamp()
            
            # 5. 稠密重建（可选）
            if self.config.get("enable_dense_reconstruction", True):
                result["stages"]["dense_reconstruction"] = {
                    "status": "processing",
                    "start_time": self._get_timestamp()
                }
                
                if not self.dense_reconstruction(workspace_dir):
                    result["stages"]["dense_reconstruction"]["status"] = "partial"
                    result["errors"].append("稠密重建部分失败")
                else:
                    result["stages"]["dense_reconstruction"]["status"] = "completed"
                    result["outputs"]["dense_point_cloud"] = str(workspace_dir / "dense" / "fused.ply")
                
                result["stages"]["dense_reconstruction"]["end_time"] = self._get_timestamp()
            
            # 6. 网格重建（可选）
            if self.config.get("enable_mesh_reconstruction", True):
                result["stages"]["mesh_reconstruction"] = {
                    "status": "processing",
                    "start_time": self._get_timestamp()
                }
                
                if not self.mesh_reconstruction(workspace_dir):
                    result["stages"]["mesh_reconstruction"]["status"] = "partial"
                    result["errors"].append("网格重建部分失败")
                else:
                    result["stages"]["mesh_reconstruction"]["status"] = "completed"
                    result["outputs"]["mesh"] = str(workspace_dir / "dense" / "meshed.ply")
                
                result["stages"]["mesh_reconstruction"]["end_time"] = self._get_timestamp()
            
            # 7. 生成统计信息
            result = self._generate_statistics(result, workspace_dir)
            result["success"] = True
            
            logger.info(f"3D重建完成: {scene_id}")
            
        except Exception as e:
            logger.error(f"3D重建异常: {e}", exc_info=True)
            result["errors"].append(f"处理异常: {str(e)}")
            result["success"] = False
        
        return result
    
    def _copy_images_to_workspace(self, source_dir: Path, dest_dir: Path):
        """复制图像到工作空间"""
        logger.info(f"复制图像: {source_dir} -> {dest_dir}")
        
        # 清空目标目录
        if dest_dir.exists():
            shutil.rmtree(dest_dir)
        dest_dir.mkdir(parents=True)
        
        # 复制图像文件
        image_extensions = {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp'}
        image_files = [f for f in source_dir.iterdir() 
                      if f.is_file() and f.suffix.lower() in image_extensions]
        
        for img_file in image_files:
            dest_file = dest_dir / img_file.name
            shutil.copy2(img_file, dest_file)
        
        logger.info(f"复制了 {len(image_files)} 张图像")
    
    def _get_vocab_tree_path(self) -> Optional[Path]:
        """获取词汇树文件路径"""
        possible_paths = [
            "/usr/local/share/colmap/vocab_tree_flickr100K_words32K.bin",
            "/usr/share/colmap/vocab_tree_flickr100K_words32K.bin",
            "/opt/colmap/share/colmap/vocab_tree_flickr100K_words32K.bin",
            Path.home() / ".colmap" / "vocab_tree_flickr100K_words32K.bin"
        ]
        
        for path in possible_paths:
            if isinstance(path, str):
                path = Path(path)
            if path.exists():
                return path
        
        # 尝试下载词汇树
        vocab_tree_url = "https://demuc.de/colmap/vocab_tree_flickr100K_words32K.bin"
        download_path = Path.home() / ".colmap" / "vocab_tree_flickr100K_words32K.bin"
        
        if not download_path.parent.exists():
            download_path.parent.mkdir(parents=True)
        
        logger.info("尝试下载词汇树文件...")
        try:
            import requests
            response = requests.get(vocab_tree_url, stream=True)
            response.raise_for_status()
            
            with open(download_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"词汇树文件下载完成: {download_path}")
            return download_path
            
        except Exception as e:
            logger.warning(f"词汇树文件下载失败: {e}")
            return None
    
    def _convert_model_to_text(self, model_dir: Path, output_dir: Path):
        """转换模型为文本格式"""
        if not model_dir.exists():
            return
        
        command = [
            str(self.colmap_bin),
            "model_converter",
            "--input_path", str(model_dir),
            "--output_path", str(output_dir),
            "--output_type", "TXT"
        ]
        
        success, output = self.run_command(command)
        if success:
            logger.info(f"模型转换为文本格式: {output_dir}")
    
    def _generate_statistics(self, result: Dict[str, Any], workspace_dir: Path) -> Dict[str, Any]:
        """生成统计信息"""
        stats = {
            "total_images": 0,
            "sparse_points": 0,
            "dense_points": 0,
            "file_sizes": {}
        }
        
        # 统计图像数量
        images_dir = workspace_dir / "images"
        if images_dir.exists():
            image_files = list(images_dir.glob("*"))
            stats["total_images"] = len([f for f in image_files if f.is_file()])
        
        # 统计稀疏点数量
        sparse_dir = workspace_dir / "sparse" / "0"
        points3d_file = sparse_dir / "points3D.bin"
        if points3d_file.exists():
            try:
                # 读取points3D.bin文件获取点数
                # 这里简化处理，实际需要解析二进制文件
                command = [
                    str(self.colmap_bin),
                    "model_analyzer",
                    "--path", str(sparse_dir)
                ]
                
                success, output = self.run_command(command)
                if success and "Num points3D:" in output:
                    # 从输出中提取点数
                    for line in output.split('\n'):
                        if "Num points3D:" in line:
                            parts = line.split(":")
                            if len(parts) > 1:
                                stats["sparse_points"] = int(parts[1].strip())
                                break
            except:
                pass
        
        # 统计文件大小
        output_files = [
            ("sparse_model", sparse_dir),
            ("dense_point_cloud", workspace_dir / "dense" / "fused.ply"),
            ("mesh", workspace_dir / "dense" / "meshed.ply"),
            ("database", workspace_dir / "database" / "database.db")
        ]
        
        for name, file_path in output_files:
            if file_path.exists():
                if file_path.is_file():
                    stats["file_sizes"][name] = self._format_file_size(file_path.stat().st_size)
                elif file_path.is_dir():
                    total_size = sum(f.stat().st_size for f in file_path.rglob('*') if f.is_file())
                    stats["file_sizes"][name] = self._format_file_size(total_size)
        
        result["statistics"] = stats
        return result
    
    def _format_file_size(self, size_bytes: int) -> str:
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} TB"
    
    def _get_timestamp(self) -> str:
        """获取时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()


class COLMAPWrapper:
    """
    COLMAP包装器，提供简化的接口
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.processor = None
        
    def initialize(self):
        """初始化COLMAP处理器"""
        colmap_config = COLMAPConfig(**self.config)
        self.processor = COLMAPProcessor(colmap_config)
        return True
    
    def reconstruct(self, scene_id: str, image_dir: Path) -> Dict[str, Any]:
        """
        执行3D重建
        
        Args:
            scene_id: 场景ID
            image_dir: 图像目录
            
        Returns:
            重建结果
        """
        if not self.processor:
            self.initialize()
        
        return self.processor.process_scene(scene_id, image_dir)
    
    def export_results(self, scene_id: str, output_dir: Path) -> bool:
        """
        导出重建结果
        
        Args:
            scene_id: 场景ID
            output_dir: 输出目录
            
        Returns:
            是否成功
        """
        workspace_dir = Path(f"/home/SpharxWorkshop/workspace/processing/colmap/{scene_id}")
        
        if not workspace_dir.exists():
            logger.error(f"工作空间不存在: {workspace_dir}")
            return False
        
        # 创建输出目录
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 复制关键文件
        files_to_copy = [
            (workspace_dir / "dense" / "fused.ply", output_dir / "point_cloud.ply"),
            (workspace_dir / "dense" / "meshed.ply", output_dir / "mesh.ply"),
            (workspace_dir / "sparse" / "0_text", output_dir / "sparse_model"),
        ]
        
        copied_count = 0
        for src, dst in files_to_copy:
            if src.exists():
                if src.is_file():
                    shutil.copy2(src, dst)
                elif src.is_dir():
                    shutil.copytree(src, dst, dirs_exist_ok=True)
                copied_count += 1
        
        logger.info(f"导出了 {copied_count} 个文件到 {output_dir}")
        return copied_count > 0