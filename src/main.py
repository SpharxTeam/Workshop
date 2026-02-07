#!/usr/bin/env python3
"""
Spharx 生产线主控制器
用法：
  python -m src.main --scene-id scene_001               # 处理单个场景
  python -m src.main --scene-id scene_001 --2d-only     # 仅生成2D产品
  python -m src.main --config batch_job.yaml           # 批量处理
"""
import argparse
import logging
from src.utils.env import load_and_validate_env
from src.utils.log import setup_logging
from src.pipeline.engine import PipelineEngine

def main():
    # 1. 加载并验证环境变量
    env = load_and_validate_env()
    
    # 2. 解析命令行参数
    parser = argparse.ArgumentParser(description='Spharx 数据生产线')
    parser.add_argument('--scene-id', required=True, help='场景ID，如 scene_001')
    parser.add_argument('--2d-only', action='store_true', 
                       help='仅运行2D标注流水线，跳过3D重建')
    parser.add_argument('--skip-physics', action='store_true',
                       help='跳过物理事实生成')
    args = parser.parse_args()
    
    # 3. 配置日志
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info(f"开始处理场景: {args.scene_id}")
    
    # 4. 根据参数决定启用的产品阶段
    enabled_products = []
    if env.get('PRODUCE_2D_PRODUCT') == 'true':
        enabled_products.append('2d')
    if not args.2d_only and env.get('PRODUCE_3D_GEOMETRY_PRODUCT') == 'true':
        enabled_products.append('3d_geometry')
    if not args.skip_physics and env.get('PRODUCE_3D_PHYSICS_PRODUCT') == 'true':
        enabled_products.append('3d_physics')
    
    logger.info(f"启用产品线: {enabled_products}")
    
    # 5. 初始化并执行流水线
    engine = PipelineEngine(
        scene_id=args.scene_id,
        enabled_products=enabled_products,
        input_dir=env['INPUT_SCENES_DIR'],
        output_dir=env['OUTPUT_DATASETS_DIR'],
        workspace_dir=env['WORKSPACE_DIR']
    )
    
    success = engine.run()
    
    if success:
        logger.info(f"场景 {args.scene_id} 处理成功！")
        return 0
    else:
        logger.error(f"场景 {args.scene_id} 处理失败！")
        return 1

if __name__ == '__main__':
    exit(main())