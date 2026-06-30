# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
# 数据导入 (Ingest) Pipeline - 重构版本
# 使用新的 BasePipeline 基类，消除重复代码

import sys
from typing import Any, Dict, Optional

from core_workshop.core.abstractions import (
    BasePipeline,
    PipelineResult,
    ErrorCode,
    PipelineError,
    ValidationError,
)
from core_workshop.core.services.logging_service import setup_logging, get_logger
from core_workshop.pipelines._validation_helpers import (
    validate_file_readable,
    validate_directory_writable,
    collect_errors,
)


class IngestPipeline(BasePipeline):
    """
    数据导入 Pipeline
    
    功能：
    - 解析 RealSense bag 文件
    - 提取 RGB 和深度图像
    - 提取时间戳和相机参数
    - 数据格式转换和压缩
    
    配置项：
        - input: 输入 bag 文件路径
        - output: 输出目录
        - compression: 压缩格式 (jpeg, png, webp)
        - extract_depth: 是否提取深度图
        - privacy_mode: 隐私模式（是否脱敏）
    """
    
    MODULE_NAME = "00_ingest"
    VERSION = "2.0.0"
    
    def _initialize(self) -> None:
        """初始化资源"""
        self._logger.info("初始化 Ingest Pipeline...")
        
        # 延迟导入算法模块
        try:
            from algorithm.bag_parser import parse_bag
            from algorithm.image_compressor import ImageCompressor
            from algorithm.privacy_desensitizer import PrivacyDesensitizer
            
            self._parse_bag = parse_bag
            self._compressor = ImageCompressor(
                format=self.config.get('compression', default='jpeg')
            )
            
            if self.config.get('privacy_mode', default=False):
                self._desensitizer = PrivacyDesensitizer()
            else:
                self._desensitizer = None
                
            self._logger.debug("算法模块加载成功")
            
        except ImportError as e:
            raise PipelineError(
                ErrorCode.MODULE_LOAD_FAILED,
                f"无法加载算法模块: {e}",
                cause=e,
            )
    
    def _execute(self, input_data: Any = None, **kwargs) -> PipelineResult:
        """
        执行数据导入
        
        Args:
            input_data: 可以是文件路径或配置字典
            
        Returns:
            PipelineResult: 执行结果
        """
        # 获取输入输出路径
        input_path = kwargs.get('input') or self.config.get('input')
        output_dir = kwargs.get('output') or self.config.get('output')

        # 验证输入参数
        errors = collect_errors(
            validate_file_readable(input_path, 'input'),
            validate_directory_writable(output_dir, 'output'),
        )

        if errors:
            return PipelineResult(
                success=False,
                error='\n'.join(errors),
                error_code=ErrorCode.VALIDATION_FAILED
            )
        
        self._logger.info(f"开始解析 bag 文件: {input_path}")
        start_count = self._processed_count
        
        try:
            # 调用核心算法
            success = self._parse_bag(
                input_path,
                output_dir,
                config=self.config.to_dict(),
                **kwargs
            )
            
            if success:
                self._increment_processed(1)
                
                result = PipelineResult(
                    success=True,
                    output={
                        'input_file': input_path,
                        'output_dir': output_dir,
                        'frames_extracted': self._processed_count - start_count
                    },
                    metrics={
                        'input_size': self._get_file_size(input_path),
                        'output_size': self._get_dir_size(output_dir)
                    }
                )
                
                self._logger.info(
                    f"数据导入完成: {input_path} → {output_dir}"
                )
                return result
                
            else:
                return PipelineResult(
                    success=False,
                    error="bag 文件解析失败",
                    error_code=ErrorCode.ALGORITHM_EXECUTION_FAILED
                )
                
        except Exception as e:
            self._logger.error(f"数据导入异常: {e}", exc_info=True)
            return PipelineResult(
                success=False,
                error=str(e),
                error_code=ErrorCode.PIPELINE_EXECUTION_FAILED
            )
    
    def _cleanup(self) -> None:
        """清理资源"""
        if hasattr(self, '_compressor'):
            del self._compressor
        if hasattr(self, '_desensitizer'):
            del self._desensitizer
        self._logger.info("Ingest Pipeline 资源已释放")
    
    @staticmethod
    def _get_file_size(path: str) -> int:
        """获取文件大小"""
        from pathlib import Path
        p = Path(path)
        return p.stat().st_size if p.exists() else 0
    
    @staticmethod
    def _get_dir_size(path: str) -> int:
        """获取目录大小"""
        from pathlib import Path
        total = 0
        for p in Path(path).rglob('*'):
            if p.is_file():
                total += p.stat().st_size
        return total


def main():
    """主入口函数 - 向后兼容"""
    import argparse
    
    parser = argparse.ArgumentParser(description="解析 RealSense bag 文件 (v2.0)")
    parser.add_argument("--input", required=True, help="输入 bag 文件路径")
    parser.add_argument("--output", required=True, help="输出目录")
    parser.add_argument("--config", help="配置文件路径")
    args = parser.parse_args()
    
    # 设置日志
    setup_logging(level="INFO")
    logger = get_logger("00_ingest")
    logger.info(f"Ingest Pipeline v{IngestPipeline.VERSION} 启动")
    logger.info(f"Python 版本: {sys.version}")
    
    # 创建并运行 Pipeline
    pipeline = IngestPipeline(config_path=args.config)
    result = pipeline.run(input_data=None, input=args.input, output=args.output)
    
    if result.success:
        logger.info("✓ 数据导入成功")
        sys.exit(0)
    else:
        logger.error(f"✗ 数据导入失败: {result.error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
