# 生产线开发指南

## 扩展新处理阶段

### 1. 创建阶段类

```python
# src/pipeline/stages/XX_custom_stage.py
from ..stage_base import PipelineStage
from typing import Dict, Any

class CustomProcessingStage(PipelineStage):
    """自定义处理阶段"""
    
    def __init__(self, custom_param: str = "default"):
        super().__init__(
            stage_id="XX_custom_stage",
            name="自定义处理阶段",
            description="处理特定任务的自定义阶段"
        )
        self.custom_param = custom_param
        
    def validate(self, input_data: Dict[str, Any]) -> bool:
        """验证输入数据"""
        # 检查必需的输入参数
        required_keys = ['input_path', 'some_config']
        for key in required_keys:
            if key not in input_data:
                raise ValueError(f"Missing required parameter: {key}")
        return True
        
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行核心处理逻辑"""
        self.validate(input_data)
        
        # 实际处理逻辑
        result = self._process_data(input_data)
        
        return {
            'custom_result': result,
            'processing_time': self.get_timestamp(),
            'stage_metadata': self.get_metadata()
        }
        
    def _process_data(self, input_data: Dict[str, Any]) -> Any:
        """具体的处理实现"""
        # 在这里实现你的处理逻辑
        pass
```

### 2. 注册新阶段

在配置文件中注册：
```yaml
# config/pipeline_default.yaml
pipeline:
  stages:
    - id: "XX_custom_stage"
      name: "自定义处理阶段"
      module: "src.pipeline.stages.XX_custom_stage"
      enabled: true
      required: false
      parameters:
        custom_param: "specific_value"
```

### 3. 在主程序中使用
```python
# src/main.py
from src.pipeline.stages.XX_custom_stage import CustomProcessingStage

def main():
    # 创建流水线引擎
    engine = PipelineEngine(config)
    
    # 注册自定义阶段
    engine.register_stage(CustomProcessingStage(custom_param="value"))
    
    # 执行流水线
    result = engine.execute(input_data)
```

## 集成新的外部服务

### 1. 创建服务封装

```python
# src/services/custom_service.py
import requests
from typing import Dict, Any, Optional

class CustomServiceClient:
    """自定义服务客户端"""
    
    def __init__(self, api_url: str, api_key: str):
        self.api_url = api_url.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        })
        
    def process_image(self, image_path: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """处理单张图像"""
        with open(image_path, 'rb') as f:
            files = {'image': f}
            response = self.session.post(
                f"{self.api_url}/process",
                files=files,
                data={'parameters': json.dumps(parameters)}
            )
        response.raise_for_status()
        return response.json()
        
    def batch_process(self, image_paths: list, parameters: Dict[str, Any]) -> list:
        """批量处理"""
        results = []
        for image_path in image_paths:
            result = self.process_image(image_path, parameters)
            results.append(result)
        return results
```

### 2. 创建服务阶段包装器

```python
# src/pipeline/stages/service_wrapper_stage.py
from ..stage_base import PipelineStage
from src.services.custom_service import CustomServiceClient

class ServiceWrapperStage(PipelineStage):
    """服务封装阶段"""
    
    def __init__(self, service_config: Dict[str, Any]):
        super().__init__(
            stage_id="service_wrapper",
            name="服务封装阶段",
            description="封装外部服务的处理阶段"
        )
        self.service = CustomServiceClient(
            service_config['api_url'],
            service_config['api_key']
        )
        self.parameters = service_config.get('parameters', {})
        
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行服务调用"""
        image_paths = input_data['image_paths']
        results = self.service.batch_process(image_paths, self.parameters)
        
        return {
            'service_results': results,
            'processed_count': len(results),
            'service_metadata': {
                'api_version': '1.0',
                'processing_time': self.get_timestamp()
            }
        }
```

## 开发新的产品类型

### 1. 继承产品基类

