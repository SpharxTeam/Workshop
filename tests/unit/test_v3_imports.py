"""
Workshop V3.0 模块导入验证测试

验证所有新模块可以正确导入。
"""

import pytest
import sys
from pathlib import Path


class TestCoreAbstractionsImport:
    """核心抽象层导入测试"""

    def test_import_pipeline(self):
        from workshop.core.abstractions.pipeline import (
            BasePipeline,
            PipelineResult,
            PipelineStatus,
            PipelineContext,
        )
        assert BasePipeline is not None
        assert PipelineResult is not None
        assert PipelineStatus is not None
        assert PipelineContext is not None

    def test_import_storage(self):
        from workshop.core.abstractions.storage import (
            IStorageBackend,
            LocalStorageBackend,
            FileMetadata,
            IOResult,
        )
        assert IStorageBackend is not None
        assert LocalStorageBackend is not None
        assert FileMetadata is not None
        assert IOResult is not None

    def test_import_device(self):
        from workshop.core.abstractions.device import (
            IHardwareDevice,
            DeviceInfo,
            DeviceStatus,
        )
        assert IHardwareDevice is not None
        assert DeviceInfo is not None
        assert DeviceStatus is not None

    def test_import_models(self):
        from workshop.core.abstractions.models import (
            ErrorCode,
            ErrorSeverity,
            WorkshopError,
            ConfigurationError,
            PipelineError,
            ValidationError,
            HardwareError,
            DataIOError,
        )
        assert ErrorCode is not None
        assert ErrorSeverity is not None
        assert WorkshopError is not None

    def test_import_abstractions_init(self):
        from workshop.core.abstractions import (
            BasePipeline,
            IStorageBackend,
            IHardwareDevice,
            ErrorCode,
        )
        assert BasePipeline is not None


class TestCoreServicesImport:
    """核心服务层导入测试"""

    def test_import_config_service(self):
        from workshop.core.services.config_service import (
            ConfigService,
            ConfigLoader,
            ConfigValidator,
        )
        assert ConfigService is not None
        assert ConfigLoader is not None
        assert ConfigValidator is not None

    def test_import_logging_service(self):
        from workshop.core.services.logging_service import (
            LoggingService,
            StructuredFormatter,
            SanitizingFilter,
        )
        assert LoggingService is not None
        assert StructuredFormatter is not None
        assert SanitizingFilter is not None

    def test_import_metrics_service(self):
        from workshop.core.services.metrics_service import (
            MetricsService,
            MetricsCollector,
            MetricsRegistry,
        )
        assert MetricsService is not None
        assert MetricsCollector is not None
        assert MetricsRegistry is not None

    def test_import_services_init(self):
        from workshop.core.services import (
            ConfigService,
            LoggingService,
            MetricsService,
        )
        assert ConfigService is not None


class TestCoreSecurityImport:
    """安全服务层导入测试"""

    def test_import_validation_service(self):
        from workshop.core.security.validation_service import (
            ValidationService,
            ValidationResult,
            FieldValidator,
            SchemaValidator,
            PathValidator,
            FileValidator,
        )
        assert ValidationService is not None
        assert ValidationResult is not None
        assert FieldValidator is not None

    def test_import_security_service(self):
        from workshop.core.security.security_service import (
            SecurityService,
            SecurityContext,
            SecurityAuditLog,
            Permission,
            Role,
            AuditLevel,
        )
        assert SecurityService is not None
        assert SecurityContext is not None
        assert Permission is not None

    def test_import_security_init(self):
        from workshop.core.security import (
            ValidationService,
            SecurityService,
            Permission,
        )
        assert ValidationService is not None


class TestCoreObservabilityImport:
    """可观测性层导入测试"""

    def test_import_tracing_service(self):
        from workshop.core.observability.tracing_service import (
            TracingService,
            Span,
            SpanContext,
            TraceContext,
        )
        assert TracingService is not None
        assert Span is not None
        assert SpanContext is not None

    def test_import_performance(self):
        from workshop.core.observability.performance import (
            PerformanceMonitor,
            PerformanceMetric,
            PerformanceThreshold,
            PerformanceAlert,
        )
        assert PerformanceMonitor is not None
        assert PerformanceMetric is not None
        assert PerformanceThreshold is not None

    def test_import_health_service(self):
        from workshop.core.observability.health_service import (
            HealthService,
            HealthStatus,
            HealthCheckResult,
            HealthCheckType,
        )
        assert HealthService is not None
        assert HealthStatus is not None
        assert HealthCheckResult is not None

    def test_import_observability_init(self):
        from workshop.core.observability import (
            TracingService,
            PerformanceMonitor,
            HealthService,
        )
        assert TracingService is not None


class TestCommonsImport:
    """通用层导入测试"""

    def test_import_utils_logging(self):
        from commons.utils.logging_utils import (
            get_logger,
            setup_logging,
            LoggerAdapter,
        )
        assert get_logger is not None
        assert setup_logging is not None

    def test_import_utils_decorators(self):
        from commons.utils.decorators import (
            retry,
            throttle,
            debounce,
            memoize,
            timed,
        )
        assert retry is not None
        assert throttle is not None
        assert debounce is not None

    def test_import_utils_data(self):
        from commons.utils.data_utils import (
            deep_merge,
            flatten_dict,
            safe_get,
            safe_set,
        )
        assert deep_merge is not None
        assert flatten_dict is not None
        assert safe_get is not None

    def test_import_utils_functional(self):
        from commons.utils.functional import (
            Singleton,
            Timer,
            RateLimiter,
            CircuitBreaker,
        )
        assert Singleton is not None
        assert Timer is not None
        assert RateLimiter is not None

    def test_import_schemas(self):
        from commons.schemas import (
            BaseSchema,
            DatasetSchema,
            SceneSchema,
            SensorStreamSchema,
        )
        assert BaseSchema is not None
        assert DatasetSchema is not None


