# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
# 打包 (Pack) Pipeline V2 - 场景数据集打包与格式转换
# 使用 BasePipeline 基类重构，消除重复代码

import sys
import json
from typing import Any, Dict, Optional, List
from pathlib import Path

sys.path.insert(0, '/app/common/scripts')

from common.core import (
    BasePipeline,
    PipelineResult,
    ConfigManager,
    setup_logging,
    InputValidator,
    ErrorCode,
    PipelineError
)


class PackPipeline(BasePipeline):
    """
    数据打包 Pipeline
    
    功能：
    - 将处理后的场景数据整理成标准数据集格式
    - 生成 manifest.json 元数据文件
    - 支持多种输出格式（ROS bag, COCO, YOLO, Custom）
    - 数据完整性校验
    - 数据集压缩和归档
    
    配置项：
        - formats: 输出格式列表 (['ros', 'coco'])
        - include_raw: 是否包含原始数据 (False)
        - include_annotations: 是否包含标注 (True)
        - include_calibration: 是否包含标定参数 (True)
        - compression: 压缩格式 (none/zip/tar.gz)
        - dataset_name: 数据集名称
        - version: 数据集版本号
        - author: 作者信息
        - description: 数据集描述
    
    Example:
        >>> pipeline = PackPipeline()
        >>> result = pipeline.run(
        ...     input_data="/app/output/processed/scene_001",
        ...     output="/app/output/datasets",
        ...     formats=["coco", "yolo"]
        ... )
    """
    
    MODULE_NAME = "04_pack"
    VERSION = "2.0.0"
    
    SUPPORTED_FORMATS = ['ros', 'coco', 'yolo', 'custom', 'voc', 'kitti']
    
    def _initialize(self) -> None:
        """初始化打包资源"""
        self._logger.info("初始化 Pack Pipeline...")
        
        try:
            from algorithm.packer import pack_scene
            from common.schemas.dataset import DatasetSchema
            
            self._pack_scene = pack_scene
            self._schema_validator = DatasetSchema()
            
            self._logger.debug("打包算法模块加载成功")
            
        except ImportError as e:
            raise PipelineError(
                ErrorCode.MODULE_LOAD_FAILED,
                f"无法加载打包算法模块: {e}",
                cause=e
            )
    
    def _execute(self, input_data: Any = None, **kwargs) -> PipelineResult:
        """
        执行数据打包
        
        Args:
            input_data: 输入场景目录路径
            **kwargs:
                - formats: 输出格式列表（逗号分隔或列表）
                
        Returns:
            PipelineResult: 打包结果
        """
        validator = InputValidator()
        
        # 获取参数
        scene_dir = kwargs.get('input') or input_data or self.config.get('scene_dir')
        output_dir = kwargs.get('output') or self.config.get('output_dir')
        
        # 验证输入目录存在且可读
        path_validation = validator.validate_path(
            scene_dir,
            must_exist=True,
            should_be_dir=True,
            name='scene_dir'
        )
        if not path_validation.valid:
            return PipelineResult(
                success=False,
                error='\n'.join(path_validation.errors),
                error_code=ErrorCode.VALIDATION_FAILED
            )
        
        # 验证输出目录可写
        out_validation = validator.validate_directory_writable(output_dir, name='output_dir')
        if not out_validation.valid:
            return PipelineResult(
                success=False,
                error='\n'.join(out_validation.errors),
                error_code=ErrorCode.VALIDATION_FAILED
            )
        
        # 解析输出格式
        formats_input = kwargs.get('formats') or self.config.get(
            'formats', default=['ros', 'coco']
        )
        
        if isinstance(formats_input, str):
            formats = [f.strip() for f in formats_input.split(',')]
        elif isinstance(formats_input, list):
            formats = formats_input
        else:
            return PipelineResult(
                success=False,
                error=f"无效的格式参数类型: {type(formats_input)}",
                error_code=ErrorCode.INVALID_PARAMETER
            )
        
        # 验证格式是否支持
        invalid_formats = [f for f in formats if f.lower() not in self.SUPPORTED_FORMATS]
        if invalid_formats:
            return PipelineResult(
                success=False,
                error=f"不支持的输出格式: {invalid_formats}\n"
                      f"支持的格式: {self.SUPPORTED_FORMATS}",
                error_code=ErrorCode.NOT_SUPPORTED
            )
        
        # 获取数据集元信息
        dataset_meta = {
            'name': self.config.get('dataset_name', default=Path(scene_dir).name),
            'version': self.config.get('version', default='1.0.0'),
            'author': self.config.get('author', default='SPHARX Workshop'),
            'description': self.config.get('description', default=''),
            'source_directory': str(scene_dir),
            'formats': formats,
            'created_at': __import__('time').strftime('%Y-%m-%d %H:%M:%S'),
        }
        
        self._logger.info(
            f"开始数据打包: {scene_dir} → {output_dir}\n"
            f"  格式: {formats}\n"
            f"  数据集名称: {dataset_meta['name']} v{dataset_meta['version']}"
        )
        
        start_time = __import__('time').time()
        
        try:
            # 执行打包
            pack_success = self._pack_scene(
                scene_dir,
                output_dir,
                formats,
                config=self.config.to_dict(),
                metadata=dataset_meta,
                **kwargs
            )
            
            execution_time = __import__('time').time() - start_time
            self._increment_processed(1)
            
            if pack_success:
                # 收集打包结果统计
                pack_stats = self._collect_pack_statistics(output_dir, formats)
                
                # 验证生成的数据集完整性
                validation_result = self._validate_packed_dataset(output_dir)
                if not validation_result['valid']:
                    self._add_warning(
                        f"数据集验证发现问题: {validation_result['issues']}"
                    )
                
                metrics = {
                    'execution_time': execution_time,
                    'output_formats': formats,
                    **pack_stats,
                    'total_size_mb': self._calculate_total_size(output_dir),
                    'validation_passed': validation_result['valid']
                }
                
                result = PipelineResult(
                    success=True,
                    output={
                        'metadata': dataset_meta,
                        'statistics': pack_stats,
                        'output_directory': str(output_dir),
                        'formats': formats
                    },
                    metrics=metrics
                )
                
                self._logger.info(
                    f"✓ 数据打包完成\n"
                    f"  耗时: {execution_time:.2f}s\n"
                    f"  总大小: {metrics['total_size_mb']:.2f} MB\n"
                    f"  格式: {', '.join(formats)}"
                )
                
                return result
            else:
                return PipelineResult(
                    success=False,
                    error="打包算法返回失败",
                    error_code=ErrorCode.ALGORITHM_EXECUTION_FAILED
                )
                
        except Exception as e:
            self._logger.error(f"打包过程异常: {e}", exc_info=True)
            return PipelineResult(
                success=False,
                error=f"打包失败: {e}",
                error_code=ErrorCode.PIPELINE_EXECUTION_FAILED
            )
    
    def _cleanup(self) -> None:
        """清理资源"""
        self._logger.info("Pack Pipeline 资源已释放")
    
    @staticmethod
    def _collect_pack_statistics(output_dir: str, formats: List[str]) -> Dict[str, Any]:
        """收集打包结果统计"""
        output_path = Path(output_dir)
        stats = {}
        
        for fmt in formats:
            format_dir = output_path / fmt
            if format_dir.exists():
                file_count = len(list(format_dir.rglob('*')))
                total_size = sum(f.stat().st_size for f in format_dir.rglob('*') if f.is_file())
                
                stats[f'{fmt}_files'] = file_count
                stats[f'{fmt}_size_bytes'] = total_size
        
        # 统计总文件数
        all_files = list(output_path.rglob('*'))
        stats['total_files'] = len([f for f in all_files if f.is_file()])
        
        return stats
    
    @staticmethod
    def _validate_packed_dataset(output_dir: str) -> Dict[str, Any]:
        """验证打包后数据集的完整性"""
        output_path = Path(output_dir)
        issues = []
        
        # 检查 manifest.json 是否存在
        manifest = output_path / 'manifest.json'
        if not manifest.exists():
            issues.append("缺少 manifest.json 文件")
        else:
            try:
                with open(manifest, 'r', encoding='utf-8') as f:
                    manifest_data = json.load(f)
                    
                required_fields = ['name', 'version', 'source_directory']
                for field in required_fields:
                    if field not in manifest_data:
                        issues.append(f"manifest.json 缺少必需字段: {field}")
                        
            except json.JSONDecodeError as e:
                issues.append(f"manifest.json JSON 解析失败: {e}")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues
        }
    
    @staticmethod
    def _calculate_total_size(directory: str) -> float:
        """计算目录总大小（MB）"""
        dir_path = Path(directory)
        total_bytes = sum(
            f.stat().st_size 
            for f in dir_path.rglob('*') 
            if f.is_file()
        )
        return total_bytes / (1024 * 1024)  # Convert to MB


def main():
    """主入口函数 - 向后兼容"""
    import argparse
    
    parser = argparse.ArgumentParser(description="数据打包模块 (v2.0)")
    parser.add_argument("--input", required=True, help="输入场景目录")
    parser.add_argument("--output", required=True, help="输出数据集目录")
    parser.add_argument("--formats", help="格式列表，逗号分隔")
    parser.add_argument("--config", help="配置文件路径")
    args = parser.parse_args()
    
    # 设置日志
    logger = setup_logging("04_pack")
    logger.info(f"Pack Pipeline v{PackPipeline.VERSION} 启动")
    
    # 创建并运行 Pipeline
    pipeline = PackPipeline(config_path=args.config)
    
    run_kwargs = {'input': args.input, 'output': args.output}
    
    if args.formats:
        run_kwargs['formats'] = args.formats
    
    result = pipeline.run(**run_kwargs)
    
    if result.success:
        logger.info("✓ 数据打包成功")
        sys.exit(0)
    else:
        logger.error(f"✗ 数据打包失败: {result.error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