```python
# src/products/custom_product.py
from .base import BaseProduct
from typing import Dict, Any
import json

class CustomProduct(BaseProduct):
    """自定义产品类型"""
    
    def __init__(self, name: str, version: str, output_path: str, schema: Dict[str, Any]):
        super().__init__(name, version, output_path)
        self.schema = schema
        
    def validate(self, data: Dict[str, Any]) -> bool:
        """验证产品数据格式"""
        # 实现数据验证逻辑
        # 可以使用JSON Schema验证
        try:
            jsonschema.validate(data, self.schema)
            return True
        except jsonschema.ValidationError as e:
            raise ValueError(f"Data validation failed: {e}")
            
    def export(self, data: Dict[str, Any]) -> str:
        """导出产品数据"""
        self.validate(data)
        
        # 创建输出目录
        output_dir = self._create_output_directory()
        
        # 导出数据文件
        data_file = f"{output_dir}/data.json"
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
        # 生成元数据
        metadata = self.get_metadata()
        metadata_file = f"{output_dir}/metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
            
        return output_dir
```

### 2. 定义产品Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "header": {
      "type": "object",
      "properties": {
        "product_type": {"type": "string"},
        "version": {"type": "string"},
        "generated_at": {"type": "string", "format": "date-time"}
      },
      "required": ["product_type", "version"]
    },
    "content": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id": {"type": "string"},
          "data": {"type": "object"}
        },
        "required": ["id", "data"]
      }
    }
  },
  "required": ["header", "content"]
}
```

## 配置管理系统扩展

### 1. 添加新的配置选项

```python
# src/utils/config_manager.py
class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_files: list):
        self.config = {}
        for config_file in config_files:
            self._load_config_file(config_file)
            
    def _load_config_file(self, config_file: str):
        """加载配置文件"""
        if config_file.endswith('.yaml'):
            self._load_yaml_config(config_file)
        elif config_file.endswith('.json'):
            self._load_json_config(config_file)
        elif config_file.endswith('.ini'):
            self._load_ini_config(config_file)
            
    def get_stage_config(self, stage_id: str) -> Dict[str, Any]:
        """获取特定阶段的配置"""
        return self.config.get('pipeline', {}).get('stages', {}).get(stage_id, {})
        
    def validate_config(self) -> bool:
        """验证配置完整性"""
        required_sections = ['pipeline', 'io', 'logging']
        for section in required_sections:
            if section not in self.config:
                raise ValueError(f"Missing required configuration section: {section}")
        return True
```

## 测试框架扩展

### 1. 创建阶段测试

```python
# tests/test_custom_stage.py
import pytest
from src.pipeline.stages.custom_stage import CustomProcessingStage

class TestCustomProcessingStage:
    """自定义阶段测试"""
    
    @pytest.fixture
    def stage(self):
        return CustomProcessingStage(custom_param="test_value")
        
    @pytest.fixture
    def sample_input(self):
        return {
            'input_path': '/test/data',
            'some_config': 'value'
        }
        
    def test_initialization(self, stage):
        """测试阶段初始化"""
        assert stage.stage_id == "XX_custom_stage"
        assert stage.name == "自定义处理阶段"
        assert stage.custom_param == "test_value"
        
    def test_validation_success(self, stage, sample_input):
        """测试输入验证成功"""
        assert stage.validate(sample_input) is True
        
    def test_validation_failure(self, stage):
        """测试输入验证失败"""
        with pytest.raises(ValueError):
            stage.validate({'missing_required': True})
            
    def test_execution(self, stage, sample_input):
        """测试阶段执行"""
        result = stage.execute(sample_input)
        assert 'custom_result' in result
        assert 'processing_time' in result
```

### 2. 集成测试

```python
# tests/test_integration.py
import pytest
from src.pipeline.engine import PipelineEngine
from src.pipeline.stages import *

class TestPipelineIntegration:
    """流水线集成测试"""
    
    @pytest.fixture
    def pipeline_engine(self, sample_config):
        engine = PipelineEngine(sample_config)
        # 注册测试阶段
        engine.register_stage(InputValidationStage())
        engine.register_stage(CustomProcessingStage())
        return engine
        
    def test_complete_pipeline(self, pipeline_engine, sample_input_data):
        """测试完整流水线执行"""
        result = pipeline_engine.execute(sample_input_data)
        
        # 验证输出
        assert 'validation_result' in result
        assert 'custom_result' in result
        assert result['status'] == 'success'
