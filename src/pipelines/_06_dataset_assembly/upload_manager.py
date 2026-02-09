"""
OSS上传管理器
负责将生成的数据集上传到阿里云OSS
"""

import os
import hashlib
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, BinaryIO
import time
from datetime import datetime
import json

try:
    import oss2
    from oss2.models import PartInfo
    OSS_AVAILABLE = True
except ImportError:
    OSS_AVAILABLE = False
    logging.warning("阿里云OSS SDK未安装，上传功能将受限")

from src.utils.file_utils import FileUtils

logger = logging.getLogger(__name__)


class OSSUploadError(Exception):
    """OSS上传错误"""
    pass


class OSSUploadManager:
    """
    阿里云OSS上传管理器
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化OSS上传管理器
        
        Args:
            config: OSS配置，包含endpoint, bucket, access_key_id, access_key_secret等
        """
        self.config = config or {}
        self.file_utils = FileUtils()
        
        # 从环境变量获取配置（如果未在config中提供）
        if not self.config.get("endpoint"):
            self.config["endpoint"] = os.getenv("OSS_ENDPOINT")
        if not self.config.get("bucket"):
            self.config["bucket"] = os.getenv("OSS_BUCKET")
        if not self.config.get("access_key_id"):
            self.config["access_key_id"] = os.getenv("OSS_ACCESS_KEY_ID")
        if not self.config.get("access_key_secret"):
            self.config["access_key_secret"] = os.getenv("OSS_ACCESS_KEY_SECRET")
        
        # 验证配置
        self._validate_config()
        
        # 初始化OSS连接
        self.auth = None
        self.bucket = None
        self._init_oss_connection()
        
        logger.info("OSS上传管理器初始化完成")
    
    def _validate_config(self):
        """验证OSS配置"""
        required_keys = ["endpoint", "bucket", "access_key_id", "access_key_secret"]
        
        missing_keys = []
        for key in required_keys:
            if not self.config.get(key):
                missing_keys.append(key)
        
        if missing_keys:
            error_msg = f"OSS配置缺失: {missing_keys}"
            logger.error(error_msg)
            
            # 如果环境变量也未设置，记录警告但允许继续（用于本地测试）
            if all(os.getenv(f"OSS_{key.upper()}") is None for key in missing_keys):
                logger.warning("OSS配置不完整，上传功能将不可用")
            else:
                raise OSSUploadError(error_msg)
    
    def _init_oss_connection(self):
        """初始化OSS连接"""
        if not OSS_AVAILABLE:
            logger.warning("阿里云OSS SDK未安装，跳过连接初始化")
            return
        
        try:
            endpoint = self.config.get("endpoint")
            bucket_name = self.config.get("bucket")
            access_key_id = self.config.get("access_key_id")
            access_key_secret = self.config.get("access_key_secret")
            
            if not all([endpoint, bucket_name, access_key_id, access_key_secret]):
                logger.warning("OSS配置不完整，跳过连接初始化")
                return
            
            # 创建认证对象
            self.auth = oss2.Auth(access_key_id, access_key_secret)
            
            # 创建Bucket对象
            self.bucket = oss2.Bucket(self.auth, endpoint, bucket_name)
            
            # 测试连接
            try:
                self.bucket.get_bucket_info()
                logger.info(f"OSS连接成功: {bucket_name} ({endpoint})")
            except Exception as e:
                logger.warning(f"OSS连接测试失败: {e}")
                self.bucket = None
            
        except Exception as e:
            logger.error(f"OSS连接初始化失败: {e}")
            self.auth = None
            self.bucket = None
    
    def is_available(self) -> bool:
        """
        检查OSS是否可用
        
        Returns:
            是否可用
        """
        return OSS_AVAILABLE and self.bucket is not None
    
    def upload_file(self, local_path: Path, oss_path: str, 
                   overwrite: bool = True, 
                   metadata: Dict[str, str] = None) -> Dict[str, Any]:
        """
        上传单个文件到OSS
        
        Args:
            local_path: 本地文件路径
            oss_path: OSS存储路径
            overwrite: 是否覆盖已存在文件
            metadata: 文件元数据
            
        Returns:
            上传结果
        """
        result = {
            "success": False,
            "local_path": str(local_path),
            "oss_path": oss_path,
            "file_size": 0,
            "md5": "",
            "upload_time": 0,
            "error": None
        }
        
        # 检查文件是否存在
        if not local_path.exists() or not local_path.is_file():
            error_msg = f"本地文件不存在: {local_path}"
            logger.error(error_msg)
            result["error"] = error_msg
            return result
        
        # 检查OSS是否可用
        if not self.is_available():
            error_msg = "OSS不可用，跳过上传"
            logger.warning(error_msg)
            result["error"] = error_msg
            return result
        
        file_size = local_path.stat().st_size
        result["file_size"] = file_size
        
        try:
            # 计算文件MD5
            md5_hash = self._calculate_file_md5(local_path)
            result["md5"] = md5_hash
            
            # 设置元数据
            headers = {}
            if metadata:
                for key, value in metadata.items():
                    headers[f"x-oss-meta-{key}"] = value
            
            # 添加文件信息到元数据
            headers["x-oss-meta-filename"] = local_path.name
            headers["x-oss-meta-md5"] = md5_hash
            headers["x-oss-meta-upload-time"] = datetime.now().isoformat()
            
            start_time = time.time()
            
            # 根据文件大小选择上传方式
            if file_size < 100 * 1024 * 1024:  # 小于100MB使用简单上传
                logger.info(f"简单上传: {local_path} -> {oss_path} ({self._format_size(file_size)})")
                
                with open(local_path, 'rb') as f:
                    self.bucket.put_object(oss_path, f, headers=headers)
                
            else:  # 大于100MB使用分片上传
                logger.info(f"分片上传: {local_path} -> {oss_path} ({self._format_size(file_size)})")
                
                # 初始化分片上传
                upload_id = self.bucket.init_multipart_upload(oss_path).upload_id
                
                # 计算分片数量
                part_size = 100 * 1024 * 1024  # 100MB每片
                part_count = (file_size + part_size - 1) // part_size
                
                parts = []
                
                with open(local_path, 'rb') as f:
                    for i in range(part_count):
                        # 读取分片数据
                        offset = i * part_size
                        bytes_to_read = min(part_size, file_size - offset)
                        data = f.read(bytes_to_read)
                        
                        # 上传分片
                        part_result = self.bucket.upload_part(
                            oss_path, upload_id, i + 1, data
                        )
                        parts.append(PartInfo(i + 1, part_result.etag))
                        
                        logger.info(f"上传分片 {i+1}/{part_count}: {self._format_size(bytes_to_read)}")
                
                # 完成分片上传
                self.bucket.complete_multipart_upload(oss_path, upload_id, parts)
            
            upload_time = time.time() - start_time
            result["upload_time"] = upload_time
            result["upload_speed"] = file_size / upload_time if upload_time > 0 else 0
            result["success"] = True
            
            logger.info(f"文件上传成功: {oss_path} ({self._format_size(file_size)}, {upload_time:.2f}s)")
            
        except Exception as e:
            error_msg = f"文件上传失败: {str(e)}"
            logger.error(error_msg, exc_info=True)
            result["error"] = error_msg
        
        return result
    
    def upload_directory(self, local_dir: Path, oss_prefix: str,
                        recursive: bool = True,
                        file_pattern: str = "*",
                        exclude_patterns: List[str] = None) -> Dict[str, Any]:
        """
        上传整个目录到OSS
        
        Args:
            local_dir: 本地目录路径
            oss_prefix: OSS路径前缀
            recursive: 是否递归上传子目录
            file_pattern: 文件匹配模式
            exclude_patterns: 排除模式列表
            
        Returns:
            上传结果汇总
        """
        result = {
            "success": False,
            "local_dir": str(local_dir),
            "oss_prefix": oss_prefix,
            "total_files": 0,
            "uploaded_files": 0,
            "failed_files": 0,
            "total_size": 0,
            "uploaded_size": 0,
            "details": [],
            "start_time": time.time(),
            "end_time": None
        }
        
        if not local_dir.exists() or not local_dir.is_dir():
            error_msg = f"本地目录不存在: {local_dir}"
            logger.error(error_msg)
            result["error"] = error_msg
            return result
        
        # 检查OSS是否可用
        if not self.is_available():
            error_msg = "OSS不可用，跳过上传"
            logger.warning(error_msg)
            result["error"] = error_msg
            return result
        
        # 查找文件
        if recursive:
            file_iter = local_dir.rglob(file_pattern)
        else:
            file_iter = local_dir.glob(file_pattern)
        
        files = [f for f in file_iter if f.is_file()]
        
        # 应用排除模式
        if exclude_patterns:
            import fnmatch
            filtered_files = []
            
            for file_path in files:
                # 检查是否匹配任何排除模式
                exclude = False
                relative_path = str(file_path.relative_to(local_dir))
                
                for pattern in exclude_patterns:
                    if fnmatch.fnmatch(relative_path, pattern):
                        exclude = True
                        break
                
                if not exclude:
                    filtered_files.append(file_path)
            
            files = filtered_files
        
        result["total_files"] = len(files)
        logger.info(f"开始上传目录: {local_dir} -> {oss_prefix} ({len(files)}个文件)")
        
        uploaded_count = 0
        failed_count = 0
        
        for i, file_path in enumerate(files):
            # 计算OSS路径
            relative_path = file_path.relative_to(local_dir)
            oss_path = f"{oss_prefix}/{relative_path}"
            
            # 确保OSS路径使用正斜杠
            oss_path = oss_path.replace("\\", "/")
            
            logger.info(f"上传文件 [{i+1}/{len(files)}]: {file_path.name}")
            
            # 上传文件
            file_result = self.upload_file(file_path, oss_path)
            
            # 记录结果
            result["details"].append(file_result)
            
            if file_result["success"]:
                uploaded_count += 1
                result["uploaded_size"] += file_result["file_size"]
            else:
                failed_count += 1
            
            result["total_size"] += file_result["file_size"]
            
            # 进度报告
            if (i + 1) % 10 == 0 or (i + 1) == len(files):
                progress = (i + 1) / len(files) * 100
                logger.info(f"上传进度: {i+1}/{len(files)} ({progress:.1f}%)")
        
        result["uploaded_files"] = uploaded_count
        result["failed_files"] = failed_count
        result["end_time"] = time.time()
        result["total_time"] = result["end_time"] - result["start_time"]
        
        if failed_count == 0:
            result["success"] = True
            logger.info(f"目录上传完成: {uploaded_count}个文件, {self._format_size(result['uploaded_size'])}, {result['total_time']:.2f}s")
        else:
            result["success"] = False
            logger.warning(f"目录上传部分失败: {uploaded_count}成功, {failed_count}失败")
        
        return result
    
    def upload_dataset(self, dataset_dir: Path, dataset_name: str,
                      version: str = "latest") -> Dict[str, Any]:
        """
        上传完整数据集到OSS
        
        Args:
            dataset_dir: 数据集目录
            dataset_name: 数据集名称
            version: 数据集版本
            
        Returns:
            上传结果
        """
        logger.info(f"开始上传数据集: {dataset_name} (版本: {version})")
        
        # 检查数据集目录结构
        required_subdirs = ["L1_2d_annotations", "L2_3d_geometry", "L3_physics_facts"]
        
        for subdir in required_subdirs:
            subdir_path = dataset_dir / subdir
            if not subdir_path.exists():
                logger.warning(f"数据集缺少子目录: {subdir}")
        
        # 数据集元数据
        metadata_file = dataset_dir / "dataset.json"
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
        else:
            # 生成基本元数据
            metadata = {
                "name": dataset_name,
                "version": version,
                "upload_time": datetime.now().isoformat(),
                "total_size": 0
            }
        
        # OSS路径前缀
        oss_prefix = f"spharx/datasets/{dataset_name}/{version}"
        
        # 上传整个目录
        upload_result = self.upload_directory(
            local_dir=dataset_dir,
            oss_prefix=oss_prefix,
            recursive=True,
            exclude_patterns=["*.tmp", "*.bak", "*.log"]
        )
        
        # 更新元数据
        if upload_result["success"]:
            metadata["oss_location"] = oss_prefix
            metadata["total_size"] = upload_result["total_size"]
            metadata["file_count"] = upload_result["uploaded_files"]
            metadata["upload_complete"] = True
            
            # 上传更新后的元数据
            metadata_json = json.dumps(metadata, indent=2)
            metadata_path = f"{oss_prefix}/dataset.json"
            
            self.bucket.put_object(metadata_path, metadata_json)
            
            logger.info(f"数据集元数据已上传: {metadata_path}")
        
        result = {
            "dataset_name": dataset_name,
            "version": version,
            "oss_prefix": oss_prefix,
            "upload_result": upload_result,
            "metadata": metadata
        }
        
        return result
    
    def list_datasets(self, prefix: str = "spharx/datasets/") -> List[Dict[str, Any]]:
        """
        列出OSS中的所有数据集
        
        Args:
            prefix: 路径前缀
            
        Returns:
            数据集列表
        """
        if not self.is_available():
            logger.warning("OSS不可用，无法列出数据集")
            return []
        
        datasets = []
        
        try:
            # 列出所有对象
            for obj in oss2.ObjectIterator(self.bucket, prefix=prefix, delimiter='/'):
                if obj.is_prefix():
                    # 这是一个目录（数据集）
                    dataset_path = obj.key.rstrip('/')
                    dataset_name = dataset_path.split('/')[-1]
                    
                    # 获取数据集信息
                    try:
                        # 尝试读取数据集元数据
                        metadata_path = f"{dataset_path}/latest/dataset.json"
                        metadata_obj = self.bucket.get_object(metadata_path)
                        metadata = json.loads(metadata_obj.read().decode('utf-8'))
                    except:
                        # 如果无法读取元数据，创建基本信息
                        metadata = {
                            "name": dataset_name,
                            "path": dataset_path,
                            "versions": []
                        }
                    
                    datasets.append(metadata)
            
        except Exception as e:
            logger.error(f"列出数据集失败: {e}")
        
        return datasets
    
    def download_file(self, oss_path: str, local_path: Path) -> Dict[str, Any]:
        """
        从OSS下载文件
        
        Args:
            oss_path: OSS路径
            local_path: 本地保存路径
            
        Returns:
            下载结果
        """
        result = {
            "success": False,
            "oss_path": oss_path,
            "local_path": str(local_path),
            "file_size": 0,
            "download_time": 0,
            "error": None
        }
        
        if not self.is_available():
            error_msg = "OSS不可用，无法下载文件"
            logger.warning(error_msg)
            result["error"] = error_msg
            return result
        
        try:
            # 确保本地目录存在
            self.file_utils.ensure_dir(local_path.parent)
            
            start_time = time.time()
            
            # 下载文件
            logger.info(f"下载文件: {oss_path} -> {local_path}")
            
            self.bucket.get_object_to_file(oss_path, str(local_path))
            
            download_time = time.time() - start_time
            file_size = local_path.stat().st_size
            
            result["file_size"] = file_size
            result["download_time"] = download_time
            result["download_speed"] = file_size / download_time if download_time > 0 else 0
            result["success"] = True
            
            logger.info(f"文件下载成功: {local_path} ({self._format_size(file_size)}, {download_time:.2f}s)")
            
        except Exception as e:
            error_msg = f"文件下载失败: {str(e)}"
            logger.error(error_msg, exc_info=True)
            result["error"] = error_msg
        
        return result
    
    def delete_file(self, oss_path: str) -> bool:
        """
        删除OSS上的文件
        
        Args:
            oss_path: OSS路径
            
        Returns:
            是否成功
        """
        if not self.is_available():
            logger.warning("OSS不可用，无法删除文件")
            return False
        
        try:
            self.bucket.delete_object(oss_path)
            logger.info(f"文件删除成功: {oss_path}")
            return True
        except Exception as e:
            logger.error(f"文件删除失败 {oss_path}: {e}")
            return False
    
    def _calculate_file_md5(self, file_path: Path, chunk_size: int = 8192) -> str:
        """计算文件MD5哈希值"""
        md5_hash = hashlib.md5()
        
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(chunk_size), b''):
                md5_hash.update(chunk)
        
        return md5_hash.hexdigest()
    
    def _format_size(self, size_bytes: int) -> str:
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"


