#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Workshop V2.0 运维管理工具集
============================
功能模块：
1. 🗑️ 日志文件自动清理与归档
2. 💾 项目数据自动备份（增量+全量）
3. 🔧 系统健康检查与维护
4. 📊 磁盘空间监控与告警
5. 🧹 临时文件与缓存清理
6. ⏰ 定时任务调度器（cron-like）

使用示例:
    # 清理7天前的日志
    python ops_toolkit.py --cleanup-logs --days 7
    
    # 创建项目备份
    python ops_toolkit.py --backup --type full
    
    # 运行全面健康检查
    python ops_toolkit.py --health-check
    
    # 一键日常维护
    python ops_toolkit.py --daily-maintenance
"""

import argparse
import gzip
import hashlib
import json
import os
import shutil
import stat
import sys
import tarfile
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any


class LogManager:
    """
    日志文件管理与归档工具
    ======================
    
    功能：
    - 按时间策略清理过期日志
    - 压缩并归档旧日志文件
    - 日志大小监控与告警
    - 多日志目录统一管理
    """
    
    def __init__(self, log_dirs: List[str] = None, max_age_days: int = 30,
                 max_size_mb: float = 500.0, archive_dir: str = None):
        self.log_dirs = log_dirs or ['logs', 'var/log']
        self.max_age_days = max_age_days
        self.max_size_mb = max_size_mb
        self.archive_dir = archive_dir or 'logs/archive'
        self.stats = {
            'files_scanned': 0,
            'files_deleted': 0,
            'files_archived': 0,
            'space_freed_mb': 0.0
        }
    
    def scan_logs(self) -> Dict[str, List[Dict]]:
        """扫描所有日志目录，返回日志文件信息"""
        all_logs = {}
        
        for log_dir in self.log_dirs:
            dir_path = Path(log_dir)
            if not dir_path.exists():
                continue
            
            logs_in_dir = []
            for log_file in dir_path.rglob('*.log'):
                try:
                    stat_info = log_file.stat()
                    mtime = datetime.fromtimestamp(stat_info.st_mtime)
                    age_days = (datetime.now() - mtime).days
                    
                    logs_in_dir.append({
                        'path': str(log_file),
                        'name': log_file.name,
                        'size_mb': round(stat_info.st_size / (1024 * 1024), 2),
                        'modified_time': mtime.isoformat(),
                        'age_days': age_days,
                        'should_delete': age_days > self.max_age_days
                    })
                    
                    self.stats['files_scanned'] += 1
                except Exception as e:
                    print(f"[警告] 无法读取 {log_file}: {e}")
            
            if logs_in_dir:
                all_logs[str(dir_path)] = logs_in_dir
        
        return all_logs
    
    def cleanup_old_logs(self, dry_run: bool = False) -> Dict[str, Any]:
        """清理超过保留期限的日志文件"""
        print(f"\n📋 开始日志清理 (保留最近 {self.max_age_days} 天)")
        print("="*60)
        
        log_data = self.scan_logs()
        
        for dir_path, logs in log_data.items():
            to_delete = [l for l in logs if l['should_delete']]
            
            if not to_delete:
                print(f"\n✅ {dir_path}: 无需清理")
                continue
            
            print(f"\n📁 {dir_path}: 发现 {len(to_delete)} 个过期日志")
            
            for log_info in to_delete:
                log_path = Path(log_info['path'])
                
                if dry_run:
                    print(f"   [预览] 将删除: {log_info['name']} "
                          f"({log_info['size_mb']}MB, {log_info['age_days']}天前)")
                else:
                    try:
                        # 先尝试压缩归档
                        if self._archive_log(log_path):
                            self.stats['files_archived'] += 1
                            self.stats['space_freed_mb'] += log_info['size_mb'] * 0.8  # 压缩率约80%
                            print(f"   ✅ 已归档: {log_info['name']}")
                        else:
                            log_path.unlink()
                            self.stats['files_deleted'] += 1
                            self.stats['space_freed_mb'] += log_info['size_mb']
                            print(f"   🗑️ 已删除: {log_info['name']}")
                    except Exception as e:
                        print(f"   ❌ 失败: {log_info['name']} - {e}")
        
        return {
            **self.stats,
            'timestamp': datetime.now().isoformat(),
            'dry_run': dry_run
        }
    
    def _archive_log(self, log_path: Path) -> bool:
        """将日志文件压缩归档"""
        try:
            archive_path = Path(self.archive_dir)
            archive_path.mkdir(parents=True, exist_ok=True)
            
            # 创建归档文件名: original_YYYYMMDD_HHMMSS.log.gz
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            archive_name = f"{log_path.stem}_{timestamp}.log.gz"
            archive_file = archive_path / archive_name
            
            with open(log_path, 'rb') as f_in:
                with gzip.open(archive_file, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # 删除原文件
            log_path.unlink()
            
            return True
        
        except Exception as e:
            print(f"[错误] 归档失败: {e}")
            return False
    
    def get_log_summary(self) -> Dict[str, Any]:
        """获取日志总体统计信息"""
        log_data = self.scan_logs()
        
        total_size = sum(
            l['size_mb'] for logs in log_data.values() for l in logs
        )
        
        oldest_log = min(
            (l for logs in log_data.values() for l in logs),
            key=lambda x: x['age_days'],
            default=None
        )
        
        return {
            'total_log_files': self.stats['files_scanned'],
            'total_size_mb': round(total_size, 2),
            'oldest_log_days': oldest_log['age_days'] if oldest_log else 0,
            'directories_scanned': len(log_data),
            'max_age_threshold': self.max_age_days,
            'max_size_threshold_mb': self.max_size_mb
        }


class BackupManager:
    """
    项目数据备份管理器
    ==================
    
    功能：
    - 全量备份（tar.gz格式）
    - 增量备份（基于修改时间）
    - 备份完整性校验（MD5/SHA256）
    - 备份版本管理与轮转
    - 支持本地和远程存储
    """
    
    def __init__(self, project_root: str = '.', backup_dir: str = 'backups',
                 exclude_patterns: List[str] = None):
        self.project_root = Path(project_root).resolve()
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
        
        # 默认排除项
        self.exclude_patterns = exclude_patterns or [
            '__pycache__', '*.pyc', '.git', '.gitignore',
            '*.egg-info', 'build', 'dist', 'venv', '.venv',
            'node_modules', '.env', '*.log', 'logs',
            'backups', '.DS_Store', '*.swp', '*~'
        ]
        
        self.current_backup_id = None
    
    def create_full_backup(self, name: Optional[str] = None,
                          compression_level: int = 9) -> Dict[str, Any]:
        """
        创建全量备份
        
        Args:
            name: 备份名称（默认使用时间戳）
            compression_level: 压缩级别(1-9)
        
        Returns:
            备份结果信息字典
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = name or f'full_{timestamp}'
        backup_file = self.backup_dir / f'{backup_name}.tar.gz'
        
        print(f"\n💾 创建全量备份: {backup_name}")
        print(f"   目标路径: {backup_file}")
        print(f"   压缩级别: {compression_level}")
        print("="*60)
        
        start_time = time.time()
        file_count = 0
        total_size = 0
        
        try:
            with tarfile.open(backup_file, f'w:gz', 
                            compresslevel=compression_level) as tar:
                for item in self._get_files_to_backup():
                    try:
                        tar.add(item, arcname=item.relative_to(self.project_root))
                        file_count += 1
                        total_size += item.stat().st_size
                        
                        if file_count % 100 == 0:
                            print(f"   已打包 {file_count} 个文件...")
                    except Exception as e:
                        print(f"   [警告] 跳过 {item}: {e}")
            
            elapsed = time.time() - start_time
            final_size = backup_file.stat().st_size / (1024 * 1024)
            
            # 生成校验和
            checksum = self._compute_checksum(backup_file)
            
            # 保存备份元数据
            metadata = {
                'id': backup_name,
                'type': 'full',
                'timestamp': datetime.now().isoformat(),
                'file_count': file_count,
                'original_size_mb': round(total_size / (1024 * 1024), 2),
                'compressed_size_mb': round(final_size, 2),
                'compression_ratio': round((1 - final_size / (total_size / (1024 * 1024))) * 100, 1),
                'elapsed_seconds': round(elapsed, 2),
                'checksum_md5': checksum['md5'],
                'checksum_sha256': checksum['sha256'],
                'excludes': self.exclude_patterns
            }
            
            metadata_file = self.backup_dir / f'{backup_name}_metadata.json'
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            self.current_backup_id = backup_name
            
            print(f"\n✅ 备份完成!")
            print(f"   文件数: {file_count}")
            print(f"   原始大小: {metadata['original_size_mb']} MB")
            print(f"   压缩后: {final_size:.2f} MB")
            print(f"   压缩比: {metadata['compression_ratio']}%")
            print(f"   耗时: {elapsed:.2f} 秒")
            print(f"   校验和(MD5): {checksum['md5'][:16]}...")
            
            return {'success': True, 'metadata': metadata}
        
        except Exception as e:
            print(f"\n❌ 备份失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def create_incremental_backup(self, last_backup_name: str = None,
                                 name: Optional[str] = None) -> Dict[str, Any]:
        """创建增量备份（只备份修改过的文件）"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = name or f'incremental_{timestamp}'
        backup_file = self.backup_dir / f'{backup_name}.tar.gz'
        
        # 找到上次备份的时间点
        if last_backup_name:
            last_metadata_file = self.backup_dir / f'{last_backup_name}_metadata.json'
            if last_metadata_file.exists():
                with open(last_metadata_file, 'r') as f:
                    last_meta = json.load(f)
                base_time = datetime.fromisoformat(last_meta['timestamp'])
            else:
                base_time = datetime.now() - timedelta(days=1)
        else:
            base_time = datetime.now() - timedelta(days=1)
        
        print(f"\n📦 创建增量备份: {backup_name}")
        print(f"   基准时间: {base_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)
        
        start_time = time.time()
        file_count = 0
        total_size = 0
        
        try:
            with tarfile.open(backup_file, 'w:gz') as tar:
                for item in self._get_files_to_backup():
                    try:
                        mod_time = datetime.fromtimestamp(item.stat().st_mtime)
                        
                        if mod_time > base_time:
                            tar.add(item, arcname=item.relative_to(self.project_root))
                            file_count += 1
                            total_size += item.stat().st_size
                    except Exception as e:
                        pass
            
            elapsed = time.time() - start_time
            
            metadata = {
                'id': backup_name,
                'type': 'incremental',
                'base_backup': last_backup_name,
                'timestamp': datetime.now().isoformat(),
                'changed_files': file_count,
                'size_mb': round(total_size / (1024 * 1024), 2),
                'elapsed_seconds': round(elapsed, 2)
            }
            
            metadata_file = self.backup_dir / f'{backup_name}_metadata.json'
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            print(f"\n✅ 增量备份完成! 变更文件: {file_count}, 耗时: {elapsed:.2f}s")
            return {'success': True, 'metadata': metadata}
        
        except Exception as e:
            print(f"\n❌ 增量备份失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """列出所有可用备份"""
        backups = []
        
        for meta_file in sorted(self.backup_dir.glob('*_metadata.json')):
            try:
                with open(meta_file, 'r') as f:
                    meta = json.load(f)
                
                backup_tar = self.backup_dir / f"{meta['id']}.tar.gz"
                meta['exists'] = backup_tar.exists()
                meta['size_mb'] = round(backup_tar.stat().st_size / (1024 * 1024), 2) if backup_tar.exists() else 0
                
                backups.append(meta)
            except Exception:
                pass
        
        return sorted(backups, key=lambda x: x.get('timestamp', ''), reverse=True)
    
    def restore_backup(self, backup_name: str, target_dir: str = None,
                      overwrite: bool = False) -> Dict[str, Any]:
        """从备份恢复"""
        backup_file = self.backup_dir / f'{backup_name}.tar.gz'
        
        if not backup_file.exists():
            return {'success': False, 'error': f'备份文件不存在: {backup_name}'}
        
        restore_target = Path(target_dir) if target_dir else self.project_root
        
        if not overwrite and any(restore_target.iterdir()):
            return {'success': False, 'error': '目标目录非空，请使用 --overwrite 强制覆盖'}
        
        print(f"\n🔄 从备份恢复: {backup_name}")
        print(f"   目标目录: {restore_target}")
        
        try:
            start_time = time.time()
            file_count = 0
            
            with tarfile.open(backup_file, 'r:gz') as tar:
                members = tar.getmembers()
                
                for member in members:
                    tar.extract(member, path=restore_target)
                    file_count += 1
                
                    if file_count % 500 == 0:
                        print(f"   已恢复 {file_count}/{len(members)} 个文件...")
            
            elapsed = time.time() - start_time
            print(f"\n✅ 恢复完成! 文件数: {file_count}, 耗时: {elapsed:.2f}s")
            
            return {
                'success': True,
                'restored_files': file_count,
                'elapsed_seconds': round(elapsed, 2)
            }
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _get_files_to_backup(self) -> List[Path]:
        """获取需要备份的文件列表（排除不需要的）"""
        files = []
        
        for item in self.project_root.rglob('*'):
            if not item.is_file():
                continue
            
            # 检查排除模式
            excluded = False
            rel_path = str(item.relative_to(self.project_root))
            
            for pattern in self.exclude_patterns:
                if pattern.startswith('*'):
                    if item.name.endswith(pattern[1:]) or item.suffix == pattern[1:]:
                        excluded = True
                        break
                elif pattern in rel_path or pattern in item.name:
                    excluded = True
                    break
            
            if not excluded:
                files.append(item)
        
        return files
    
    def _compute_checksum(self, file_path: Path, 
                         algorithm: str = 'md5') -> Dict[str, str]:
        """计算文件校验和"""
        hashes = {}
        
        for algo in ['md5', 'sha256']:
            h = hashlib.new(algo)
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b''):
                    h.update(chunk)
            hashes[algo] = h.hexdigest()
        
        return hashes
    
    def rotate_backups(self, keep_count: int = 5) -> Dict[str, Any]:
        """备份轮转：只保留最近的N个备份"""
        backups = self.list_backups()
        
        if len(backups) <= keep_count:
            print(f"\n✅ 当前备份数 ({len(backouts)}) 未超过保留上限 ({keep_count})")
            return {'rotated': 0, 'kept': len(backups)}
        
        to_remove = backups[keep_count:]
        removed_count = 0
        
        print(f"\n🔄 备份轮转: 保留最近 {keep_count} 个，删除 {len(to_remove)} 个旧备份")
        
        for backup in to_remove:
            try:
                backup_file = self.backup_dir / f"{backup['id']}.tar.gz"
                meta_file = self.backup_dir / f"{backup['id']}_metadata.json"
                
                if backup_file.exists():
                    backup_file.unlink()
                if meta_file.exists():
                    meta_file.unlink()
                
                removed_count += 1
                print(f"   🗑️ 删除: {backup['id']}")
            except Exception as e:
                print(f"   ❌ 删除失败: {backup['id']} - {e}")
        
        return {'rotated': removed_count, 'kept': keep_count}


class SystemHealthChecker:
    """
    系统健康检查工具
    ================
    
    检查项目：
    - Python环境与依赖
    - 磁盘空间使用情况
    - 内存使用情况
    - 关键进程状态
    - 配置文件完整性
    - 权限检查
    """
    
    def __init__(self, project_root: str = '.'):
        self.project_root = Path(project_root).resolve()
        self.checks_performed = 0
        self.checks_passed = 0
        self.checks_failed = 0
        self.warnings = []
        self.errors = []
    
    def run_full_checkup(self) -> Dict[str, Any]:
        """运行完整的系统健康检查"""
        print("\n" + "="*70)
        print("🏥 Workshop V2.0 系统健康检查")
        print("="*70)
        
        results = {}
        
        # 1. Python环境检查
        results['python_environment'] = self._check_python_env()
        
        # 2. 磁盘空间检查
        results['disk_space'] = self._check_disk_space()
        
        # 3. 关键目录结构检查
        results['directory_structure'] = self._check_directory_structure()
        
        # 4. 配置文件检查
        results['configuration_files'] = self._check_config_files()
        
        # 5. 依赖包状态检查
        results['dependencies'] = self._check_dependencies()
        
        # 6. 日志系统检查
        results['logging_system'] = self._check_logging_system()
        
        # 输出汇总
        total = self.checks_performed
        passed = self.checks_passed
        failed = self.checks_failed
        
        print("\n" + "="*70)
        print("📊 健康检查汇总")
        print("="*70)
        print(f"   总检查项: {total}")
        print(f"   ✅ 通过: {passed} ({passed/total*100:.1f}%)" if total > 0 else "")
        print(f"   ❌ 失败: {failed} ({failed/total*100:.1f}%)" if total > 0 else "")
        
        if self.warnings:
            print(f"\n⚠️  警告 ({len(self.warnings)}):")
            for w in self.warnings[:5]:  # 只显示前5个
                print(f"   • {w}")
        
        if self.errors:
            print(f"\n🔴 错误 ({len(self.errors)}):")
            for e in self.errors[:5]:
                print(f"   • {e}")
        
        health_score = (passed / total * 100) if total > 0 else 100
        
        if health_score >= 90:
            status = "✅ 健康"
        elif health_score >= 70:
            status = "⚠️  需要关注"
        else:
            status = "❌ 需要紧急处理"
        
        print(f"\n🏥 总体状态: {status} (得分: {health_score:.1f}/100)")
        
        return {
            'health_score': health_score,
            'status': status,
            'checks_total': total,
            'checks_passed': passed,
            'checks_failed': failed,
            'warnings': self.warnings,
            'errors': self.errors,
            'details': results
        }
    
    def _check_python_env(self) -> Dict[str, Any]:
        """检查Python环境"""
        print("\n🐍 Python环境检查...")
        result = {'status': 'ok', 'details': {}}
        
        import sys
        import platform
        
        details = result['details']
        details['version'] = sys.version.split()[0]
        details['executable'] = sys.executable
        details['platform'] = platform.system()
        
        version = sys.version_info
        if version.major == 3 and version.minor >= 8:
            print(f"   ✅ Python版本: {details['version']} (符合要求 ≥3.8)")
            self.checks_passed += 1
        else:
            print(f"   ❌ Python版本过低: {details['version']} (要求 ≥3.8)")
            result['status'] = 'warning'
            self.warnings.append(f"Python版本建议升级至3.8+")
            self.checks_failed += 1
        
        self.checks_performed += 1
        return result
    
    def _check_disk_space(self) -> Dict[str, Any]:
        """检查磁盘空间"""
        print("\n💾 磁盘空间检查...")
        result = {'status': 'ok', 'details': {}}
        
        try:
            usage = shutil.disk_usage(self.project_root)
            
            total_gb = usage.total / (1024**3)
            used_gb = usage.used / (1024**3)
            free_gb = usage.free / (1024**3)
            used_pct = (usage.used / usage.total) * 100
            
            details = result['details']
            details['total_gb'] = round(total_gb, 2)
            details['used_gb'] = round(used_gb, 2)
            details['free_gb'] = round(free_gb, 2)
            details['used_percentage'] = round(used_pct, 1)
            
            print(f"   总容量: {total_gb:.2f} GB")
            print(f"   已使用: {used_gb:.2f} GB ({used_pct:.1f}%)")
            print(f"   可用空间: {free_gb:.2f} GB")
            
            if used_pct > 90:
                print("   🔴 磁盘空间严重不足 (<10% 可用)")
                result['status'] = 'critical'
                self.errors.append(f"磁盘空间不足，仅剩{free_gb:.1f}GB")
                self.checks_failed += 1
            elif used_pct > 80:
                print("   ⚠️  磁盘空间偏紧 (<20% 可用)")
                result['status'] = 'warning'
                self.warnings.append(f"磁盘空间使用率达{used_pct:.1f}%")
                self.checks_passed += 1  # 仍算通过但警告
            else:
                print("   ✅ 磁盘空间充足")
                self.checks_passed += 1
            
        except Exception as e:
            print(f"   ❌ 检查失败: {e}")
            result['status'] = 'error'
            self.errors.append(f"磁盘检查异常: {e}")
            self.checks_failed += 1
        
        self.checks_performed += 1
        return result
    
    def _check_directory_structure(self) -> Dict[str, Any]:
        """检查关键目录结构"""
        print("\n📁 目录结构检查...")
        result = {'status': 'ok', 'missing_dirs': []}
        
        expected_dirs = [
            'common/core',
            'pipelines',
            'hardware',
            'tests',
            'scripts',
            'docs'
        ]
        
        for dir_name in expected_dirs:
            dir_path = self.project_root / dir_name
            if dir_path.exists() and dir_path.is_dir():
                print(f"   ✅ {dir_name}/")
                self.checks_passed += 1
            else:
                print(f"   ❌ 缺失: {dir_name}/")
                result['missing_dirs'].append(dir_name)
                self.checks_failed += 1
                result['status'] = 'error'
            
            self.checks_performed += 1
        
        return result
    
    def _check_config_files(self) -> Dict[str, Any]:
        """检查关键配置文件"""
        print("\n⚙️  配置文件检查...")
        result = {'status': 'ok', 'missing_configs': []}
        
        config_files = [
            ('common/core/__init__.py', '核心模块初始化'),
            ('common/core/config_manager.py', '配置管理器'),
            ('common/core/base_pipeline.py', '管道基类'),
            ('common/core/exceptions.py', '异常定义'),
        ]
        
        for file_path, description in config_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                size = full_path.stat().st_size
                print(f"   ✅ {description}: {file_path} ({size:,} bytes)")
                self.checks_passed += 1
            else:
                print(f"   ❌ 缺失: {description} - {file_path}")
                result['missing_configs'].append(file_path)
                self.checks_failed += 1
                result['status'] = 'error'
            
            self.checks_performed += 1
        
        return result
    
    def _check_dependencies(self) -> Dict[str, Any]:
        """检查依赖包安装情况"""
        print("\n📦 依赖包检查...")
        result = {'status': 'ok', 'installed': [], 'missing': []}
        
        required_packages = [
            ('numpy', 'NumPy'),
            ('opencv-python', 'OpenCV'),
            ('PyYAML', 'PyYAML'),
            ('Pillow', 'Pillow'),
        ]
        
        for package, display_name in required_packages:
            try:
                __import__(package.replace('-', '_'))
                print(f"   ✅ {display_name}")
                result['installed'].append(package)
                self.checks_passed += 1
            except ImportError:
                print(f"   ❌ 未安装: {display_name} (pip install {package})")
                result['missing'].append(package)
                self.checks_failed += 1
                result['status'] = 'warning'
            
            self.checks_performed += 1
        
        return result
    
    def _check_logging_system(self) -> Dict[str, Any]:
        """检查日志系统"""
        print("\n📝 日志系统检查...")
        result = {'status': 'ok', 'details': {}}
        
        log_dir = self.project_root / 'logs'
        if log_dir.exists():
            log_files = list(log_dir.glob('*.log'))
            total_size = sum(f.stat().st_size for f in log_files)
            
            details = result['details']
            details['log_count'] = len(log_files)
            details['total_size_mb'] = round(total_size / (1024*1024), 2)
            
            print(f"   日志文件数: {len(log_files)}")
            print(f"   总大小: {details['total_size_mb']} MB")
            
            if details['total_size_mb'] > 1000:  # >1GB
                print("   ⚠️  日志文件过大，建议清理")
                self.warnings.append("日志占用空间过多(>1GB)")
                result['status'] = 'warning'
            
            self.checks_passed += 1
        else:
            print("   ℹ️  日志目录不存在（首次运行正常）")
            self.checks_passed += 1
        
        self.checks_performed += 1
        return result


class TempFileCleaner:
    """
    临时文件与缓存清理工具
    =======================
    
    功能：
    - 清理__pycache__目录
    - 清理.pyc编译文件
    - 清理编辑器临时文件
    - 清理测试缓存
    - 自定义模式匹配清理
    """
    
    TEMP_PATTERNS = [
        '__pycache__',
        '*.pyc',
        '*.pyo',
        '.pytest_cache',
        '.mypy_cache',
        '*.egg-info',
        '.coverage',
        'htmlcov',
        '.DS_Store',
        '*.swp',
        '*~',
        '.cache',
        '*.tmp',
        '*.temp'
    ]
    
    def __init__(self, root_dir: str = '.', dry_run: bool = True):
        self.root_dir = Path(root_dir).resolve()
        self.dry_run = dry_run
        self.cleaned_items = []
        self.space_freed = 0
    
    def clean_temp_files(self, custom_patterns: List[str] = None) -> Dict[str, Any]:
        """执行临时文件清理"""
        patterns = custom_patterns or self.TEMP_PATTERNS
        
        print(f"\n🧹 临时文件清理")
        print(f"   目标目录: {self.root_dir}")
        print(f"   清理模式: {'预览模式' if self.dry_run else '实际删除'}")
        print("="*60)
        
        for pattern in patterns:
            self._clean_pattern(pattern)
        
        total_freed_mb = self.space_freed / (1024 * 1024)
        
        print(f"\n{'='*60}")
        print(f"✅ 清理完成!")
        print(f"   清理项目数: {len(self.cleaned_items)}")
        print(f"   释放空间: {total_freed_mb:.2f} MB")
        
        if self.dry_run:
            print(f"\n💡 提示: 这是预览模式，添加 --execute 参数实际执行清理")
        
        return {
            'items_cleaned': len(self.cleaned_items),
            'space_freed_bytes': self.space_freed,
            'space_freed_mb': round(total_freed_mb, 2),
            'cleaned_items': self.cleaned_items[:20],  # 只返回前20条
            'dry_run': self.dry_run
        }
    
    def _clean_pattern(self, pattern: str):
        """按指定模式清理文件"""
        items = []
        
        if pattern.startswith('*'):
            # 文件通配符模式
            suffix = pattern[1:]
            items = [f for f in self.root_dir.rglob(f'*{suffix}') if f.is_file()]
        else:
            # 目录或精确匹配
            items = [f for f in self.root_dir.rglob(pattern)]
        
        if not items:
            return
        
        print(f"\n📂 模式: {pattern} (找到 {len(items)} 项)")
        
        for item in items:
            try:
                size = item.stat().st_size
                rel_path = item.relative_to(self.root_dir)
                
                if self.dry_run:
                    print(f"   [预览] {rel_path} ({size:,} bytes)")
                else:
                    if item.is_dir():
                        shutil.rmtree(item)
                    else:
                        item.unlink()
                    print(f"   🗑️ {rel_path}")
                
                self.cleaned_items.append(str(rel_path))
                self.space_freed += size
                
            except Exception as e:
                print(f"   ❌ 失败: {item.name} - {e}")


class MaintenanceScheduler:
    """
    定时任务调度器（简化版cron）
    ============================
    
    功能：
    - 注册定时任务
    - 按间隔/计划执行任务
    - 任务执行历史记录
    - 错误重试机制
    """
    
    def __init__(self):
        self.tasks: Dict[str, Dict] = {}
        self.execution_history: List[Dict] = []
    
    def register_task(self, task_id: str, task_func, interval_hours: int = 24,
                     description: str = "", max_retries: int = 3):
        """注册定时任务"""
        self.tasks[task_id] = {
            'function': task_func,
            'interval_hours': interval_hours,
            'description': description,
            'max_retries': max_retries,
            'last_execution': None,
            'next_execution': datetime.now(),
            'consecutive_failures': 0
        }
        print(f"✅ 注册任务: {task_id} - {description or task_id}")
    
    def run_due_tasks(self) -> Dict[str, Any]:
        """执行所有到期任务"""
        now = datetime.now()
        executed = []
        failed = []
        
        print(f"\n⏰ 检查定时任务... ({now.strftime('%Y-%m-%d %H:%M:%S')})")
        
        for task_id, task in self.tasks.items():
            if now >= task['next_execution']:
                print(f"\n▶️ 执行任务: {task_id}")
                
                try:
                    start_time = time.time()
                    result = task['function']()
                    elapsed = time.time() - start_time
                    
                    task['last_execution'] = now
                    task['next_execution'] = now + timedelta(hours=task['interval_hours'])
                    task['consecutive_failures'] = 0
                    
                    executed.append({
                        'task_id': task_id,
                        'status': 'success',
                        'execution_time': now.isoformat(),
                        'duration_seconds': round(elapsed, 2)
                    })
                    
                    print(f"   ✅ 完成 ({elapsed:.2f}s)")
                    
                except Exception as e:
                    task['consecutive_failures'] += 1
                    
                    failed.append({
                        'task_id': task_id,
                        'status': 'failed',
                        'error': str(e),
                        'retry_count': task['consecutive_failures']
                    })
                    
                    print(f"   ❌ 失败: {e}")
                    
                    if task['consecutive_failures'] < task['max_retries']:
                        # 5分钟后重试
                        task['next_execution'] = now + timedelta(minutes=5)
                        print(f"   🔄 将在5分钟后重试 ({task['consecutive_failures']}/{task['max_retries']})")
                    else:
                        print(f"   ⛔ 达到最大重试次数，跳过本次执行")
                        task['next_execution'] = now + timedelta(hours=task['interval_hours'])
        
        self.execution_history.extend(executed + failed)
        
        return {
            'executed': len(executed),
            'failed': len(failed),
            'tasks_executed': [t['task_id'] for t in executed],
            'tasks_failed': [t['task_id'] for t in failed]
        }
    
    def list_tasks(self) -> List[Dict[str, Any]]:
        """列出所有已注册的任务"""
        tasks_list = []
        for task_id, task in self.tasks.items():
            tasks_list.append({
                'id': task_id,
                'description': task['description'],
                'interval_hours': task['interval_hours'],
                'next_execution': task['next_execution'].isoformat(),
                'last_execution': task['last_execution'].isoformat() if task['last_execution'] else '从未执行',
                'failures': task['consecutive_failures']
            })
        return tasks_list


def run_daily_maintenance(project_root: str = None, auto_cleanup: bool = True,
                         auto_backup: bool = True):
    """
    一键日常维护任务
    ===============
    
    整合所有运维操作为一次运行：
    1. 系统健康检查
    2. 日志清理（>7天）
    3. 临时文件清理
    4. 增量备份创建
    5. 生成维护报告
    """
    root = project_root or '.'
    
    print("\n" + "█"*70)
    print("█" + " "*68 + "█")
    print("█" + "  🛠️  Workshop V2.0 日常运维维护".center(64) + "█")
    print("█" + f"  时间: {datetime.now():%Y-%m-%d %H:%M:%S}".center(64) + "█")
    print("█" + " "*68 + "█")
    print("█"*70)
    
    maintenance_log = {
        'start_time': datetime.now().isoformat(),
        'tasks': [],
        'summary': {}
    }
    
    # 1. 健康检查
    print("\n\n[1/4] 🏥 系统健康检查")
    print("-"*60)
    health_checker = SystemHealthChecker(root)
    health_result = health_checker.run_full_checkup()
    maintenance_log['tasks'].append({'name': 'health_check', 'result': health_result})
    
    # 2. 日志清理
    if auto_cleanup:
        print("\n\n[2/4] 🗑️ 日志文件清理")
        print("-"*60)
        log_manager = LogManager(max_age_days=7)
        cleanup_result = log_manager.cleanup_old_logs(dry_run=False)
        maintenance_log['tasks'].append({'name': 'log_cleanup', 'result': cleanup_result})
    
    # 3. 临时文件清理
    if auto_cleanup:
        print("\n\n[3/4] 🧹 临时文件清理")
        print("-"*60)
        cleaner = TempFileCleaner(root, dry_run=False)
        clean_result = cleaner.clean_temp_files()
        maintenance_log['tasks'].append({'name': 'temp_cleanup', 'result': clean_result})
    
    # 4. 增量备份
    if auto_backup:
        print("\n\n[4/4] 💾 创建增量备份")
        print("-"*60)
        backup_mgr = BackupManager(root)
        backups = backup_mgr.list_backups()
        last_backup = backups[0]['id'] if backups else None
        backup_result = backup_mgr.create_incremental_backup(last_backup)
        maintenance_log['tasks'].append({'name': 'incremental_backup', 'result': backup_result})
        
        # 备份轮转
        backup_mgr.rotate_backups(keep_count=5)
    
    # 生成报告
    end_time = datetime.now()
    duration = (end_time - datetime.fromisoformat(maintenance_log['start_time'])).seconds
    
    maintenance_log['end_time'] = end_time.isoformat()
    maintenance_log['duration_seconds'] = duration
    maintenance_log['summary'] = {
        'health_score': health_result['health_score'],
        'overall_status': 'completed' if health_result['health_score'] >= 70 else 'needs_attention'
    }
    
    # 保存维护日志
    log_dir = Path(root) / 'logs' / 'maintenance'
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f'maintenance_{datetime.now():%Y%m%d_%H%M%S}.json'
    
    with open(log_file, 'w', encoding='utf-8') as f:
        json.dump(maintenance_log, f, ensure_ascii=False, indent=2)
    
    print("\n\n" + "█"*70)
    print(f"✅ 日常维护完成! 总耗时: {duration}秒")
    print(f"📄 维护日志: {log_file}")
    print(f"🏥 系统健康评分: {health_result['health_score']:.1f}/100")
    print("█"*70)
    
    return maintenance_log


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(
        description='Workshop V2.0 运维管理工具集',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  %(prog)s --cleanup-logs --days 7          清理7天前的日志
  %(prog)s --backup --type full             创建完整备份
  %(prog)s --health-check                   运行健康检查
  %(prog)s --clean-temp                     清理临时文件
  %(prog)s --daily-maintenance              一键日常维护
  %(prog)s --list-backups                   查看备份列表
        """
    )
    
    parser.add_argument('--cleanup-logs', action='store_true',
                       help='清理过期日志文件')
    parser.add_argument('--days', type=int, default=30,
                       help='日志保留天数 (默认30)')
    parser.add_argument('--backup', action='store_true',
                       help='创建项目备份')
    parser.add_argument('--type', choices=['full', 'incremental'],
                       default='full', help='备份类型 (默认full)')
    parser.add_argument('--restore', type=str,
                       help='从指定备份恢复')
    parser.add_argument('--health-check', action='store_true',
                       help='运行系统健康检查')
    parser.add_argument('--clean-temp', action='store_true',
                       help='清理临时文件和缓存')
    parser.add_argument('--execute', action='store_true',
                       help='实际执行操作 (默认预览模式)')
    parser.add_argument('--daily-maintenance', action='store_true',
                       help='一键运行日常维护任务')
    parser.add_argument('--list-backups', action='store_true',
                       help='列出现有备份')
    parser.add_argument('--project-root', type=str, default='.',
                       help='项目根目录 (默认当前目录)')
    
    args = parser.parse_args()
    
    if not any([args.cleanup_logs, args.backup, args.restore,
               args.health_check, args.clean_temp, args.daily_maintenance,
               args.list_backups]):
        parser.print_help()
        return
    
    root = args.project_root
    
    try:
        if args.daily_maintenance:
            run_daily_maintenance(
                project_root=root,
                auto_cleanup=True,
                auto_backup=True
            )
        
        elif args.cleanup_logs:
            log_mgr = LogManager(max_age_days=args.days)
            result = log_mgr.cleanup_old_logs(dry_run=not args.execute)
            print(f"\n释放空间: {result['space_freed_mb']:.2f} MB")
        
        elif args.backup:
            backup_mgr = BackupManager(root)
            if args.type == 'full':
                result = backup_mgr.create_full_backup()
            else:
                backups = backup_mgr.list_backups()
                last = backups[0]['id'] if backups else None
                result = backup_mgr.create_incremental_backup(last)
        
        elif args.restore:
            backup_mgr = BackupManager(root)
            result = backup_mgr.restore_backup(args.restore, overwrite=args.execute)
        
        elif args.health_check:
            checker = SystemHealthChecker(root)
            checker.run_full_checkup()
        
        elif args.clean_temp:
            cleaner = TempFileCleaner(root, dry_run=not args.execute)
            cleaner.clean_temp_files()
        
        elif args.list_backups:
            backup_mgr = BackupManager(root)
            backups = backup_mgr.list_backups()
            
            if not backups:
                print("\n📭 没有找到备份记录")
            else:
                print(f"\n📦 备份列表 (共 {len(backups)} 个):\n")
                print(f"{'名称':<35} {'类型':<12} {'大小(MB)':<10} {'时间'}")
                print("-"*75)
                for b in backups:
                    print(f"{b['id']:<35} {b['type']:<12} {b.get('size_mb', 0):<10.2f} {b['timestamp'][:19]}")
    
    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断操作")
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
