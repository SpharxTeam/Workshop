# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
# 质量 (Quality) Pipeline - 重构版本
# 使用新的 BasePipeline 基类，消除重复代码

import sys
from typing import Any, Dict

sys.path.insert(0, '/app/common/scripts')

from common.core import (
    BasePipeline,
    PipelineResult,
    ConfigManager,
    setup_logging,
    get_logger,
    InputValidator,
    ErrorCode
)


class QualityPipeline(BasePipeline):
    """
    质量检测 Pipeline
    
    功能：
    - 图像模糊度检测
    - 曝光度检测
    - 丢帧统计
    - 生成质量报告 JSON
    
    配置项：
        - blur_threshold: 模糊阈值 (默认 100)
        - over_threshold: 过曝阈值
        - under_threshold: 欠曝阈值
        - expected_fps: 期望帧率
        - output_format: 报告输出格式 (json, yaml)
    """
    
    MODULE_NAME = "01_quality"
    VERSION = "2.0.0"
    
    def _initialize(self) -> None:
        """初始化资源"""
        self._logger.info("初始化 Quality Pipeline...")
        
        try:
            from algorithm.quality_analyzer import generate_quality_report
            from algorithm.blur_detector import BlurDetector
            
            self._generate_report = generate_quality_report
            self._blur_detector = BlurDetector(
                threshold=self.config.get('blur_threshold', default=100)
            )
            
            self._logger.debug("质量检测算法模块加载成功")
            
        except ImportError as e:
            raise ErrorCode.MODULE_LOAD_FAILED(f"无法加载质量检测模块: {e}")
    
    def _execute(self, input_data: Any = None, **kwargs) -> PipelineResult:
        """
        执行质量检测
        
        Args:
            input_data: 场景目录路径
            
        Returns:
            PipelineResult: 执行结果
        """
        validator = InputValidator()
        
        # 获取参数（优先使用 kwargs，其次配置，最后默认值）
        scene_dir = kwargs.get('input') or input_data or self.config.get('scene_dir')
        output_dir = kwargs.get('output') or self.config.get('output_dir')
        
        # 构建算法参数
        algo_params = {}
        
        if kwargs.get('blur_threshold') is not None:
            algo_params['blur_threshold'] = kwargs['blur_threshold']
        else:
            algo_params['blur_threshold'] = self.config.get(
                'blur_threshold', default=100
            )
        
        if kwargs.get('over_threshold') is not None:
            algo_params['over_threshold'] = kwargs['over_threshold']
        else:
            algo_params['over_threshold'] = self.config.get('over_threshold')
        
        if kwargs.get('under_threshold') is not None:
            algo_params['under_threshold'] = kwargs['under_threshold']
        else:
            algo_params['under_threshold'] = self.config.get('under_threshold')
        
        if kwargs.get('fps') is not None:
            algo_params['expected_fps'] = kwargs['fps']
        else:
            algo_params['expected_fps'] = self.config.get('expected_fps')
        
        # 验证输入
        validation = validator.validate_path(
            scene_dir,
            must_exist=True,
            should_be_dir=True,
            name='scene_dir'
        )
        
        if not validation.valid:
            return PipelineResult(
                success=False,
                error='\n'.join(validation.errors),
                error_code=ErrorCode.VALIDATION_FAILED
            )
        
        # 验证输出目录
        out_validation = validator.validate_directory_writable(output_dir, name='output_dir')
        if not out_validation.valid:
            return PipelineResult(
                success=False,
                error='\n'.join(out_validation.errors),
                error_code=ErrorCode.VALIDATION_FAILED
            )
        
        self._logger.info(f"开始质量检测: {scene_dir}")
        start_time = __import__('time').time()
        
        try:
            # 调用质量分析算法
            report = self._generate_report(
                scene_dir,
                output_dir,
                config=self.config.to_dict(),
                **algo_params
            )
            
            execution_time = __import__('time').time() - start_time
            self._increment_processed(1)
            
            # 统计报告中的关键指标
            if isinstance(report, dict):
                total_frames = report.get('total_frames', 0)
                blurry_frames = report.get('blurry_frames', 0)
                quality_score = report.get('quality_score', 0)
                
                metrics = {
                    'execution_time': execution_time,
                    'total_frames': total_frames,
                    'blurry_frames': blurry_frames,
                    'quality_score': quality_score,
                    'blurry_ratio': blurry_frames / max(total_frames, 1)
                }
                
                if metrics['blurry_ratio'] > 0.5:
                    self._add_warning(
                        f"模糊帧比例过高: {metrics['blurry_ratio']*100:.1f}%"
                    )
            else:
                metrics = {'execution_time': execution_time}
            
            result = PipelineResult(
                success=True,
                output=report,
                metrics=metrics
            )
            
            self._logger.info(
                f"质量检测完成: {scene_dir} "
                f"(耗时: {execution_time:.2f}s)"
            )
            
            return result
            
        except Exception as e:
            self._logger.error(f"质量检测异常: {e}", exc_info=True)
            return PipelineResult(
                success=False,
                error=f"质检失败: {e}",
                error_code=ErrorCode.ALGORITHM_EXECUTION_FAILED
            )
    
    def _cleanup(self) -> None:
        """清理资源"""
        if hasattr(self, '_blur_detector'):
            del self._blur_detector
        self._logger.info("Quality Pipeline 资源已释放")


def main():
    """主入口函数 - 向后兼容"""
    import argparse
    
    parser = argparse.ArgumentParser(description="质量检测模块 (v2.0)")
    parser.add_argument("--input", required=True, help="场景目录")
    parser.add_argument("--output", required=True, help="报告输出目录")
    parser.add_argument("--blur_threshold", type=int, help="模糊阈值")
    parser.add_argument("--over_threshold", type=int, help="过曝阈值")
    parser.add_argument("--under_threshold", type=int, help="欠曝阈值")
    parser.add_argument("--fps", type=int, help="期望帧率")
    parser.add_argument("--config", help="配置文件路径")
    args = parser.parse_args()
    
    # 设置日志
    logger = setup_logging("01_quality")
    logger.info(f"Quality Pipeline v{QualityPipeline.VERSION} 启动")
    
    # 创建并运行 Pipeline
    pipeline = QualityPipeline(config_path=args.config)
    
    # 构建 kwargs
    run_kwargs = {
        'input': args.input,
        'output': args.output
    }
    
    if args.blur_threshold is not None:
        run_kwargs['blur_threshold'] = args.blur_threshold
    if args.over_threshold is not None:
        run_kwargs['over_threshold'] = args.over_threshold
    if args.under_threshold is not None:
        run_kwargs['under_threshold'] = args.under_threshold
    if args.fps is not None:
        run_kwargs['fps'] = args.fps
    
    result = pipeline.run(**run_kwargs)
    
    if result.success:
        logger.info("✓ 质量检测成功")
        sys.exit(0)
    else:
        logger.error(f"✗ 质量检测失败: {result.error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