```

## 性能监控扩展

### 1. 添加性能指标收集

```python
# src/utils/performance_monitor.py
import time
import psutil
from typing import Dict, Any

class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        self.metrics = {}
        self.start_time = time.time()
        
    def record_stage_performance(self, stage_id: str, execution_time: float, memory_used: int):
        """记录阶段性能指标"""
        self.metrics[stage_id] = {
            'execution_time': execution_time,
            'memory_used': memory_used,
            'cpu_percent': psutil.cpu_percent(),
            'timestamp': time.time()
        }
        
    def get_system_metrics(self) -> Dict[str, Any]:
        """获取系统级指标"""
        return {
            'cpu_percent': psutil.cpu_percent(),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_usage': psutil.disk_usage('/').percent,
            'network_io': psutil.net_io_counters()._asdict()
        }
        
    def generate_performance_report(self) -> Dict[str, Any]:
        """生成性能报告"""
        return {
            'stage_metrics': self.metrics,
            'system_metrics': self.get_system_metrics(),
            'total_execution_time': time.time() - self.start_time,
            'report_generated_at': time.time()
        }
```

## 日志系统扩展

### 1. 自定义日志处理器

```python
# src/utils/custom_logger.py
import logging
import json
from logging.handlers import RotatingFileHandler

class JSONFormatter(logging.Formatter):
    """JSON格式日志格式化器"""
    
    def format(self, record):
        log_entry = {
            'timestamp': self.formatTime(record),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
            
        return json.dumps(log_entry, ensure_ascii=False)

def setup_custom_logging(config_file: str):
    """设置自定义日志系统"""
    # 加载日志配置
    with open(config_file, 'r') as f:
        log_config = yaml.safe_load(f)
    
    # 应用配置
    logging.config.dictConfig(log_config)
    
    # 添加自定义处理器
    json_handler = RotatingFileHandler(
        'logs/application.json',
        maxBytes=10*1024*1024,
        backupCount=5
    )
    json_handler.setFormatter(JSONFormatter())
    
    root_logger = logging.getLogger()
    root_logger.addHandler(json_handler)
```

## 部署脚本扩展

### 1. 创建自定义部署脚本

```bash
#!/bin/bash
# scripts/deploy_custom_service.sh

set -e

SERVICE_NAME="custom-service"
SERVICE_PORT=${CUSTOM_SERVICE_PORT:-8081}
DOCKER_IMAGE="spharx/custom-service:latest"

echo "部署自定义服务: $SERVICE_NAME"

# 构建Docker镜像
echo "构建Docker镜像..."
docker build -t $DOCKER_IMAGE -f docker/custom-service.Dockerfile .

# 停止现有服务
echo "停止现有服务..."
docker stop $SERVICE_NAME 2>/dev/null || true
docker rm $SERVICE_NAME 2>/dev/null || true

# 启动新服务
echo "启动服务..."
docker run -d \
  --name $SERVICE_NAME \
  --restart unless-stopped \
  -p $SERVICE_PORT:8000 \
  -v /workspace/data:/app/data \
  -e CUSTOM_PARAM="$CUSTOM_PARAM" \
  $DOCKER_IMAGE

# 等待服务启动
echo "等待服务启动..."
sleep 10

# 健康检查
echo "执行健康检查..."
if curl -f http://localhost:$SERVICE_PORT/health; then
    echo "✅ 服务部署成功"
else
    echo "❌ 服务部署失败"
    exit 1
fi
```

## 最佳实践建议

### 1. 代码组织
- 遵循单一职责原则
- 使用类型提示提高代码可读性
- 实现适当的错误处理和日志记录

### 2. 配置管理
- 使用环境变量管理敏感信息
- 提供合理的默认配置
- 实现配置验证机制

### 3. 测试策略
- 编写单元测试覆盖核心逻辑
- 实现集成测试验证组件协作
- 使用测试数据和模拟对象

### 4. 文档维护
- 保持代码注释和文档同步
- 提供清晰的使用示例
- 记录API变化和迁移指南

---
*最后更新: 2026-02-07*
*版本: 1.0*