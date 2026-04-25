"""
数据集模式定义

定义数据集的元数据和样本结构。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from commons.schemas.base import BaseSchema, Field, ValidationResult


class DatasetStatus(Enum):
    """数据集状态"""
    DRAFT = "draft"
    PROCESSING = "processing"
    READY = "ready"
    ARCHIVED = "archived"
    ERROR = "error"


class DatasetType(Enum):
    """数据集类型"""
    IMAGE = "image"
    VIDEO = "video"
    POINT_CLOUD = "point_cloud"
    DEPTH = "depth"
    MULTIMODAL = "multimodal"
    SYNTHETIC = "synthetic"


@dataclass
class DatasetMetadata:
    """数据集元数据"""
    name: str
    version: str = "1.0.0"
    description: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    author: str = ""
    tags: List[str] = field(default_factory=list)
    custom: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "author": self.author,
            "tags": self.tags,
            "custom": self.custom,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DatasetMetadata":
        return cls(
            name=data.get("name", ""),
            version=data.get("version", "1.0.0"),
            description=data.get("description", ""),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if "updated_at" in data else datetime.now(),
            author=data.get("author", ""),
            tags=data.get("tags", []),
            custom=data.get("custom", {}),
        )


@dataclass
class DataSample:
    """数据样本"""
    id: str
    file_path: str
    annotations: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    split: str = "train"
    checksum: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "file_path": self.file_path,
            "annotations": self.annotations,
            "metadata": self.metadata,
            "split": self.split,
            "checksum": self.checksum,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DataSample":
        return cls(
            id=data.get("id", ""),
            file_path=data.get("file_path", ""),
            annotations=data.get("annotations", {}),
            metadata=data.get("metadata", {}),
            split=data.get("split", "train"),
            checksum=data.get("checksum"),
        )


class DatasetSchema(BaseSchema):
    """数据集模式"""

    def _setup_fields(self) -> None:
        self.add_field(Field(
            name="id",
            field_type=str,
            required=True,
            description="数据集唯一标识符",
            pattern=r"^[a-zA-Z0-9_-]+$",
        ))

        self.add_field(Field(
            name="name",
            field_type=str,
            required=True,
            description="数据集名称",
            min_length=1,
            max_length=256,
        ))

        self.add_field(Field(
            name="type",
            field_type=str,
            required=True,
            description="数据集类型",
            choices=[t.value for t in DatasetType],
        ))

        self.add_field(Field(
            name="status",
            field_type=str,
            required=False,
            default=DatasetStatus.DRAFT.value,
            description="数据集状态",
            choices=[s.value for s in DatasetStatus],
        ))

        self.add_field(Field(
            name="version",
            field_type=str,
            required=False,
            default="1.0.0",
            description="数据集版本",
            pattern=r"^\d+\.\d+\.\d+$",
        ))

        self.add_field(Field(
            name="description",
            field_type=str,
            required=False,
            default="",
            description="数据集描述",
            max_length=4096,
        ))

        self.add_field(Field(
            name="samples_count",
            field_type=int,
            required=False,
            default=0,
            description="样本数量",
            min_value=0,
        ))

        self.add_field(Field(
            name="size_bytes",
            field_type=int,
            required=False,
            default=0,
            description="数据集大小（字节）",
            min_value=0,
        ))

        self.add_field(Field(
            name="metadata",
            field_type=dict,
            required=False,
            default={},
            description="元数据",
        ))

        self.add_field(Field(
            name="samples",
            field_type=list,
            required=False,
            default=[],
            description="样本列表",
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

        if result.is_valid and "samples" in data:
            for i, sample in enumerate(data["samples"]):
                if not isinstance(sample, dict):
                    result.add_error(
                        field=f"samples[{i}]",
                        message=f"样本 {i} 必须是字典类型",
                        code="INVALID_SAMPLE_TYPE",
                    )
                elif "id" not in sample:
                    result.add_error(
                        field=f"samples[{i}].id",
                        message=f"样本 {i} 缺少 id 字段",
                        code="MISSING_SAMPLE_ID",
                    )

        return result
