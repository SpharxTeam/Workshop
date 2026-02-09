#!/usr/bin/env python3
"""
SpharxWorkshop 主控制程序
空间智能数据生产线入口点

命令层次结构：
1. pipeline     - 直接运行流水线（传统方式）
2. manager      - 通过任务管理器运行（推荐方式）
3. health-check - 系统健康检查
4. server       - 启动API服务器（开发中）
"""

import os
import sys
import asyncio
import logging
import json
import argparse
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.logging import setup_logging
from src.schemas.config import PipelineConfig

logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv(project_root / ".env")


async def run_pipeline(pipeline_type: str, scene_id: str, config_path: Optional[str] = None):
    """
    运行指定流水线（传统方式）
    
    Args:
        pipeline_type: 流水线类型 (2d, 3d, physics, full)
        scene_id: 场景ID
        config_path: 配置文件路径
    """
    try:
        # 初始化配置
        config = PipelineConfig.from_yaml(config_path) if config_path else PipelineConfig()
        
        # 根据流水线类型导入相应的控制器
        if pipeline_type == "2d":
            from src.pipelines.pipeline_controller import PipelineController
            controller = PipelineController(config)
            logger.info(f"启动2D标注流水线，场景: {scene_id}")
            result = await controller.run_2d_pipeline(scene_id)
            
        elif pipeline_type == "3d":
            from src.pipelines.pipeline_controller import PipelineController
            controller = PipelineController(config)
            logger.info(f"启动3D重建流水线，场景: {scene_id}")
            result = await controller.run_3d_pipeline(scene_id)
            
        elif pipeline_type == "physics":
            from src.pipelines.pipeline_controller import PipelineController
            controller = PipelineController(config)
            logger.info(f"启动物理事实生成流水线，场景: {scene_id}")
            result = await controller.run_physics_pipeline(scene_id)
            
        elif pipeline_type == "full":
            from src.pipelines.pipeline_controller import PipelineController
            controller = PipelineController(config)
            logger.info(f"启动完整流水线，场景: {scene_id}")
            result = await controller.run_full_pipeline(scene_id)
            
        else:
            logger.error(f"未知流水线类型: {pipeline_type}")
            print(f"❌ 错误: 未知流水线类型: {pipeline_type}")
            return False
        
        logger.info(f"流水线执行完成: {pipeline_type} - {scene_id}")
        
        # 打印结果摘要
        print(f"\n✅ 流水线执行成功!")
        print(f"   场景: {scene_id}")
        print(f"   类型: {pipeline_type}")
        
        if isinstance(result, dict) and 'output_path' in result:
            print(f"   输出路径: {result['output_path']}")
        
        return True
        
    except ImportError as e:
        logger.error(f"模块导入失败: {e}", exc_info=True)
        print(f"❌ 模块导入失败: {e}")
        print("请确保所有依赖已安装: pip install -r requirements.txt")
        return False
        
    except Exception as e:
        logger.error(f"流水线执行失败: {e}", exc_info=True)
        print(f"❌ 流水线执行失败: {e}")
        return False


async def run_manager_command(args):
    """
    运行管理器命令（推荐方式）
    
    Args:
        args: 命令行参数
    """
    try:
        from src.pipelines import get_pipeline_manager
        
        # 获取管理器单例
        manager = get_pipeline_manager()
        await manager.initialize()
        
        if args.manager_command == "submit":
            # 提交新任务
            task_id = await manager.submit_pipeline_task(
                scene_id=args.scene,
                pipeline_type=args.type,
                priority=args.priority,
                config_overrides=args.config_overrides
            )
            
            print(f"✅ 任务提交成功!")
            print(f"   任务ID: {task_id}")
            print(f"   场景: {args.scene}")
            print(f"   类型: {args.type}")
            print(f"   优先级: {args.priority}")
            print(f"\n查看状态: python src/main.py manager status --task-id {task_id}")
            
        elif args.manager_command == "status":
            # 查看任务状态
            if args.task_id:
                status = await manager.get_task_status(args.task_id)
                if status:
                    print(json.dumps(status, indent=2, default=str))
                else:
                    print(f"❌ 任务不存在: {args.task_id}")
            elif args.list:
                tasks = await manager.get_task_list(
                    status_filter=args.filter,
                    limit=args.limit
                )
                
                if not tasks:
                    print("📭 没有任务")
                    return
                
                print(f"📋 任务列表 (共{len(tasks)}个):")
                print("-" * 80)
                print(f"{'ID':<25} {'场景':<15} {'类型':<8} {'状态':<12} {'进度':<8} {'优先级':<8}")
                print("-" * 80)
                
                for task in tasks:
                    progress_str = f"{task['progress']*100:.1f}%" if task['progress'] > 0 else "待开始"
                    print(f"{task['id']:<25} {task['scene_id']:<15} {task['pipeline_type']:<8} "
                          f"{task['status']:<12} {progress_str:<8} {task['priority']:<8}")
                
                print("-" * 80)
                
        elif args.manager_command == "dashboard":
            # 查看监控仪表板
            dashboard = await manager.get_monitor_dashboard()
            
            print("📊 SpharxWorkshop 监控仪表板")
            print("=" * 60)
            print(f"系统状态: {dashboard.get('system_status', 'unknown')}")
            print(f"时间戳: {dashboard.get('timestamp', 'unknown')}")
            print(f"\n📈 任务统计:")
            print(f"   总任务数: {dashboard.get('total_tasks', 0)}")
            print(f"   已完成: {dashboard.get('completed_tasks', 0)}")
            print(f"   已失败: {dashboard.get('failed_tasks', 0)}")
            print(f"   平均处理时间: {dashboard.get('avg_processing_time', 0):.2f}秒")
            
            current_tasks = dashboard.get('current_tasks', {})
            if current_tasks:
                print(f"\n🔄 当前运行任务 ({len(current_tasks)}个):")
                for task_id, task_info in list(current_tasks.items())[:5]:  # 只显示前5个
                    print(f"   - {task_id}: {task_info.get('scene_id')} "
                          f"[{task_info.get('status')}] "
                          f"进度: {task_info.get('progress', 0)*100:.1f}%")
                
                if len(current_tasks) > 5:
                    print(f"   ... 还有 {len(current_tasks)-5} 个任务")
            
        elif args.manager_command == "cancel":
            # 取消任务（TODO: 需要实现取消功能）
            print("⚠️  任务取消功能正在开发中...")
            # await manager.cancel_task(args.task_id)
            
        else:
            print(f"❌ 未知的管理器命令: {args.manager_command}")
            
    except ImportError as e:
        logger.error(f"管理器导入失败: {e}", exc_info=True)
        print(f"❌ 管理器模块导入失败: {e}")
        print("请确保 pipeline_manager.py 已正确创建")
        
    except Exception as e:
        logger.error(f"管理器命令执行失败: {e}", exc_info=True)
        print(f"❌ 管理器命令执行失败: {e}")


