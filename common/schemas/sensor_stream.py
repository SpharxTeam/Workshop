"""
传感器流模式定义

定义传感器配置和数据帧结构。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from commons.schemas.base import BaseSchema, Field, ValidationResult


class SensorType(Enum):
    """传感器类型"""
    RGB_CAMERA = "rgb_camera"
    DEPTH_CAMERA = "depth_camera"
    STEREO_CAMERA = "stereo_camera"
    LIDAR = "lidar"
    IMU = "imu"
    GPS = "gps"
    THERMAL = "thermal"


class SensorStatus(Enum):
    """传感器状态"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    READY = "ready"
    STREAMING = "streaming"
    ERROR = "error"


@dataclass
class SensorConfig:
    """传感器配置"""
    sensor_id: str
    sensor_type: str
    name: str = ""
    manufacturer: str = ""
    model: str = ""
    serial_number: str = ""
    resolution: Dict[str, int] = field(default_factory=lambda: {"width": 1920, "height": 1080})
    fps: float = 30.0
    exposure: Optional[float] = None
    gain: Optional[float] = None
    calibration: Dict[str, Any] = field(default_factory=dict)
    custom: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sensor_id": self.sensor_id,
            "sensor_type": self.sensor_type,
            "name": self.name,
            "manufacturer": self.manufacturer,
            "model": self.model,
            "serial_number": self.serial_number,
            "resolution": self.resolution,
            "fps": self.fps,
            "exposure": self.exposure,
            "gain": self.gain,
            "calibration": self.calibration,
            "custom": self.custom,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SensorConfig":
        return cls(
            sensor_id=data.get("sensor_id", ""),
            sensor_type=data.get("sensor_type", ""),
            name=data.get("name", ""),
            manufacturer=data.get("manufacturer", ""),
            model=data.get("model", ""),
            serial_number=data.get("serial_number", ""),
            resolution=data.get("resolution", {"width": 1920, "height": 1080}),
            fps=data.get("fps", 30.0),
            exposure=data.get("exposure"),
            gain=data.get("gain"),
            calibration=data.get("calibration", {}),
            custom=data.get("custom", {}),
        )


@dataclass
class SensorFrame:
    """传感器帧"""
    frame_id: str
    sensor_id: str
    timestamp: float
    frame_number: int
    data_path: Optional[str] = None
    data_format: str = "raw"
    data_size: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    checksum: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "frame_id": self.frame_id,
            "sensor_id": self.sensor_id,
            "timestamp": self.timestamp,
            "frame_number": self.frame_number,
            "data_path": self.data_path,
            "data_format": self.data_format,
            "data_size": self.data_size,
            "metadata": self.metadata,
            "checksum": self.checksum,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SensorFrame":
        return cls(
            frame_id=data.get("frame_id", ""),
            sensor_id=data.get("sensor_id", ""),
            timestamp=data.get("timestamp", 0.0),
            frame_number=data.get("frame_number", 0),
            data_path=data.get("data_path"),
            data_format=data.get("data_format", "raw"),
            data_size=data.get("data_size", 0),
            metadata=data.get("metadata", {}),
            checksum=data.get("checksum"),
        )


class SensorStreamSchema(BaseSchema):
    """传感器流模式"""

    def _setup_fields(self) -> None:
        self.add_field(Field(
            name="stream_id",
            field_type=str,
            required=True,
            description="流唯一标识符",
            pattern=r"^[a-zA-Z0-9_-]+$",
        ))

        self.add_field(Field(
            name="name",
            field_type=str,
            required=True,
            description="流名称",
            min_length=1,
            max_length=256,
        ))

        self.add_field(Field(
            name="sensor_type",
            field_type=str,
            required=True,
            description="传感器类型",
            choices=[t.value for t in SensorType],
        ))

        self.add_field(Field(
            name="status",
            field_type=str,
            required=False,
            default=SensorStatus.DISCONNECTED.value,
            description="流状态",
            choices=[s.value for s in SensorStatus],
        ))

        self.add_field(Field(
            name="fps",
            field_type=float,
            required=False,
            default=30.0,
            description="帧率",
            min_value=0.0,
            max_value=1000.0,
        ))

        self.add_field(Field(
            name="resolution",
            field_type=dict,
            required=False,
            default={"width": 1920, "height": 1080},
            description="分辨率",
        ))

        self.add_field(Field(
            name="encoding",
            field_type=str,
            required=False,
            default="raw",
            description="编码格式",
        ))

        self.add_field(Field(
            name="frames_count",
            field_type=int,
            required=False,
            default=0,
            description="帧数量",
            min_value=0,
        ))

        self.add_field(Field(
            name="duration_seconds",
            field_type=float,
            required=False,
            default=0.0,
            description="流时长（秒）",
            min_value=0.0,
        ))

        self.add_field(Field(
            name="config",
            field_type=dict,
            required=False,
            default={},
            description="传感器配置",
        ))

        self.add_field(Field(
            name="metadata",
            field_type=dict,
            required=False,
            default={},
            description="元数据",
        ))

        self.add_field(Field(
            name="frames",
            field_type=list,
            required=False,
            default=[],
            description="帧列表",
        ))

        self.add_field(Field(
            name="created_at",
            field_type=str,
            required=False,
            description="创建时间",
        ))

        self.add_field(Field(
            name="updated_at",
            field_type=str,
            required=False,
            description="更新时间",
        ))

    def validate(self, data: Dict[str, Any]) -> ValidationResult:
        result = super().validate(data)

        if result.is_valid and "config" in data:
            config = data["config"]
            if not isinstance(config, dict):
                result.add_error(
                    field="config",
                    message="配置必须是字典类型",
                    code="INVALID_CONFIG_TYPE",
                )
            elif "sensor_id" not in config:
                result.add_error(
                    field="config.sensor_id",
                    message="配置缺少 sensor_id 字段",
                    code="MISSING_SENSOR_ID",
                )

        if result.is_valid and "frames" in data:
            for i, frame in enumerate(data["frames"]):
                if not isinstance(frame, dict):
                    result.add_error(
                        field=f"frames[{i}]",
                        message=f"帧 {i} 必须是字典类型",
                        code="INVALID_FRAME_TYPE",
                    )
                elif "frame_id" not in frame:
                    result.add_error(
                        field=f"frames[{i}].frame_id",
                        message=f"帧 {i} 缺少 frame_id 字段",
                        code="MISSING_FRAME_ID",
                    )
                elif "sensor_id" not in frame:
                    result.add_error(
                        field=f"frames[{i}].sensor_id",
                        message=f"帧 {i} 缺少 sensor_id 字段",
                        code="MISSING_SENSOR_ID",
                    )

        return result
