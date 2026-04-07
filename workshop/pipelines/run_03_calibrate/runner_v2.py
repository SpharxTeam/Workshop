# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
# 标定 (Calibrate) Pipeline V2 - 基于棋盘格图像的相机内参标定
# 使用 BasePipeline 基类重构，消除重复代码

import sys
import os
from typing import Any, Dict, Optional, Tuple

sys.path.insert(0, '/app/common/scripts')

from common.core import (
    BasePipeline,
    PipelineResult,
    ConfigManager,
    setup_logging,
    InputValidator,
    ErrorCode,
    PipelineError,
    HardwareError
)


class CalibratePipeline(BasePipeline):
    """
    相机标定 Pipeline
    
    功能：
    - 基于棋盘格图案的内参标定
    - 外参标定（多相机系统）
    - 标定精度评估
    - 标定结果可视化
    - 标定参数导出（JSON/YAML）
    
    配置项：
        - chessboard_size: 棋盘格内角点尺寸 (9,6)
        - square_size: 方格实际尺寸（米） (0.025)
        - min_images: 最少标定图像数 (10)
        - show_detection: 是否显示角点检测结果 (False)
        - output_format: 输出格式 (json/yaml)
        - reprojection_error_threshold: 重投影误差阈值 (1.0)
    
    Example:
        >>> pipeline = CalibratePipeline()
        >>> result = pipeline.run(
        ...     input_data="/app/calibration/images",
        ...     output="/app/output/calibration",
        ...     chessboard=(11, 8),
        ...     square_size=0.03
        ... )
    """
    
    MODULE_NAME = "03_calibrate"
    VERSION = "2.0.0"
    
    def _initialize(self) -> None:
        """初始化标定资源"""
        self._logger.info("初始化 Calibrate Pipeline...")
        
        try:
            from algorithm.camera_calibrator import calibrate_camera
            self._calibrate_camera = calibrate_camera
            
            self._logger.debug("标定算法模块加载成功")
            
        except ImportError as e:
            raise PipelineError(
                ErrorCode.MODULE_LOAD_FAILED,
                f"无法加载标定算法模块: {e}",
                cause=e
            )
    
    def _execute(self, input_data: Any = None, **kwargs) -> PipelineResult:
        """
        执行相机标定
        
        Args:
            input_data: 标定图像目录路径
            **kwargs:
                - chessboard: 棋盘格内角点尺寸元组 (cols, rows)
                - square_size: 方格实际尺寸（米）
                
        Returns:
            PipelineResult: 标定结果
        """
        validator = InputValidator()
        
        # 获取参数
        calib_images_dir = kwargs.get('input') or input_data or self.config.get('calib_images_dir')
        output_dir = kwargs.get('output') or self.config.get('output_dir')
        
        # 验证输入目录存在且可读
        path_validation = validator.validate_path(
            calib_images_dir,
            must_exist=True,
            should_be_dir=True,
            name='calib_images_dir'
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
        
        # 解析棋盘格参数
        chessboard_str = kwargs.get('chessboard') or self.config.get(
            'chessboard_size', default='9,6'
        )
        
        if isinstance(chessboard_str, str):
            chessboard = tuple(map(int, chessboard_str.split(',')))
        elif isinstance(chessboard_str, (tuple, list)):
            chessboard = tuple(chessboard_str)
        else:
            return PipelineResult(
                success=False,
                error=f"无效的棋盘格尺寸格式: {type(chessboard_str)}",
                error_code=ErrorCode.INVALID_DATA_FORMAT
            )
        
        # 验证棋盘格尺寸合理性
        if len(chessboard) != 2:
            return PipelineResult(
                success=False,
                error="棋盘格尺寸必须是2个整数 (cols, rows)",
                error_code=ErrorCode.INVALID_PARAMETER
            )
        
        for dim, name in zip(chessboard, ['columns', 'rows']):
            range_check = validator.validate_range(
                dim,
                min_val=3,
                max_val=20,
                name=f'chessboard_{name}'
            )
            if not range_check.valid:
                return PipelineResult(
                    success=False,
                    error='\n'.join(range_check.errors),
                    error_code=ErrorCode.VALUE_OUT_OF_RANGE
                )
        
        # 解析方格尺寸
        square_size = kwargs.get('square_size') or self.config.get(
            'square_size', default=0.025
        )
        
        size_validation = validator.validate_range(
            square_size,
            min_val=0.001,
            max_val=1.0,
            name='square_size'
        )
        if not size_validation.valid:
            return PipelineResult(
                success=False,
                error='\n'.join(size_validation.errors),
                error_code=ErrorCode.VALUE_OUT_OF_RANGE
            )
        
        # 统计可用标定图像数量
        image_count = self._count_calibration_images(calib_images_dir)
        min_images = self.config.get('min_images', default=10)
        
        if image_count < min_images:
            self._add_warning(
                f"标定图像数量 ({image_count}) 少于推荐值 ({min_images})，"
                f"可能影响标定精度"
            )
        
        self._logger.info(
            f"开始相机标定: {calib_images_dir} → {output_dir}\n"
            f"  棋盘格尺寸: {chessboard[0]}x{chessboard[1]} 内角点\n"
            f"  方格尺寸: {square_size*1000:.1f}mm\n"
            f"  可用图像: {image_count}"
        )
        
        start_time = __import__('time').time()
        
        try:
            # 执行标定
            calibration_success = self._calibrate_camera(
                calib_images_dir,
                chessboard_size=chessboard,
                square_size=square_size,
                output_dir=output_dir,
                config=self.config.to_dict(),
                **kwargs
            )
            
            execution_time = __import__('time').time() - start_time
            self._increment_processed(1)
            
            if calibration_success:
                # 加载标定结果
                calibration_data = self._load_calibration_result(output_dir)
                
                reprojection_error = calibration_data.get(
                    'reprojection_error',
                    calibration_data.get('rms_error', 0.0)
                )
                
                # 检查标定质量
                error_threshold = self.config.get(
                    'reprojection_error_threshold',
                    default=1.0
                )
                
                if reprojection_error > error_threshold:
                    self._add_warning(
                        f"重投影误差 ({reprojection_error:.3f}px) "
                        f"超过阈值 ({error_threshold:.3f}px)，"
                        f"建议增加标定图像或检查棋盘格质量"
                    )
                
                metrics = {
                    'execution_time': execution_time,
                    'image_count': image_count,
                    'chessboard_size': chessboard,
                    'square_size_mm': square_size * 1000,
                    'reprojection_error_px': reprojection_error,
                    'calibration_quality': (
                        'excellent' if reprojection_error < 0.5 else
                        'good' if reprojection_error < 1.0 else
                        'acceptable' if reprojection_error < 2.0 else
                        'poor'
                    )
                }
                
                result = PipelineResult(
                    success=True,
                    output=calibration_data,
                    metrics=metrics
                )
                
                quality = metrics['calibration_quality']
                self._logger.info(
                    f"✓ 相机标定完成\n"
                    f"  耗时: {execution_time:.2f}s\n"
                    f"  重投影误差: {reprojection_error:.4f}px\n"
                    f"  标定质量: {quality}"
                )
                
                return result
            else:
                return PipelineResult(
                    success=False,
                    error="相机标定算法返回失败",
                    error_code=ErrorCode.ALGORITHM_EXECUTION_FAILED
                )
                
        except Exception as e:
            self._logger.error(f"标定过程异常: {e}", exc_info=True)
            return PipelineResult(
                success=False,
                error=f"标定失败: {e}",
                error_code=ErrorCode.HARDWARE_INIT_FAILED
            )
    
    def _cleanup(self) -> None:
        """清理资源"""
        self._logger.info("Calibrate Pipeline 资源已释放")
    
    @staticmethod
    def _count_calibration_images(directory: str) -> int:
        """统计标定图像数量"""
        from pathlib import Path
        dir_path = Path(directory)
        
        image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.bmp', '*.tiff']
        count = 0
        
        for ext in image_extensions:
            count += len(list(dir_path.glob(ext)))
            # 也检查子目录
            count += len(list(dir_path.rglob(ext)))
        
        return count
    
    @staticmethod
    def _load_calibration_result(output_dir: str) -> Dict[str, Any]:
        """加载标定结果"""
        import json
        from pathlib import Path
        
        output_path = Path(output_dir)
        
        # 尝试加载 JSON 结果
        json_files = [
            output_path / 'calibration_result.json',
            output_path / 'intrinsics.json',
            output_path / 'camera_matrix.json'
        ]
        
        for json_file in json_files:
            if json_file.exists():
                with open(json_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        
        # 如果没有找到 JSON，返回基本信息
        return {
            'status': 'completed',
            'output_directory': str(output_path)
        }


def main():
    """主入口函数 - 向后兼容"""
    import argparse
    
    parser = argparse.ArgumentParser(description="相机标定模块 (v2.0)")
    parser.add_argument("--input", required=True, help="标定图像目录")
    parser.add_argument("--output", required=True, help="输出目录")
    parser.add_argument("--chessboard", help="棋盘格内角点，如 9,6")
    parser.add_argument("--square_size", type=float, help="方格尺寸（米）")
    parser.add_argument("--config", help="配置文件路径")
    args = parser.parse_args()
    
    # 设置日志
    logger = setup_logging("03_calibrate")
    logger.info(f"Calibrate Pipeline v{CalibratePipeline.VERSION} 启动")
    
    # 创建并运行 Pipeline
    pipeline = CalibratePipeline(config_path=args.config)
    
    # 构建 kwargs
    run_kwargs = {'input': args.input, 'output': args.output}
    
    if args.chessboard:
        cb_parts = [int(x.strip()) for x in args.chessboard.split(',')]
        run_kwargs['chessboard'] = tuple(cb_parts)
    
    if args.square_size is not None:
        run_kwargs['square_size'] = args.square_size
    
    result = pipeline.run(**run_kwargs)
    
    if result.success:
        logger.info("✓ 相机标定成功")
        sys.exit(0)
    else:
        logger.error(f"✗ 相机标定失败: {result.error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
