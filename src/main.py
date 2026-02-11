#!/usr/bin/env python3
"""
SpharxWorkshop 主控制程序
空间智能数据生产线入口点

命令结构：
1. pipeline - 直接运行流水线（简单模式）
2. manager  - 通过管理器运行（任务队列、监控）
3. health-check - 系统健康检查
4. server   - 启动API服务器（未来）
"""

import os
import sys
import asyncio
import json
import logging
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


async def run_pipeline(pipeline_type: str, scene_id: str, config_path: Optional[str] = None) -> Dict[str, Any]:
    """运行指定流水线（直接模式）"""
    try:
        from src.pipelines.pipeline_controller import PipelineController
        
        # 初始化配置
        config = PipelineConfig.from_yaml(config_path) if config_path else PipelineConfig()
        
        # 初始化控制器
        controller = PipelineController(config)
        
        # 运行流水线
        if pipeline_type == "2d":
            logger.info(f"启动2D标注流水线，场景: {scene_id}")
            result = await controller.run_2d_pipeline(scene_id)
        elif pipeline_type == "3d":
            logger.info(f"启动3D重建流水线，场景: {scene_id}")
            result = await controller.run_3d_pipeline(scene_id)
        elif pipeline_type == "physics":
            logger.info(f"启动物理事实生成流水线，场景: {scene_id}")
            result = await controller.run_physics_pipeline(scene_id)
        elif pipeline_type == "full":
            logger.info(f"启动完整流水线，场景: {scene_id}")
            result = await controller.run_full_pipeline(scene_id)
        else:
            logger.error(f"未知流水线类型: {pipeline_type}")
            return {"success": False, "error": f"未知流水线类型: {pipeline_type}"}
        
        logger.info(f"流水线执行完成: {pipeline_type} - {scene_id}")
        return {"success": True, "result": result}
        
    except Exception as e:
        logger.error(f"流水线执行失败: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


async def run_manager_command(args) -> Dict[str, Any]:
    """运行管理器命令"""
    try:
        from src.pipelines import get_pipeline_manager
        
        manager = get_pipeline_manager()
        await manager.initialize()
        
        if args.manager_command == "submit":
            # 提交新任务
            task_id = await manager.submit_pipeline_task(
                scene_id=args.scene,
                pipeline_type=args.type,
                priority=args.priority,
                config_overrides=args.config_overrides if hasattr(args, 'config_overrides') else {}
            )
            return {
                "success": True,
                "command": "submit",
                "task_id": task_id,
                "message": f"任务提交成功: {task_id}"
            }
            
        elif args.manager_command == "status":
            if args.task_id:
                # 查看特定任务状态
                status = await manager.get_task_status(args.task_id)
                if status:
                    return {
                        "success": True,
                        "command": "status",
                        "task_id": args.task_id,
                        "status": status
                    }
                else:
                    return {
                        "success": False,
                        "command": "status",
                        "error": f"任务不存在: {args.task_id}"
                    }
            elif args.list:
                # 列出任务
                tasks = await manager.get_task_list(
                    status_filter=args.filter,
                    limit=args.limit
                )
                return {
                    "success": True,
                    "command": "list",
                    "count": len(tasks),
                    "tasks": tasks
                }
                
        elif args.manager_command == "dashboard":
            # 查看监控仪表板
            dashboard = await manager.get_monitor_dashboard()
            return {
                "success": True,
                "command": "dashboard",
                "dashboard": dashboard
            }
            
        elif args.manager_command == "cancel":
            # 取消任务（需要实现）
            return {
                "success": False,
                "command": "cancel",
                "error": "取消功能暂未实现"
            }
            
        else:
            return {
                "success": False,
                "error": f"未知的管理器命令: {args.manager_command}"
            }
            
    except Exception as e:
        logger.error(f"管理器命令执行失败: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


async def health_check() -> Dict[str, Any]:
    """系统健康检查"""
    checks = []
    
    # 1. 检查环境变量
    required_envs = ["PROJECT_NAME", "OSS_ENDPOINT", "OSS_BUCKET"]
    for env_var in required_envs:
        if os.getenv(env_var):
            checks.append(("环境变量", env_var, "✅", f"已设置: {os.getenv(env_var)[:10]}..."))
        else:
            checks.append(("环境变量", env_var, "❌", "未设置"))
    
    # 2. 检查目录是否存在
    required_dirs = [
        ("输入目录", os.getenv("SPHARX_INPUT_DIR", "/home/SpharxWorkshop/data/input/scenes")),
        ("输出目录", os.getenv("SPHARX_OUTPUT_DIR", "/home/SpharxWorkshop/data/output/datasets")),
        ("工作空间", os.getenv("SPHARX_WORKSPACE_DIR", "/home/SpharxWorkshop/workspace")),
    ]
    
    for dir_name, dir_path in required_dirs:
        if dir_path and os.path.exists(dir_path):
            checks.append(("目录检查", dir_name, "✅", f"存在: {dir_path}"))
        else:
            checks.append(("目录检查", dir_name, "❌", f"不存在: {dir_path}"))
    
    # 3. 检查Python模块
    required_modules = [
        ("Pydantic", "pydantic"),
        ("Loguru", "loguru"),
        ("OpenCV", "cv2"),
        ("Open3D", "open3d"),
    ]
    
    for module_name, module_import in required_modules:
        try:
            __import__(module_import)
            checks.append(("Python模块", module_name, "✅", "已安装"))
        except ImportError:
            checks.append(("Python模块", module_name, "❌", "未安装"))
    
    # 4. 检查Docker服务
    try:
        import docker
        client = docker.from_env()
        client.ping()
        checks.append(("Docker服务", "Docker Engine", "✅", "运行正常"))
    except Exception as e:
        checks.append(("Docker服务", "Docker Engine", "❌", f"异常: {str(e)}"))
    
    # 汇总结果
    total_checks = len(checks)
    passed_checks = sum(1 for _, _, status, _ in checks if status == "✅")
    health_score = passed_checks / total_checks if total_checks > 0 else 0
    
    return {
        "success": health_score > 0.7,
        "health_score": health_score,
        "total_checks": total_checks,
        "passed_checks": passed_checks,
        "checks": checks,
        "timestamp": asyncio.get_event_loop().time()
    }


async def start_server(host: str = "0.0.0.0", port: int = 8080):
    """启动API服务器"""
    try:
        # 这里可以集成FastAPI或其他Web框架
        logger.info(f"启动API服务器: {host}:{port}")
        
        # 模拟服务器启动
        # TODO: 实现实际的API服务器
        print(f"🚀 API服务器正在启动...")
        print(f"   📍 地址: http://{host}:{port}")
        print(f"   📚 API文档: http://{host}:{port}/docs")
        print(f"   🏗️  状态: 开发中，功能尚未完全实现")
        
        # 保持服务器运行
        while True:
            await asyncio.sleep(3600)  # 每小时检查一次
            
    except KeyboardInterrupt:
        logger.info("API服务器已停止")
    except Exception as e:
        logger.error(f"API服务器启动失败: {e}", exc_info=True)


def print_health_report(health_result: Dict[str, Any]):
    """打印健康检查报告"""
    print("\n" + "="*60)
    print("SpharxWorkshop 健康检查报告")
    print("="*60)
    
    for category, item, status, detail in health_result["checks"]:
        print(f"{status} {category}: {item:20} {detail}")
    
    print("-"*60)
    print(f"健康分数: {health_result['health_score']:.1%}")
    print(f"通过检查: {health_result['passed_checks']}/{health_result['total_checks']}")
    
    if health_result["success"]:
        print("✅ 系统健康状态: 正常")
    else:
        print("❌ 系统健康状态: 异常，请检查上述问题")
    
    print("="*60)


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="SpharxWorkshop 空间智能数据生产线",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 直接运行2D流水线
  python main.py pipeline --type 2d --scene scene_001
  
  # 通过管理器提交任务
  python main.py manager submit --scene scene_001 --type 2d
  
  # 查看任务状态
  python main.py manager status --list
  python main.py manager status --task-id task_20240101_120000_scene_001
  
  # 系统健康检查
  python main.py health-check
  
  # 启动API服务器
  python main.py server --host 0.0.0.0 --port 8080
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
    
    # manager 命令 - 通过管理器运行
    manager_parser = subparsers.add_parser("manager", help="流水线管理器（任务队列、监控）")
    manager_subparsers = manager_parser.add_subparsers(dest="manager_command", help="管理器子命令")
    
    # manager submit - 提交任务
    submit_parser = manager_subparsers.add_parser("submit", help="提交新任务")
    submit_parser.add_argument("--scene", "-s", required=True, help="场景ID")
    submit_parser.add_argument("--type", "-t", default="2d", 
                              choices=["2d", "3d", "full"],
                              help="流水线类型")
    submit_parser.add_argument("--priority", "-p", type=int, default=1,
                              help="任务优先级 (1-10)")
    submit_parser.add_argument("--config-overrides", "-o", type=json.loads,
                              default={}, help="配置覆盖（JSON字符串）")
    
    # manager status - 查看状态
    status_parser = manager_subparsers.add_parser("status", help="查看任务状态")
    status_group = status_parser.add_mutually_exclusive_group(required=True)
    status_group.add_argument("--task-id", "-t", help="任务ID")
    status_group.add_argument("--list", "-l", action="store_true",
                             help="列出所有任务")
    status_parser.add_argument("--filter", "-f", 
                              choices=["pending", "processing", "completed", "failed"],
                              help="过滤状态")
    status_parser.add_argument("--limit", type=int, default=20,
                              help="列表限制数量")
    
    # manager dashboard - 监控仪表板
    manager_subparsers.add_parser("dashboard", help="查看监控仪表板")
    
    # manager cancel - 取消任务
    cancel_parser = manager_subparsers.add_parser("cancel", help="取消任务")
    cancel_parser.add_argument("--task-id", "-t", required=True, help="任务ID")
    
    # health-check 命令
    subparsers.add_parser("health-check", help="系统健康检查")
    
    # server 命令
    server_parser = subparsers.add_parser("server", help="启动API服务器")
    server_parser.add_argument("--host", default="0.0.0.0", help="监听地址")
    server_parser.add_argument("--port", type=int, default=8080, help="监听端口")
    
    # version 命令
    subparsers.add_parser("version", help="显示版本信息")
    
    args = parser.parse_args()
    
    # 初始化日志
    setup_logging()
    
    if args.command == "pipeline":
        # 直接运行流水线
        result = asyncio.run(run_pipeline(args.type, args.scene, args.config))
        if result["success"]:
            print("✅ 流水线执行成功")
            if "result" in result:
                print(json.dumps(result["result"], indent=2, default=str))
        else:
            print(f"❌ 流水线执行失败: {result.get('error', '未知错误')}")
        
    elif args.command == "manager":
        # 通过管理器运行
        result = asyncio.run(run_manager_command(args))
        
        # 格式化输出
        if result["success"]:
            command = result.get("command", "")
            
            if command == "submit":
                print(f"✅ {result['message']}")
                
            elif command == "status" and "status" in result:
                print(json.dumps(result["status"], indent=2, default=str))
                
            elif command == "list":
                tasks = result.get("tasks", [])
                print(f"📋 任务列表 ({len(tasks)} 个):")
                for task in tasks:
                    status_icon = {
                        "pending": "⏳",
                        "processing": "🔄",
                        "completed": "✅",
                        "failed": "❌",
                        "cancelled": "🚫"
                    }.get(task.get("status", ""), "❓")
                    
                    print(f"  {status_icon} {task['id']}")
                    print(f"     场景: {task['scene_id']}, 类型: {task['pipeline_type']}")
                    print(f"     状态: {task['status']}, 进度: {task.get('progress', 0)*100:.1f}%")
                    print()
                    
            elif command == "dashboard":
                dashboard = result.get("dashboard", {})
                print(f"📊 系统监控仪表板")
                print(f"   总任务数: {dashboard.get('total_tasks', 0)}")
                print(f"   已完成: {dashboard.get('completed_tasks', 0)}")
                print(f"   已失败: {dashboard.get('failed_tasks', 0)}")
                print(f"   平均处理时间: {dashboard.get('avg_processing_time', 0):.2f}秒")
                print(f"   系统状态: {dashboard.get('system_status', 'unknown')}")
                
        else:
            print(f"❌ 命令执行失败: {result.get('error', '未知错误')}")
        
    elif args.command == "health-check":
        # 系统健康检查
        health_result = asyncio.run(health_check())
        print_health_report(health_result)
        
    elif args.command == "server":
        # 启动API服务器
        asyncio.run(start_server(args.host, args.port))
        
    elif args.command == "version":
        # 显示版本信息
        print("SpharxWorkshop - 空间智能数据生产线")
        print("版本: 1.0.0")
        print("状态: 开发版")
        print("许可证: Apache 2.0")
        print("仓库: https://gitee.com/spharx/toolchain")
        
    else:
        # 显示帮助信息
        parser.print_help()


if __name__ == "__main__":
    main()