async def health_check():
    """
    系统健康检查
    
    Returns:
        bool: 检查是否通过
    """
    checks = []
    
    # 检查环境变量
    required_envs = [
        ("PROJECT_NAME", "项目名称"),
        ("SPHARX_WORKSHOP_ROOT", "工作空间根目录"),
        ("OSS_ENDPOINT", "OSS端点"),
        ("OSS_BUCKET", "OSS存储桶")
    ]
    
    for env_var, description in required_envs:
        value = os.getenv(env_var)
        if value:
            checks.append(("环境变量", f"{description}({env_var})", "✅", value))
        else:
            checks.append(("环境变量", f"{description}({env_var})", "❌", "未设置"))
    
    # 检查目录是否存在
    required_dirs = [
        ("SPHARX_INPUT_DIR", "输入数据目录"),
        ("SPHARX_OUTPUT_DIR", "输出数据目录"),
        ("SPHARX_WORKSPACE_DIR", "工作区目录")
    ]
    
    for env_var, description in required_dirs:
        dir_path = os.getenv(env_var)
        if dir_path and Path(dir_path).exists():
            checks.append(("目录检查", description, "✅", dir_path))
        elif dir_path:
            checks.append(("目录检查", description, "❌", f"路径不存在: {dir_path}"))
        else:
            checks.append(("目录检查", description, "⚠️", "环境变量未设置"))
    
    # 检查Python模块
    required_modules = [
        ("pydantic", "数据验证"),
        ("loguru", "日志记录"),
        ("opencv-python", "图像处理"),
        ("segment_anything", "SAM模型")
    ]
    
    for module_name, description in required_modules:
        try:
            __import__(module_name.replace("-", "_"))
            checks.append(("Python模块", description, "✅", module_name))
        except ImportError:
            checks.append(("Python模块", description, "❌", f"未安装: {module_name}"))
    
    # 检查Docker服务
    try:
        import docker
        client = docker.from_env()
        client.ping()
        checks.append(("Docker服务", "Docker引擎", "✅", "运行正常"))
    except Exception as e:
        checks.append(("Docker服务", "Docker引擎", "❌", f"连接失败: {e}"))
    
    # 输出检查结果
    print("\n" + "="*80)
    print("SpharxWorkshop 健康检查报告")
    print("="*80)
    
    # 按类别分组显示
    categories = {}
    for category, item, status, detail in checks:
        if category not in categories:
            categories[category] = []
        categories[category].append((item, status, detail))
    
    all_passed = True
    
    for category, items in categories.items():
        print(f"\n{category}:")
        print("-" * 60)
        
        for item, status, detail in items:
            print(f"  {status} {item}: {detail}")
            if status == "❌":
                all_passed = False
    
    print("\n" + "="*80)
    
    if all_passed:
        print("✅ 所有检查通过！系统状态正常。")
    else:
        print("⚠️  存在一些问题，请根据上述提示修复。")
    
    return all_passed


