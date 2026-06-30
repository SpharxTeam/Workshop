# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
# 增强 (Enhance) Pipeline V2 - 基于图像序列的目标检测与数据增强
# 使用 BasePipeline 基类重构，消除重复代码

import sys
from typing import Any, Dict, Optional, List

from core_workshop.core.abstractions import (
    BasePipeline,
    PipelineResult,
    ErrorCode,
    PipelineError,
)
from core_workshop.core.services.logging_service import setup_logging, get_logger
from core_workshop.pipelines._validation_helpers import (
    validate_path_exists_dir,
    validate_directory_writable,
    validate_range,
    collect_errors,
)


class EnhancePipeline(BasePipeline):
    """
    数据增强 Pipeline
    
    功能：
    - 基于 YOLO 等模型的目标检测
    - 图像语义分割（HDVS）
    - 目标检测结果标注和导出
    - 支持多种模型和版本切换
    
    配置项：
        - default_model: 默认模型名称 (yolo)
        - model_version: 模型版本 (current)
        - conf_threshold: 置信度阈值 (0.25)
        - iou_threshold: IoU 阈值 (0.45)
        - max_detections: 最大检测数量 (300)
        - output_format: 输出格式 (json/coco/yolo)
    
    Example:
        >>> pipeline = EnhancePipeline()
        >>> result = pipeline.run(
        ...     input_data="/app/data/scene_001",
        ...     output="/app/output/enhanced",
        ...     conf=0.3,
        ...     model="yolov8"
        ... )
    """
    
    MODULE_NAME = "02_enhance"
    VERSION = "2.0.0"
    
    def __init__(self, **kwargs):
        self._model_manager = None
        self._model_adapter = None
        self._detector = None
        super().__init__(**kwargs)
    
    def _initialize(self) -> None:
        """初始化增强处理资源"""
        self._logger.info("初始化 Enhance Pipeline...")
        
        try:
            # 导入算法模块
            from algorithm.yolo_detector import process_video
            from algorithm.hdvs_segmenter import HDVSSegmenter
            from algorithm.segmentation_auditor import SegmentationAuditor
            
            self._process_video = process_video
            self._segmenter = HDVSSegmenter(
                config=self.config.get('segmentation', default={})
            )
            self._auditor = SegmentationAuditor()
            
            # 初始化模型管理器
            model_config_path = self.config.get(
                'model_config_path',
                default='/app/common/configs/model_config.yaml'
            )
            
            from model.manager import ModelManager
            self._model_manager = ModelManager(model_config_path)
            
            # 加载默认模型
            default_model = self.config.get('default_model', default='yolo')
            model_version = self.config.get('model_version', default='current')
            
            self._model_adapter = self._model_manager.load_adapter(
                default_model,
                version=model_version
            )
            self._model_manager.switch_to(default_model)
            
            self._logger.info(
                f"✓ 模型加载成功: {default_model} (v{model_version})"
            )
            
        except ImportError as e:
            raise PipelineError(
                ErrorCode.MODULE_LOAD_FAILED,
                f"无法加载增强算法模块: {e}",
                cause=e
            )
        
        except Exception as e:
            raise PipelineError(
                ErrorCode.PIPELINE_INIT_FAILED,
                f"Enhance Pipeline 初始化失败: {e}",
                cause=e
            )
    
    def _execute(self, input_data: Any = None, **kwargs) -> PipelineResult:
        """
        执行数据增强处理
        
        Args:
            input_data: 场景目录路径
            **kwargs:
                - conf: 置信度阈值
                - model: 模型名称
                - version: 模型版本
                - output_format: 输出格式
                
        Returns:
            PipelineResult: 处理结果
        """
        # 获取参数
        scene_dir = kwargs.get('input') or input_data or self.config.get('scene_dir')
        output_dir = kwargs.get('output') or self.config.get('output_dir')
        
        # 验证输入输出路径
        errors = collect_errors(
            validate_path_exists_dir(scene_dir, 'scene_dir'),
            validate_directory_writable(output_dir, 'output_dir'),
        )
        if errors:
            return PipelineResult(
                success=False,
                error='\n'.join(errors),
                error_code=ErrorCode.VALIDATION_FAILED
            )
        
        # 构建算法参数
        conf_threshold = kwargs.get('conf') or self.config.get(
            'conf_threshold', default=0.25
        )
        
        # 验证置信度阈值范围
        conf_errors = collect_errors(
            validate_range(conf_threshold, 0.0, 1.0, 'conf_threshold'),
        )
        if conf_errors:
            return PipelineResult(
                success=False,
                error='\n'.join(conf_errors),
                error_code=ErrorCode.VALIDATION_FAILED
            )
        
        # 可选的模型切换
        if kwargs.get('model'):
            model_name = kwargs['model']
            version = kwargs.get('version', 'current')
            
            try:
                adapter = self._model_manager.load_adapter(model_name, version=version)
                self._model_manager.switch_to(model_name)
                self._model_adapter = adapter
                self._logger.info(f"切换到模型: {model_name} v{version}")
            except Exception as e:
                self._add_warning(f"模型切换失败，使用默认模型: {e}")
        
        self._logger.info(
            f"开始增强处理: {scene_dir} → {output_dir} "
            f"(conf={conf_threshold})"
        )
        
        start_time = __import__('time').time()
        
        try:
            # 执行目标检测
            detection_results = self._process_video(
                scene_dir,
                output_dir,
                self._model_adapter,
                config=self.config.to_dict(),
                conf_thres=conf_threshold
            )
            
            execution_time = __import__('time').time() - start_time
            self._increment_processed(1)
            
            # 统计检测指标
            total_detections = 0
            if isinstance(detection_results, dict):
                total_detections = detection_results.get('total_detections', 0)
                
                # 质量审计
                audit_result = self._auditor.audit(detection_results)
                if not audit_result.get('passed', True):
                    self._add_warning(
                        f"分割质量审计未通过: {audit_result.get('issues', [])}"
                    )
            
            metrics = {
                'execution_time': execution_time,
                'total_detections': total_detections,
                'confidence_threshold': conf_threshold,
                'model': self._model_manager.current_model if self._model_manager else 'unknown',
                'avg_detections_per_frame': total_detections / max(self._get_frame_count(scene_dir), 1)
            }
            
            result = PipelineResult(
                success=True,
                output=detection_results,
                metrics=metrics
            )
            
            self._logger.info(
                f"✓ 增强处理完成: {scene_dir} "
                f"(耗时: {execution_time:.2f}s, "
                f"检测目标: {total_detections})"
            )
            
            return result
            
        except Exception as e:
            self._logger.error(f"增强处理异常: {e}", exc_info=True)
            return PipelineResult(
                success=False,
                error=f"增强处理失败: {e}",
                error_code=ErrorCode.ALGORITHM_EXECUTION_FAILED
            )
    
    def _cleanup(self) -> None:
        """清理资源"""
        if hasattr(self, '_model_manager') and self._model_manager:
            try:
                self._model_manager.unload()
            except Exception as e:
                self._logger.warning(f"模型卸载时出错: {e}")
        
        if hasattr(self, '_segmenter'):
            del self._segmenter
        
        if hasattr(self, '_auditor'):
            del self._auditor
        
        self._logger.info("Enhance Pipeline 资源已释放")
    
    @staticmethod
    def _get_frame_count(scene_dir: str) -> int:
        """统计场景中的帧数"""
        from pathlib import Path
        scene_path = Path(scene_dir)
        
        count = 0
        for ext in ['*.jpg', '*.jpeg', '*.png', '*.webp']:
            count += len(list(scene_path.glob(f'rgb/{ext}')))
            count += len(list(scene_path.glob(ext)))
        
        return max(count, 1)


