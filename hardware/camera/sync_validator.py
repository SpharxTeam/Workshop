"""
同步验证器
验证多相机系统的时间同步精度和数据一致性
"""

import time
import numpy as np
from typing import List, Dict, Tuple, Optional
import logging
from dataclasses import dataclass
from collections import deque

logger = logging.getLogger(__name__)


@dataclass
class FrameData:
    """帧数据结构"""
    camera_id: str
    timestamp: float
    frame_number: int
    data_hash: str


@dataclass
class SyncMetrics:
    """同步指标"""
    timestamp_diff_ms: float
    frame_number_diff: int
    hash_match_rate: float
    validation_timestamp: float


class SyncValidator:
    """同步验证器"""
    
    def __init__(self, window_size: int = 100):
        """
        初始化同步验证器
        
        Args:
            window_size: 验证窗口大小（帧数）
        """
        self.window_size = window_size
        self.frame_buffers: Dict[str, deque] = {}
        self.metrics_history: deque = deque(maxlen=1000)
        self.validation_enabled = True
        
    def add_frame(self, camera_id: str, timestamp: float, frame_number: int, 
                  frame_data: np.ndarray) -> bool:
        """
        添加帧数据用于验证
        
        Args:
            camera_id: 相机ID
            timestamp: 时间戳
            frame_number: 帧编号
            frame_data: 帧数据
            
        Returns:
            bool: 添加是否成功
        """
        if not self.validation_enabled:
            return True
            
        try:
            # 计算数据哈希
            data_hash = self._calculate_hash(frame_data)
            
            # 创建帧数据对象
            frame_obj = FrameData(camera_id, timestamp, frame_number, data_hash)
            
            # 初始化缓冲区
            if camera_id not in self.frame_buffers:
                self.frame_buffers[camera_id] = deque(maxlen=self.window_size)
            
            # 添加到缓冲区
            self.frame_buffers[camera_id].append(frame_obj)
            
            # 执行验证
            self._validate_sync()
            
            return True
            
        except Exception as e:
            logger.error(f"添加帧数据失败: {e}")
            return False
    
    def _calculate_hash(self, data: np.ndarray) -> str:
        """
        计算数据哈希值
        
        Args:
            data: 输入数据
            
        Returns:
            str: 哈希字符串
        """
        try:
            # 使用简单的统计特征作为哈希
            if data.size == 0:
                return "empty"
            
            mean_val = np.mean(data)
            std_val = np.std(data)
            hash_str = f"{mean_val:.6f}_{std_val:.6f}"
            return hash_str
        except Exception:
            return "error"
    
    def _validate_sync(self):
        """执行同步验证"""
        try:
            # 检查是否有足够的数据
            if len(self.frame_buffers) < 2:
                return
            
            # 获取最新的帧数据
            latest_frames = {}
            for camera_id, buffer in self.frame_buffers.items():
                if buffer:
                    latest_frames[camera_id] = buffer[-1]
            
            # 需要至少两个相机的数据
            if len(latest_frames) < 2:
                return
            
            # 计算同步指标
            metrics = self._calculate_metrics(list(latest_frames.values()))
            
            if metrics:
                self.metrics_history.append(metrics)
                self._log_validation_result(metrics)
                
        except Exception as e:
            logger.error(f"同步验证失败: {e}")
    
    def _calculate_metrics(self, frames: List[FrameData]) -> Optional[SyncMetrics]:
        """
        计算同步指标
        
        Args:
            frames: 帧数据列表
            
        Returns:
            SyncMetrics: 同步指标或None
        """
        if len(frames) < 2:
            return None
            
        try:
            # 计算时间戳差异
            timestamps = [frame.timestamp for frame in frames]
            timestamp_diff = max(timestamps) - min(timestamps)
            timestamp_diff_ms = timestamp_diff * 1000  # 转换为毫秒
            
            # 计算帧编号差异
            frame_numbers = [frame.frame_number for frame in frames]
            frame_number_diff = max(frame_numbers) - min(frame_numbers)
            
            # 计算哈希匹配率
            hashes = [frame.data_hash for frame in frames]
            unique_hashes = set(hashes)
            hash_match_rate = (len(hashes) - len(unique_hashes) + 1) / len(hashes)
            
            return SyncMetrics(
                timestamp_diff_ms=timestamp_diff_ms,
                frame_number_diff=frame_number_diff,
                hash_match_rate=hash_match_rate,
                validation_timestamp=time.time()
            )
            
        except Exception as e:
            logger.error(f"计算同步指标失败: {e}")
            return None
    
    def _log_validation_result(self, metrics: SyncMetrics):
        """
        记录验证结果
        
        Args:
            metrics: 同步指标
        """
        # 记录详细信息
        logger.debug(
            f"同步验证 - 时间差: {metrics.timestamp_diff_ms:.3f}ms, "
            f"帧差: {metrics.frame_number_diff}, "
            f"哈希匹配率: {metrics.hash_match_rate:.3f}"
        )
        
        # 记录警告信息
        if metrics.timestamp_diff_ms > 10:  # 超过10ms
            logger.warning(f"时间同步偏差较大: {metrics.timestamp_diff_ms:.3f}ms")
        
        if metrics.frame_number_diff > 1:  # 帧编号差异超过1
            logger.warning(f"帧编号不同步: 差异 {metrics.frame_number_diff}")
    
    def get_validation_report(self) -> Dict:
        """
        获取验证报告
        
        Returns:
            Dict: 验证报告
        """
        if not self.metrics_history:
            return {"status": "no_data"}
        
        # 计算统计数据
        timestamp_diffs = [m.timestamp_diff_ms for m in self.metrics_history]
        frame_diffs = [m.frame_number_diff for m in self.metrics_history]
        hash_rates = [m.hash_match_rate for m in self.metrics_history]
        
        return {
            "status": "active",
            "sample_count": len(self.metrics_history),
            "timestamp_sync": {
                "avg_diff_ms": float(np.mean(timestamp_diffs)),
                "max_diff_ms": float(np.max(timestamp_diffs)),
                "min_diff_ms": float(np.min(timestamp_diffs)),
                "std_diff_ms": float(np.std(timestamp_diffs))
            },
            "frame_sync": {
                "avg_diff": float(np.mean(frame_diffs)),
                "max_diff": int(np.max(frame_diffs)),
                "perfect_sync_rate": float(np.mean([1 if d == 0 else 0 for d in frame_diffs]))
            },
            "data_consistency": {
                "avg_hash_match_rate": float(np.mean(hash_rates)),
                "perfect_match_rate": float(np.mean([1 if r == 1.0 else 0 for r in hash_rates]))
            }
        }
    
    def enable_validation(self, enabled: bool):
        """
        启用/禁用验证
        
        Args:
            enabled: 是否启用验证
        """
        self.validation_enabled = enabled
        if enabled:
            logger.info("同步验证已启用")
        else:
            logger.info("同步验证已禁用")
    
    def clear_history(self):
        """清除历史数据"""
        self.metrics_history.clear()
        self.frame_buffers.clear()
        logger.info("验证历史数据已清除")


# 示例使用
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(level=logging.INFO)
    
    # 创建验证器
    validator = SyncValidator(window_size=50)
    
    # 模拟添加帧数据
    for i in range(100):
        # 模拟两个相机的数据
        cam1_data = np.random.randint(0, 255, (480, 640), dtype=np.uint8)
        cam2_data = np.random.randint(0, 255, (480, 640), dtype=np.uint8)
        
        timestamp = time.time()
        
        validator.add_frame("cam1", timestamp, i, cam1_data)
        validator.add_frame("cam2", timestamp + 0.001, i, cam2_data)  # 1ms延迟
        
        time.sleep(0.033)  # 模拟30fps
    
    # 输出验证报告
    report = validator.get_validation_report()
    print("验证报告:")
    for key, value in report.items():
        print(f"  {key}: {value}")