"""
数据导出服务

提供数据导出、格式转换等功能。
"""

from __future__ import annotations

import csv
import io
import json
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union


class ExportFormat(Enum):
    """导出格式"""
    JSON = auto()
    CSV = auto()
    XML = auto()
    YAML = auto()
    PARQUET = auto()
    EXCEL = auto()
    HDF5 = auto()


@dataclass
class ExportConfig:
    """导出配置"""
    format: ExportFormat
    output_path: Optional[Union[str, Path]] = None
    include_headers: bool = True
    include_metadata: bool = True
    pretty_print: bool = False
    encoding: str = "utf-8"
    delimiter: str = ","
    sheet_name: str = "Sheet1"
    compression: Optional[str] = None
    custom_options: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExportResult:
    """导出结果"""
    success: bool
    format: ExportFormat
    output_path: Optional[str] = None
    data: Optional[bytes] = None
    records_count: int = 0
    size_bytes: int = 0
    duration_ms: float = 0.0
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "format": self.format.name,
            "output_path": self.output_path,
            "records_count": self.records_count,
            "size_bytes": self.size_bytes,
            "duration_ms": self.duration_ms,
            "error": self.error,
            "metadata": self.metadata,
        }


class Exporter:
    """数据导出服务"""

    _instance: Optional[Exporter] = None
    _lock = threading.Lock()

    def __new__(cls) -> Exporter:
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._formatters: Dict[ExportFormat, Callable] = {
            ExportFormat.JSON: self._format_json,
            ExportFormat.CSV: self._format_csv,
            ExportFormat.XML: self._format_xml,
            ExportFormat.YAML: self._format_yaml,
        }
        self._initialized = True

    def register_formatter(
        self,
        format: ExportFormat,
        formatter: Callable[[List[Dict[str, Any]], ExportConfig], bytes],
    ) -> None:
        self._formatters[format] = formatter

    def export(
        self,
        data: List[Dict[str, Any]],
        config: ExportConfig,
    ) -> ExportResult:
        start_time = time.time()

        try:
            formatter = self._formatters.get(config.format)
            if formatter is None:
                return ExportResult(
                    success=False,
                    format=config.format,
                    error=f"不支持的导出格式: {config.format.name}",
                )

            output_bytes = formatter(data, config)
            size_bytes = len(output_bytes)

            if config.output_path:
                output_path = Path(config.output_path)
                output_path.parent.mkdir(parents=True, exist_ok=True)

                with open(output_path, "wb") as f:
                    f.write(output_bytes)

            duration_ms = (time.time() - start_time) * 1000

            return ExportResult(
                success=True,
                format=config.format,
                output_path=str(config.output_path) if config.output_path else None,
                data=output_bytes if not config.output_path else None,
                records_count=len(data),
                size_bytes=size_bytes,
                duration_ms=duration_ms,
                metadata={
                    "encoding": config.encoding,
                    "compression": config.compression,
                },
            )

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return ExportResult(
                success=False,
                format=config.format,
                error=str(e),
                duration_ms=duration_ms,
            )

    def export_json(
        self,
        data: List[Dict[str, Any]],
        output_path: Optional[Union[str, Path]] = None,
        pretty_print: bool = False,
    ) -> ExportResult:
        config = ExportConfig(
            format=ExportFormat.JSON,
            output_path=output_path,
            pretty_print=pretty_print,
        )
        return self.export(data, config)

    def export_csv(
        self,
        data: List[Dict[str, Any]],
        output_path: Optional[Union[str, Path]] = None,
        delimiter: str = ",",
        include_headers: bool = True,
    ) -> ExportResult:
        config = ExportConfig(
            format=ExportFormat.CSV,
            output_path=output_path,
            delimiter=delimiter,
            include_headers=include_headers,
        )
        return self.export(data, config)

    def _format_json(
        self,
        data: List[Dict[str, Any]],
        config: ExportConfig,
    ) -> bytes:
        indent = 2 if config.pretty_print else None
        json_str = json.dumps(
            data,
            ensure_ascii=False,
            indent=indent,
        )
        return json_str.encode(config.encoding)

    def _format_csv(
        self,
        data: List[Dict[str, Any]],
        config: ExportConfig,
    ) -> bytes:
        if not data:
            return b""

        output = io.StringIO()
        fieldnames = list(data[0].keys()) if data else []

        writer = csv.DictWriter(
            output,
            fieldnames=fieldnames,
            delimiter=config.delimiter,
        )

        if config.include_headers:
            writer.writeheader()

        for row in data:
            writer.writerow(row)

        return output.getvalue().encode(config.encoding)

    def _format_xml(
        self,
        data: List[Dict[str, Any]],
        config: ExportConfig,
    ) -> bytes:
        lines = ['<?xml version="1.0" encoding="utf-8"?>']
        lines.append("<records>")

        for record in data:
            lines.append("  <record>")
            for key, value in record.items():
                if value is None:
                    lines.append(f"    <{key}/>")
                elif isinstance(value, (dict, list)):
                    lines.append(f"    <{key}>{json.dumps(value)}</{key}>")
                else:
                    escaped = str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                    lines.append(f"    <{key}>{escaped}</{key}>")
            lines.append("  </record>")

        lines.append("</records>")
        return "\n".join(lines).encode(config.encoding)

    def _format_yaml(
        self,
        data: List[Dict[str, Any]],
        config: ExportConfig,
    ) -> bytes:
        try:
            import yaml
            yaml_str = yaml.dump(
                data,
                allow_unicode=True,
                default_flow_style=False,
            )
            return yaml_str.encode(config.encoding)
        except ImportError:
            raise RuntimeError("需要安装 PyYAML 库: pip install pyyaml")

    def get_supported_formats(self) -> List[str]:
        return [f.name for f in self._formatters.keys()]

    def get_format_info(self, format: ExportFormat) -> Dict[str, Any]:
        info = {
            ExportFormat.JSON: {
                "name": "JSON",
                "extension": ".json",
                "mime_type": "application/json",
                "description": "JavaScript Object Notation",
            },
            ExportFormat.CSV: {
                "name": "CSV",
                "extension": ".csv",
                "mime_type": "text/csv",
                "description": "Comma-Separated Values",
            },
            ExportFormat.XML: {
                "name": "XML",
                "extension": ".xml",
                "mime_type": "application/xml",
                "description": "Extensible Markup Language",
            },
            ExportFormat.YAML: {
                "name": "YAML",
                "extension": ".yaml",
                "mime_type": "application/x-yaml",
                "description": "YAML Ain't Markup Language",
            },
        }
        return info.get(format, {})


def get_exporter() -> Exporter:
    return Exporter()