def main():
    """主入口函数 - 向后兼容"""
    import argparse
    
    parser = argparse.ArgumentParser(description="数据增强模块 (v2.0)")
    parser.add_argument("--input", required=True, help="场景目录")
    parser.add_argument("--output", required=True, help="输出目录")
    parser.add_argument("--conf", type=float, help="置信度阈值")
    parser.add_argument("--model", help="指定模型名称（如 yolo）")
    parser.add_argument("--version", default="current", help="模型版本")
    parser.add_argument("--config", help="配置文件路径")
    args = parser.parse_args()
    
    # 设置日志
    setup_logging(level="INFO")
    logger = get_logger("02_enhance")
    logger.info(f"Enhance Pipeline v{EnhancePipeline.VERSION} 启动")
    
    # 创建并运行 Pipeline
    pipeline = EnhancePipeline(config_path=args.config)
    
    # 构建 kwargs
    run_kwargs = {
        'input': args.input,
        'output': args.output
    }
    
    if args.conf is not None:
        run_kwargs['conf'] = args.conf
    if args.model:
        run_kwargs['model'] = args.model
    if args.version != "current":
        run_kwargs['version'] = args.version
    
    result = pipeline.run(**run_kwargs)
    
    if result.success:
        logger.info("✓ 增强处理成功")
        sys.exit(0)
    else:
        logger.error(f"✗ 增强处理失败: {result.error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
