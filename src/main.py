#!/usr/bin/env python3
"""
SPHARX TOOLCHAIN 主入口程序
遵循"先2D后3D、数据分离、配置驱动、快速复制"原则
"""

import argparse
import sys
import os
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from utils.log import setup_logging
from utils.env import load_environment
from pipeline.engine import PipelineEngine
from products.validator import ProductValidator


def main():
    """主程序入口"""
    parser = argparse.ArgumentParser(
        description="SPHARX数据处理流水线",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 运行完整流水线
  python main.py --config config/pipeline_default.yaml
  
  # 运行指定阶段
  python main.py --stage 01_2d_annotation
  
  # 验证产品数据
  python main.py --validate-product /path/to/product
  
  # 显示流水线信息
  python main.py --list-stages
        """
    )
    
    # 运行模式选择
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument(
        '--config', '-c',
        help='使用配置文件运行完整流水线'
    )
    mode_group.add_argument(
        '--stage', '-s',
        help='运行指定阶段'
    )
    mode_group.add_argument(
        '--validate-product', '-v',
        help='验证产品数据完整性'
    )
    mode_group.add_argument(
        '--list-stages', '-l',
        action='store_true',
        help='列出所有可用阶段'
    )
    
    # 通用选项
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='预演模式：只显示将要执行的操作'
    )
    parser.add_argument(
        '--verbose', '-V',
        action='store_true',
        help='详细输出模式'
    )
    parser.add_argument(
        '--skip-validation',
        action='store_true',
        help='跳过输入数据验证'
    )
    
    args = parser.parse_args()
    
    # 初始化环境
    try:
        load_environment()
        logger = setup_logging(level='DEBUG' if args.verbose else 'INFO')
        logger.info("🚀 SPHARX Toolchain 启动")
    except Exception as e:
        print(f"❌ 环境初始化失败: {e}")
        sys.exit(1)
    
    try:
        if args.list_stages:
            # 显示阶段列表
            _list_available_stages(logger)
            
        elif args.validate_product:
            # 验证产品
            _validate_product(args.validate_product, logger)
            
        elif args.stage:
            # 运行单个阶段
            _run_single_stage(args.stage, args.dry_run, args.skip_validation, logger)
            
        elif args.config:
            # 运行完整流水线
            _run_full_pipeline(args.config, args.dry_run, args.skip_validation, logger)
            
    except KeyboardInterrupt:
        logger.info("🛑 用户中断操作")
        sys.exit(130)
    except Exception as e:
        logger.error(f"❌ 执行失败: {e}", exc_info=True)
        sys.exit(1)


def _list_available_stages(logger):
    """列出所有可用阶段"""
    from pipeline.stages import get_all_stages
    
    logger.info("📋 可用处理阶段:")
    stages = get_all_stages()
    
    for stage_info in stages:
        print(f"  {stage_info['id']:>2} - {stage_info['name']}")
        print(f"       {stage_info['description']}")
        if stage_info['dependencies']:
            deps = ', '.join(stage_info['dependencies'])
            print(f"       依赖: {deps}")
        print()


def _validate_product(product_path: str, logger):
    """验证产品数据"""
    validator = ProductValidator()
    result = validator.validate(Path(product_path))
    
    if result.is_valid:
        logger.info(f"✅ 产品验证通过: {product_path}")
        print(f"产品类型: {result.product_type}")
        print(f"版本: {result.version}")
        print(f"文件数量: {result.file_count}")
    else:
        logger.error(f"❌ 产品验证失败: {product_path}")
        for error in result.errors:
            print(f"  - {error}")
        sys.exit(1)


def _run_single_stage(stage_name: str, dry_run: bool, skip_validation: bool, logger):
    """运行单个阶段"""
    logger.info(f"⚙️  准备运行阶段: {stage_name}")
    
    if dry_run:
        logger.info("🎭 预演模式 - 显示将要执行的操作")
        # TODO: 实现预演逻辑
        return
    
    engine = PipelineEngine()
    try:
        engine.run_stage(stage_name, skip_validation=skip_validation)
        logger.info(f"✅ 阶段 {stage_name} 执行完成")
    except Exception as e:
        logger.error(f"❌ 阶段 {stage_name} 执行失败: {e}")
        raise


def _run_full_pipeline(config_path: str, dry_run: bool, skip_validation: bool, logger):
    """运行完整流水线"""
    logger.info(f"⚙️  准备运行完整流水线: {config_path}")
    
    if dry_run:
        logger.info("🎭 预演模式 - 显示将要执行的操作")
        # TODO: 实现预演逻辑
        return
    
    engine = PipelineEngine()
    try:
        engine.run_pipeline(config_path, skip_validation=skip_validation)
        logger.info("✅ 完整流水线执行完成")
    except Exception as e:
        logger.error(f"❌ 流水线执行失败: {e}")
        raise


if __name__ == "__main__":
    main()