def start_api_server(host: str = "0.0.0.0", port: int = 8080):
    """
    启动API服务器（开发中）
    
    Args:
        host: 监听地址
        port: 监听端口
    """
    try:
        # 尝试导入FastAPI相关模块
        from fastapi import FastAPI
        import uvicorn
        
        app = FastAPI(title="SpharxWorkshop API", version="1.0.0")
        
        @app.get("/")
        async def root():
            return {"message": "SpharxWorkshop API Server", "status": "running"}
        
        @app.get("/health")
        async def health():
            return {"status": "healthy", "timestamp": "2024-01-01T00:00:00Z"}
        
        logger.info(f"启动API服务器: {host}:{port}")
        print(f"🚀 API服务器启动中: http://{host}:{port}")
        print("📚 API文档: http://{host}:{port}/docs")
        print("⏹️  按 Ctrl+C 停止服务器")
        
        # 在实际部署中，应该使用下面的代码
        # uvicorn.run(app, host=host, port=port)
        
        # 这里先打印信息，实际运行需要安装fastapi和uvicorn
        print("\n⚠️  注意: API服务器功能需要额外依赖")
        print("安装依赖: pip install fastapi uvicorn")
        print("然后取消注释 src/main.py 中的 uvicorn.run() 代码")
        
    except ImportError:
        print("❌ 缺少API服务器依赖")
        print("请安装: pip install fastapi uvicorn")
        print("或者使用其他命令如 'pipeline' 或 'manager'")


def main():
    """主函数 - 命令行入口点"""
    parser = argparse.ArgumentParser(
        description="SpharxWorkshop 空间智能数据生产线",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 传统方式 - 直接运行流水线
  python src/main.py pipeline --type 2d --scene scene_001
  
  # 推荐方式 - 通过任务管理器
  python src/main.py manager submit --scene scene_001 --type 2d
  python src/main.py manager status --list
  python src/main.py manager dashboard
  
  # 系统检查
  python src/main.py health-check
  
  # 启动API服务器
  python src/main.py server --port 8081
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # pipeline 命令 - 直接运行流水线
    pipeline_parser = subparsers.add_parser("pipeline", help="直接运行数据处理流水线")
    pipeline_parser.add_argument("--type", "-t", required=True, 
                               choices=["2d", "3d", "physics", "full"],
                               help="流水线类型")
    pipeline_parser.add_argument("--scene", "-s", required=True,
                               help="场景ID")
    pipeline_parser.add_argument("--config", "-c",
                               help="配置文件路径")
    
    # manager 命令 - 任务管理器
    manager_parser = subparsers.add_parser("manager", help="流水线任务管理器（推荐方式）")
    manager_subparsers = manager_parser.add_subparsers(dest="manager_command", help="管理器子命令")
    
    # manager submit - 提交新任务
    submit_parser = manager_subparsers.add_parser("submit", help="提交新任务")
    submit_parser.add_argument("--scene", "-s", required=True, help="场景ID")
    submit_parser.add_argument("--type", "-t", default="2d", 
                              choices=["2d", "3d", "full"],
                              help="流水线类型")
    submit_parser.add_argument("--priority", "-p", type=int, default=1,
                              choices=range(1, 11),
                              help="任务优先级 (1-10)")
    submit_parser.add_argument("--config-overrides", "-o", type=json.loads,
                              default="{}",
                              help='配置覆盖，JSON格式，如：\'{"max_concurrent_tasks": 2}\'')
    
    # manager status - 查看任务状态
    status_parser = manager_subparsers.add_parser("status", help="查看任务状态")
    status_group = status_parser.add_mutually_exclusive_group(required=True)
    status_group.add_argument("--task-id", "-t", help="查看指定任务ID的状态")
    status_group.add_argument("--list", "-l", action="store_true",
                            help="列出所有任务")
    status_parser.add_argument("--filter", "-f",
                              choices=["pending", "processing", "completed", "failed", "cancelled"],
                              help="过滤任务状态")
    status_parser.add_argument("--limit", type=int, default=20,
                              help="列表显示的最大任务数")
    
    # manager dashboard - 监控仪表板
    manager_subparsers.add_parser("dashboard", help="查看监控仪表板")
    
    # manager cancel - 取消任务（预留）
    cancel_parser = manager_subparsers.add_parser("cancel", help="取消任务")
    cancel_parser.add_argument("--task-id", "-t", required=True, help="要取消的任务ID")
    
    # health-check 命令
    subparsers.add_parser("health-check", help="系统健康检查")
    
    # server 命令
    server_parser = subparsers.add_parser("server", help="启动API服务器")
    server_parser.add_argument("--host", default="0.0.0.0", help="监听地址")
    server_parser.add_argument("--port", type=int, default=8080, help="监听端口")
    
    # 如果没有提供命令，显示帮助
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)
    
    args = parser.parse_args()
    
    # 初始化日志
    log_config_path = project_root / "configs" / "logging.yaml"
    setup_logging(str(log_config_path) if log_config_path.exists() else None)
    
    logger.info(f"执行命令: {args.command}")
    
    # 根据命令执行相应的函数
    if args.command == "pipeline":
        asyncio.run(run_pipeline(args.type, args.scene, args.config))
        
    elif args.command == "manager":
        asyncio.run(run_manager_command(args))
        
    elif args.command == "health-check":
        asyncio.run(health_check())
        
    elif args.command == "server":
        start_api_server(args.host, args.port)
        
    else:
        parser.print_help()


if __name__ == "__main__":
    main()