class TestOrchestrationImport:
    """编排层导入测试"""

    def test_import_scheduler(self):
        from workshop.orchestration.scheduler import (
            Scheduler,
            ScheduledTask,
            ScheduleType,
            TaskPriority,
        )
        assert Scheduler is not None
        assert ScheduledTask is not None
        assert ScheduleType is not None

    def test_import_task_queue(self):
        from workshop.orchestration.task_queue import (
            TaskQueue,
            Task,
            TaskStatus,
            TaskResult,
            Worker,
        )
        assert TaskQueue is not None
        assert Task is not None
        assert TaskStatus is not None

    def test_import_workflow_engine(self):
        from workshop.orchestration.workflow_engine import (
            WorkflowEngine,
            Workflow,
            WorkflowStep,
            WorkflowStatus,
            WorkflowContext,
        )
        assert WorkflowEngine is not None
        assert Workflow is not None
        assert WorkflowStep is not None

    def test_import_orchestration_init(self):
        from workshop.orchestration import (
            Scheduler,
            TaskQueue,
            WorkflowEngine,
        )
        assert Scheduler is not None


class TestServicesImport:
    """服务层导入测试"""

    def test_import_gateway(self):
        from workshop.services.gateway import (
            Gateway,
            Route,
            RequestContext,
            Response,
            Middleware,
        )
        assert Gateway is not None
        assert Route is not None
        assert Response is not None

    def test_import_monitor(self):
        from workshop.services.monitor import (
            Monitor,
            MonitorTarget,
            MonitorStatus,
            Alert,
        )
        assert Monitor is not None
        assert MonitorTarget is not None
        assert MonitorStatus is not None

    def test_import_exporter(self):
        from workshop.services.exporter import (
            Exporter,
            ExportConfig,
            ExportFormat,
            ExportResult,
        )
        assert Exporter is not None
        assert ExportConfig is not None
        assert ExportFormat is not None

    def test_import_services_init(self):
        from workshop.services import (
            Gateway,
            Monitor,
            Exporter,
        )
        assert Gateway is not None


class TestBackwardCompatibility:
    """向后兼容层测试"""

    def test_common_core_import(self):
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            from common.core import BasePipeline, ConfigService
            assert BasePipeline is not None
            assert ConfigService is not None

    def test_common_schemas_import(self):
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            from common.schemas import DatasetSchema, SceneSchema
            assert DatasetSchema is not None
            assert SceneSchema is not None


class TestSingletonPattern:
    """单例模式测试"""

    def test_config_service_singleton(self):
        from workshop.core.services.config_service import ConfigService
        s1 = ConfigService()
        s2 = ConfigService()
        assert s1 is s2

    def test_logging_service_singleton(self):
        from workshop.core.services.logging_service import LoggingService
        s1 = LoggingService()
        s2 = LoggingService()
        assert s1 is s2

    def test_metrics_service_singleton(self):
        from workshop.core.services.metrics_service import MetricsService
        s1 = MetricsService()
        s2 = MetricsService()
        assert s1 is s2

    def test_security_service_singleton(self):
        from workshop.core.security.security_service import SecurityService
        s1 = SecurityService()
        s2 = SecurityService()
        assert s1 is s2

    def test_tracing_service_singleton(self):
        from workshop.core.observability.tracing_service import TracingService
        s1 = TracingService()
        s2 = TracingService()
        assert s1 is s2


class TestErrorCodeSystem:
    """错误码系统测试"""

    def test_error_code_values(self):
        from workshop.core.abstractions.models import ErrorCode

        assert ErrorCode.CONFIG_FILE_NOT_FOUND.value == 1001
        assert ErrorCode.PIPELINE_INIT_FAILED.value == 2001
        assert ErrorCode.VALIDATION_FAILED.value == 3001
        assert ErrorCode.HARDWARE_NOT_CONNECTED.value == 4001
        assert ErrorCode.IO_FILE_NOT_FOUND.value == 5001

    def test_error_severity(self):
        from workshop.core.abstractions.models import ErrorSeverity

        assert ErrorSeverity.LOW.value == 1
        assert ErrorSeverity.MEDIUM.value == 2
        assert ErrorSeverity.HIGH.value == 3
        assert ErrorSeverity.CRITICAL.value == 4

    def test_workshop_error(self):
        from workshop.core.abstractions.models import (
            WorkshopError,
            ErrorCode,
            ErrorSeverity,
        )

        error = WorkshopError(
            code=ErrorCode.CONFIG_FILE_NOT_FOUND,
            message="配置文件未找到",
            severity=ErrorSeverity.HIGH,
        )

        assert error.code == ErrorCode.CONFIG_FILE_NOT_FOUND
        assert error.message == "配置文件未找到"
        assert error.severity == ErrorSeverity.HIGH


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