class DatasetUploadManager:
    """
    数据集上传管理器
    高层接口，提供数据集上传的完整工作流
    """
    
    def __init__(self, oss_config: Dict[str, Any] = None):
        """
        初始化数据集上传管理器
        
        Args:
            oss_config: OSS配置
        """
        self.oss_manager = OSSUploadManager(oss_config)
        self.file_utils = FileUtils()
        
        # 上传配置
        self.config = {
            "max_retries": 3,
            "retry_delay": 5,  # 秒
            "chunk_size": 100 * 1024 * 1024,  # 100MB
            "concurrent_uploads": 3
        }
    
    def upload_dataset_pipeline(self, pipeline_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        上传流水线生成的数据集
        
        Args:
            pipeline_result: 流水线执行结果
            
        Returns:
            上传结果
        """
        logger.info("开始上传数据集流水线...")
        
        result = {
            "success": False,
            "pipeline_id": pipeline_result.get("scene_id", "unknown"),
            "upload_stages": {},
            "uploaded_files": [],
            "errors": []
        }
        
        try:
            # 1. 检查流水线输出
            if "outputs" not in pipeline_result:
                result["errors"].append("流水线没有输出结果")
                return result
            
            outputs = pipeline_result["outputs"]
            
            # 2. 上传2D标注数据
            if "2d_annotations" in outputs:
                logger.info("上传2D标注数据...")
                annotation_result = self._upload_2d_annotations(outputs["2d_annotations"])
                result["upload_stages"]["2d_annotations"] = annotation_result
            
            # 3. 上传3D几何数据
            if "3d_reconstruction" in outputs:
                logger.info("上传3D几何数据...")
                geometry_result = self._upload_3d_geometry(outputs["3d_reconstruction"])
                result["upload_stages"]["3d_geometry"] = geometry_result
            
            # 4. 上传物理事实数据
            if "physics_facts" in outputs:
                logger.info("上传物理事实数据...")
                physics_result = self._upload_physics_facts(outputs["physics_facts"])
                result["upload_stages"]["physics_facts"] = physics_result
            
            # 5. 上传数据集元数据
            logger.info("上传数据集元数据...")
            metadata_result = self._upload_dataset_metadata(pipeline_result)
            result["upload_stages"]["metadata"] = metadata_result
            
            # 检查所有阶段是否成功
            all_success = all(
                stage.get("success", False) 
                for stage in result["upload_stages"].values()
            )
            
            result["success"] = all_success
            
            if all_success:
                logger.info("数据集上传流水线完成")
            else:
                logger.warning("数据集上传流水线部分失败")
            
        except Exception as e:
            logger.error(f"数据集上传流水线异常: {e}", exc_info=True)
            result["errors"].append(f"上传异常: {str(e)}")
            result["success"] = False
        
        return result
    
    def _upload_2d_annotations(self, annotation_data: Dict[str, Any]) -> Dict[str, Any]:
        """上传2D标注数据"""
        result = {
            "success": False,
            "type": "2d_annotations",
            "files_uploaded": 0,
            "total_size": 0,
            "details": []
        }
        
        # 查找标注文件
        annotation_dir = Path(annotation_data.get("output_path", ""))
        if not annotation_dir.exists():
            result["error"] = f"标注目录不存在: {annotation_dir}"
            return result
        
        # 查找主要文件
        annotation_files = []
        
        # COCO格式标注文件
        coco_file = annotation_dir / "annotations.json"
        if coco_file.exists():
            annotation_files.append(coco_file)
        
        # 可视化图像
        vis_dir = annotation_dir / "visualizations"
        if vis_dir.exists():
            vis_files = list(vis_dir.glob("*.png")) + list(vis_dir.glob("*.jpg"))
            annotation_files.extend(vis_files[:10])  # 限制上传数量
        
        # 上传文件
        for file_path in annotation_files:
            relative_path = file_path.relative_to(annotation_dir)
            oss_path = f"annotations/2d/{relative_path}"
            
            upload_result = self.oss_manager.upload_file(file_path, oss_path)
            result["details"].append(upload_result)
            
            if upload_result["success"]:
                result["files_uploaded"] += 1
                result["total_size"] += upload_result["file_size"]
        
        result["success"] = result["files_uploaded"] > 0
        return result
    
    def _upload_3d_geometry(self, geometry_data: Dict[str, Any]) -> Dict[str, Any]:
        """上传3D几何数据"""
        result = {
            "success": False,
            "type": "3d_geometry",
            "files_uploaded": 0,
            "total_size": 0,
            "details": []
        }
        
        # 查找几何文件
        outputs = geometry_data.get("outputs", {})
        
        files_to_upload = []
        
        # 点云文件
        if "dense_point_cloud" in outputs:
            pc_path = Path(outputs["dense_point_cloud"])
            if pc_path.exists():
                files_to_upload.append((pc_path, "geometry/point_cloud.ply"))
        
        # 网格文件
        if "mesh" in outputs:
            mesh_path = Path(outputs["mesh"])
            if mesh_path.exists():
                files_to_upload.append((mesh_path, "geometry/mesh.ply"))
        
        # 稀疏模型
        workspace_dir = Path(geometry_data.get("workspace_dir", ""))
        if workspace_dir.exists():
            sparse_dir = workspace_dir / "sparse" / "0_text"
            if sparse_dir.exists():
                # 创建稀疏模型压缩包
                import zipfile
                import tempfile
                
                with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp_file:
                    with zipfile.ZipFile(tmp_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
                        for file_path in sparse_dir.rglob("*"):
                            if file_path.is_file():
                                arcname = file_path.relative_to(sparse_dir)
                                zipf.write(file_path, arcname)
                    
                    tmp_path = Path(tmp_file.name)
                    files_to_upload.append((tmp_path, "geometry/sparse_model.zip"))
                    
                    # 稍后删除临时文件
                    import atexit
                    atexit.register(lambda: tmp_path.unlink() if tmp_path.exists() else None)
        
        # 上传文件
        for local_path, oss_path in files_to_upload:
            upload_result = self.oss_manager.upload_file(local_path, oss_path)
            result["details"].append(upload_result)
            
            if upload_result["success"]:
                result["files_uploaded"] += 1
                result["total_size"] += upload_result["file_size"]
        
        result["success"] = result["files_uploaded"] > 0
        return result
    
    def _upload_physics_facts(self, physics_data: Dict[str, Any]) -> Dict[str, Any]:
        """上传物理事实数据"""
        result = {
            "success": False,
            "type": "physics_facts",
            "files_uploaded": 0,
            "total_size": 0,
            "details": []
        }
        
        # 查找物理事实文件
        if "facts_path" in physics_data:
            facts_path = Path(physics_data["facts_path"])
            if facts_path.exists():
                upload_result = self.oss_manager.upload_file(facts_path, "physics/facts.json")
                result["details"].append(upload_result)
                
                if upload_result["success"]:
                    result["files_uploaded"] += 1
                    result["total_size"] += upload_result["file_size"]
        
        # 查找其他相关文件
        outputs = physics_data.get("outputs", {})
        
        if "relationships" in outputs:
            # 将关系数据保存为JSON并上传
            import tempfile
            import json
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp_file:
                json.dump(outputs["relationships"], tmp_file, indent=2)
                tmp_path = Path(tmp_file.name)
                
                upload_result = self.oss_manager.upload_file(tmp_path, "physics/relationships.json")
                result["details"].append(upload_result)
                
                if upload_result["success"]:
                    result["files_uploaded"] += 1
                    result["total_size"] += upload_result["file_size"]
                
                # 清理临时文件
                tmp_path.unlink()
        
        result["success"] = result["files_uploaded"] > 0
        return result
    
    def _upload_dataset_metadata(self, pipeline_result: Dict[str, Any]) -> Dict[str, Any]:
        """上传数据集元数据"""
        result = {
            "success": False,
            "type": "metadata",
            "files_uploaded": 0,
            "total_size": 0
        }
        
        # 创建数据集元数据
        metadata = {
            "dataset_info": {
                "name": f"SPHARX_PHYSICS_{pipeline_result.get('scene_id', 'unknown')}",
                "version": "1.0.0",
                "created_at": datetime.now().isoformat(),
                "scene_id": pipeline_result.get("scene_id"),
                "pipeline_version": "1.0.0"
            },
            "data_components": {
                "has_2d_annotations": "2d_annotations" in pipeline_result.get("outputs", {}),
                "has_3d_geometry": "3d_reconstruction" in pipeline_result.get("outputs", {}),
                "has_physics_facts": "physics_facts" in pipeline_result.get("outputs", {})
            },
            "statistics": pipeline_result.get("statistics", {}),
            "upload_info": {
                "upload_time": datetime.now().isoformat(),
                "uploader": "SpharxWorkshop"
            }
        }
        
        # 保存并上传元数据
        import tempfile
        import json
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp_file:
            json.dump(metadata, tmp_file, indent=2)
            tmp_path = Path(tmp_file.name)
            
            upload_result = self.oss_manager.upload_file(tmp_path, "dataset.json")
            
            if upload_result["success"]:
                result["files_uploaded"] = 1
                result["total_size"] = upload_result["file_size"]
                result["success"] = True
            
            # 清理临时文件
            tmp_path.unlink()
        
        return result