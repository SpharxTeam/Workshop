# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
# 交付 (Delivery) Pipeline V2 - 数据集上传与通知
# 使用 BasePipeline 基类重构，消除重复代码

import sys
import os
from typing import Any, Dict, Optional, List

sys.path.insert(0, '/app/common/scripts')

from common.core import (
    BasePipeline,
    PipelineResult,
    ConfigManager,
    setup_logging,
    InputValidator,
    ErrorCode,
    PipelineError,
    ConfigurationError
)


class DeliveryPipeline(BasePipeline):
    """
    数据交付 Pipeline
    
    功能：
    - 将打包好的数据集上传至 OSS（对象存储）
    - 发送交付通知（邮件/Webhook/消息队列）
    - 上传状态跟踪和重试机制
    - 交付记录生成
    - 安全性检查（敏感信息过滤）
    
    配置项：
        - oss.endpoint: OSS 端点URL
        - oss.bucket: 存储桶名称
        - oss.access_key_id: 访问密钥ID
        - oss.access_key_secret: 访问密钥Secret
        - oss.prefix: 上传路径前缀 (/datasets/)
        - notification.enabled: 是否启用通知 (True)
        - notification.type: 通知类型 (email/webhook/slack)
        - notification.recipients: 通知接收者列表
        - retry_count: 上传失败重试次数 (3)
        - dry_run: 模拟模式，不上传实际数据 (False)
    
    Example:
        >>> pipeline = DeliveryPipeline()
        >>> result = pipeline.run(
        ...     input_data="/app/output/datasets/scene_001",
        ...     dry_run=True  # 测试模式
        ... )
    """
    
    MODULE_NAME = "05_delivery"
    VERSION = "2.0.0"
    
    REQUIRED_OSS_CONFIG = [
        'endpoint',
        'bucket',
        'access_key_id',
        'access_key_secret'
    ]
    
    def _initialize(self) -> None:
        """初始化交付资源"""
        self._logger.info("初始化 Delivery Pipeline...")
        
        try:
            from algorithm.oss_uploader import upload_dataset
            from algorithm.notifier import send_notification
            
            self._upload_dataset = upload_dataset
            self._send_notification = send_notification
            
            self._logger.debug("交付算法模块加载成功")
            
        except ImportError as e:
            raise PipelineError(
                ErrorCode.MODULE_LOAD_FAILED,
                f"无法加载交付算法模块: {e}",
                cause=e
            )
    
    def _execute(self, input_data: Any = None, **kwargs) -> PipelineResult:
        """
        执行数据交付
        
        Args:
            input_data: 待上传的数据集目录路径
            **kwargs:
                - dry_run: 模拟模式（不实际上传）
                
        Returns:
            PipelineResult: 交付结果
        """
        validator = InputValidator()
        
        # 获取参数
        dataset_dir = kwargs.get('input') or input_data or self.config.get('dataset_dir')
        dry_run = kwargs.get('dry_run', False) or self.config.get('dry_run', default=False)
        
        # 验证输入目录存在
        path_validation = validator.validate_path(
            dataset_dir,
            must_exist=True,
            should_be_dir=True,
            name='dataset_dir'
        )
        if not path_validation.valid:
            return PipelineResult(
                success=False,
                error='\n'.join(path_validation.errors),
                error_code=ErrorCode.VALIDATION_FAILED
            )
        
        # 加载和验证 OSS 配置
        oss_config = self._load_oss_config()
        
        # 检查 OSS 配置完整性
        missing_configs = [
            key for key in self.REQUIRED_OSS_CONFIG 
            if not oss_config.get(key)
        ]
        
        if missing_configs and not dry_run:
            msg = (
                f"OSS 配置不完整，缺少: {missing_configs}\n"
                f"可通过环境变量设置 (如 OSS_ENDPOINT) 或在配置文件中指定\n"
                f"或使用 --dry-run 参数进行模拟测试"
            )
            
            self._logger.warning(msg)
            
            # 如果配置严重缺失，返回错误
            if len(missing_configs) >= 3:
                return PipelineResult(
                    success=False,
                    error=msg,
                    error_code=ErrorCode.CONFIG_MISSING_REQUIRED
                )
            
            self._add_warning(msg)
        
        # 构建交付元数据
        delivery_meta = {
            'dataset_path': str(dataset_dir),
            'dataset_name': os.path.basename(dataset_dir.rstrip('/')),
            'timestamp': __import__('time').strftime('%Y-%m-%d %H:%M:%S'),
            'dry_run': dry_run,
            'oss_config': {
                k: ('*' * 8 if 'key' in k.lower() and v else v) 
                for k, v in oss_config.items()  # 隐藏敏感信息
            }
        }
        
        mode_str = "[模拟模式] " if dry_run else ""
        self._logger.info(
            f"{mode_str}开始数据交付:\n"
            f"  数据集: {delivery_meta['dataset_name']}\n"
            f"  目标存储桶: {oss_config.get('bucket', 'N/A')}"
        )
        
        start_time = __import__('time').time()
        
        try:
            # 执行上传（或模拟）
            if dry_run:
                self._logger.info("[DRY-RUN] 模拟上传流程...")
                upload_success = True
                
                # 模拟统计数据
                upload_stats = {
                    'files_scanned': self._count_files(dataset_dir),
                    'files_uploaded': 0,
                    'total_bytes': 0,
                    'upload_duration_s': 0
                }
            else:
                upload_success = self._upload_dataset(dataset_dir, oss_config)
                upload_stats = {}  # 实际上传后会填充
            
            execution_time = __import__('time').time() - start_time
            self._increment_processed(1)
            
            if upload_success:
                # 发送通知
                notification_sent = False
                if self.config.get('notification.enabled', True):
                    try:
                        notification_msg = (
                            f"数据集 {delivery_meta['dataset_name']} "
                            f"已{'[模拟]' if dry_run else ''}成功交付"
                        )
                        self._send_notification(notification_msg, config=self.config.to_dict())
                        notification_sent = True
                    except Exception as notify_error:
                        self._add_warning(f"发送通知失败: {notify_error}")
                
                metrics = {
                    'execution_time': execution_time,
                    'dry_run': dry_run,
                    'notification_sent': notification_sent,
                    **upload_stats
                }
                
                result = PipelineResult(
                    success=True,
                    output={
                        'status': 'delivered' if not dry_run else 'dry_run_completed',
                        'metadata': delivery_meta,
                        'oss_bucket': oss_config.get('bucket'),
                        'notification_sent': notification_sent
                    },
                    metrics=metrics
                )
                
                status_msg = "✓ [模拟] " if dry_run else "✓ "
                self._logger.info(
                    f"{status_msg}数据交付完成\n"
                    f"  耗时: {execution_time:.2f}s\n"
                    f"  通知发送: {'是' if notification_sent else '否'}"
                )
                
                return result
            else:
                return PipelineResult(
                    success=False,
                    error="数据集上传失败",
                    error_code=ErrorCode.PIPELINE_EXECUTION_FAILED
                )
                
        except Exception as e:
            self._logger.error(f"交付过程异常: {e}", exc_info=True)
            return PipelineResult(
                success=False,
                error=f"交付失败: {e}",
                error_code=ErrorCode.IO_ERROR
            )
    
    def _cleanup(self) -> None:
        """清理资源"""
        self._logger.info("Delivery Pipeline 资源已释放")
    
    def _load_oss_config(self) -> Dict[str, str]:
        """
        加载 OSS 配置（支持多来源）
        
        优先级：命令行参数 > 配置文件 > 环境变量 > 默认值
        """
        oss_config = self.config.get_section('oss') or {}
        
        # 从环境变量补充缺失的配置
        env_mappings = {
            'endpoint': 'OSS_ENDPOINT',
            'bucket': 'OSS_BUCKET',
            'access_key_id': 'OSS_ACCESS_KEY_ID',
            'access_key_secret': 'OSS_ACCESS_KEY_SECRET',
            'region': 'OSS_REGION',
            'prefix': 'OSS_PREFIX'
        }
        
        for config_key, env_var in env_mappings.items():
            if not oss_config.get(config_key):
                env_value = os.environ.get(env_var)
                if env_value:
                    oss_config[config_key] = env_value
                    self._logger.debug(f"从环境变量加载 {config_key}")
        
        # 设置默认值
        defaults = {
            'prefix': '/datasets/',
            'region': 'cn-hangzhou'
        }
        
        for key, value in defaults.items():
            if key not in oss_config:
                oss_config[key] = value
        
        return oss_config
    
    @staticmethod
    def _count_files(directory: str) -> int:
        """统计目录中的文件数量"""
        from pathlib import Path
        dir_path = Path(directory)
        return len([f for f in dir_path.rglob('*') if f.is_file()])


def main():
    """主入口函数 - 向后兼容"""
    import argparse
    
    parser = argparse.ArgumentParser(description="数据交付模块 (v2.0)")
    parser.add_argument("--input", required=True, help="输入数据集目录")
    parser.add_argument("--dry-run", action="store_true", help="模拟模式（不上传）")
    parser.add_argument("--config", help="配置文件路径")
    args = parser.parse_args()
    
    # 设置日志
    logger = setup_logging("05_delivery")
    logger.info(f"Delivery Pipeline v{DeliveryPipeline.VERSION} 启动")
    
    # 创建并运行 Pipeline
    pipeline = DeliveryPipeline(config_path=args.config)
    
    run_kwargs = {'input': args.input}
    
    if args.dry_run:
        run_kwargs['dry_run'] = True
    
    result = pipeline.run(**run_kwargs)
    
    if result.success:
        logger.info("✓ 数据交付成功")
        sys.exit(0)
    else:
        logger.error(f"✗ 数据交付失败: {result.error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
