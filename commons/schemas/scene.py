"""
场景模式定义

定义场景的元数据和帧结构。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from commons.schemas.base import BaseSchema, Field, ValidationResult


class SceneType(Enum):
    """场景类型"""
    INDOOR = "indoor"
    OUTDOOR = "outdoor"
    LABORATORY = "laboratory"
    INDUSTRIAL = "industrial"
    SYNTHETIC = "synthetic"


class SceneStatus(Enum):
    """场景状态"""
    CAPTURING = "capturing"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


@dataclass
class SceneMetadata:
    """场景元数据"""
    scene_id: str
    name: str = ""
    location: str = ""
    capture_date: Optional[datetime] = None
    weather: str = ""
    lighting: str = ""
    notes: str = ""
    custom: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scene_id": self.scene_id,
            "name": self.name,
            "location": self.location,
            "capture_date": self.capture_date.isoformat() if self.capture_date else None,
            "weather": self.weather,
            "lighting": self.lighting,
            "notes": self.notes,
            "custom": self.custom,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SceneMetadata":
        return cls(
            scene_id=data.get("scene_id", ""),
            name=data.get("name", ""),
            location=data.get("location", ""),
            capture_date=datetime.fromisoformat(data["capture_date"]) if data.get("capture_date") else None,
            weather=data.get("weather", ""),
            lighting=data.get("lighting", ""),
            notes=data.get("notes", ""),
            custom=data.get("custom", {}),
        )


@dataclass
class SceneFrame:
    """场景帧"""
    frame_id: str
    timestamp: float
    frame_number: int
    image_path: Optional[str] = None
    depth_path: Optional[str] = None
    point_cloud_path: Optional[str] = None
    camera_pose: Optional[List[float]] = None
    intrinsics: Optional[Dict[str, Any]] = None
    annotations: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "frame_id": self.frame_id,
            "timestamp": self.timestamp,
            "frame_number": self.frame_number,
            "image_path": self.image_path,
            "depth_path": self.depth_path,
            "point_cloud_path": self.point_cloud_path,
            "camera_pose": self.camera_pose,
            "intrinsics": self.intrinsics,
            "annotations": self.annotations,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SceneFrame":
        return cls(
            frame_id=data.get("frame_id", ""),
            timestamp=data.get("timestamp", 0.0),
            frame_number=data.get("frame_number", 0),
            image_path=data.get("image_path"),
            depth_path=data.get("depth_path"),
            point_cloud_path=data.get("point_cloud_path"),
            camera_pose=data.get("camera_pose"),
            intrinsics=data.get("intrinsics"),
            annotations=data.get("annotations", {}),
            metadata=data.get("metadata", {}),
        )


class SceneSchema(BaseSchema):
    """场景模式"""

    def _setup_fields(self) -> None:
        self.add_field(Field(
            name="scene_id",
            field_type=str,
            required=True,
            description="场景唯一标识符",
            pattern=r"^[a-zA-Z0-9_-]+$",
        ))

        self.add_field(Field(
            name="name",
            field_type=str,
            required=True,
            description="场景名称",
            min_length=1,
            max_length=256,
        ))

        self.add_field(Field(
            name="type",
            field_type=str,
            required=False,
            default=SceneType.INDOOR.value,
            description="场景类型",
            choices=[t.value for t in SceneType],
        ))

        self.add_field(Field(
            name="status",
            field_type=str,
            required=False,
            default=SceneStatus.CAPTURING.value,
            description="场景状态",
            choices=[s.value for s in SceneStatus],
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
            description="场景时长（秒）",
            min_value=0.0,
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
            name="sensors",
            field_type=list,
            required=False,
            default=[],
            description="传感器列表",
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

        if result.is_valid and "resolution" in data:
            res = data["resolution"]
            if not isinstance(res, dict):
                result.add_error(
                    field="resolution",
                    message="分辨率必须是字典类型",
                    code="INVALID_RESOLUTION_TYPE",
                )
            elif "width" not in res or "height" not in res:
                result.add_error(
                    field="resolution",
                    message="分辨率必须包含 width 和 height 字段",
                    code="MISSING_RESOLUTION_FIELDS",
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

        return result
