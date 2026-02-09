# SPHARX API 文档

## 📡 API概述

SPHARX Toolchain提供RESTful API接口，支持流水线任务管理、数据处理和状态查询。

## 🔐 认证

所有API请求需要JWT Token认证：

```bash
Authorization: Bearer <your-jwt-token>
```

## 🔄 流水线API

### 1. 提交任务

**POST** `/api/v1/pipelines/submit`

提交新的数据处理任务。

**请求体**：
```json
{
  "pipeline_type": "full",  // full, 2d_only, 3d_only
  "input_path": "/data/input/images/",
  "output_path": "/data/output/dataset_001/",
  "config": {
    "sam_model": "vit_h",
    "colmap_preset": "exhaustive"
  }
}
```

**响应**：
```json
{
  "task_id": "task_1234567890abcdef",
  "status": "submitted",
  "created_at": "2024-01-15T10:30:00Z"
}
```

### 2. 查询任务状态

**GET** `/api/v1/pipelines/status/{task_id}`

查询指定任务的执行状态。

**响应**：
```json
{
  "task_id": "task_1234567890abcdef",
  "status": "running",
  "progress": 65,
  "current_stage": "03_3d_reconstruction",
  "stages": {
    "01_preprocess": "completed",
    "02_2d_annotation": "completed", 
    "03_3d_reconstruction": "running",
    "04_2d_to_3d_lifting": "pending",
    "05_physics_generation": "pending",
    "06_dataset_assembly": "pending"
  },
  "metrics": {
    "processed_images": 1250,
    "generated_meshes": 42,
    "estimated_time_remaining": "2h 15m"
  }
}
```

### 3. 获取任务结果

**GET** `/api/v1/pipelines/results/{task_id}`

获取任务执行结果和输出数据。

**响应**：
```json
{
  "task_id": "task_1234567890abcdef",
  "status": "completed",
  "output": {
    "dataset_path": "/data/output/dataset_001/",
    "statistics": {
      "total_objects": 156,
      "annotated_2d": 156,
      "reconstructed_3d": 142,
      "physics_enabled": 138
    },
    "files": [
      {
        "name": "annotations_2d.json",
        "size": "2.3MB",
        "checksum": "abc123..."
      },
      {
        "name": "meshes_3d.ply",
        "size": "15.7MB", 
        "checksum": "def456..."
      }
    ]
  }
}
```

## 📁 数据管理API

### 1. 上传数据

**POST** `/api/v1/data/upload`

上传待处理的数据文件。

**表单参数**：
- `file`: 数据文件（支持ZIP, JPG, PNG等）
- `dataset_name`: 数据集名称
- `description`: 描述信息

### 2. 列出数据集

**GET** `/api/v1/data/datasets`

获取所有数据集列表。

**响应**：
```json
{
  "datasets": [
    {
      "id": "ds_001",
      "name": "indoor_scenes",
      "description": "室内场景数据集",
      "created_at": "2024-01-10T09:15:00Z",
      "file_count": 2450,
      "total_size": "12.5GB"
    }
  ]
}
```

## ⚙️ 配置API

### 1. 获取配置模板

**GET** `/api/v1/config/templates`

获取可用的配置模板。

**响应**：
```json
{
  "templates": [
    {
      "name": "standard_2d",
      "description": "标准2D处理配置",
      "parameters": {
        "image_size": "1024x1024",
        "sam_model": "vit_h",
        "batch_size": 8
      }
    }
  ]
}
```

### 2. 更新系统配置

**PUT** `/api/v1/config/system`

更新系统级配置。

## 📊 监控API

### 1. 系统状态

**GET** `/api/v1/monitoring/status`

获取系统整体状态。

**响应**：
```json
{
  "system": {
    "cpu_usage": 45.2,
    "memory_usage": 68.7,
    "gpu_usage": 72.1,
    "disk_usage": 34.5
  },
  "services": {
    "api": "healthy",
    "cvat": "healthy", 
    "colmap": "healthy",
    "database": "healthy"
  },
  "queues": {
    "pending_tasks": 3,
    "active_workers": 4
  }
}
```

### 2. 性能指标

**GET** `/api/v1/monitoring/metrics`

获取详细的性能指标。

## 🔧 工具API

### 1. 健康检查

**GET** `/api/health`

简单的健康检查端点。

**响应**：
```json
{
  "status": "ok",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### 2. 版本信息

**GET** `/api/version`

获取API版本信息。

## 📞 错误处理

### 错误响应格式

```json
{
  "error": {
    "code": "INVALID_INPUT",
    "message": "输入参数验证失败",
    "details": {
      "field": "pipeline_type",
      "reason": "必须是 'full', '2d_only' 或 '3d_only'"
    }
  }
}
```

### 常见错误码

| 错误码 | 说明 |
|--------|------|
| INVALID_INPUT | 输入参数验证失败 |
| TASK_NOT_FOUND | 任务不存在 |
| SERVICE_UNAVAILABLE | 服务不可用 |
| INSUFFICIENT_RESOURCES | 资源不足 |
| AUTHENTICATION_FAILED | 认证失败 |

## 📱 SDK客户端

### Python客户端示例

```python
from spharx_client import SpharxClient

# 初始化客户端
client = SpharxClient(
    base_url="http://localhost:8000",
    api_key="your-api-key"
)

# 提交任务
task = client.submit_pipeline(
    pipeline_type="full",
    input_path="/data/input/my_dataset/",
    config={"sam_model": "vit_h"}
)

# 轮询任务状态
while True:
    status = client.get_task_status(task.task_id)
    print(f"进度: {status.progress}%")
    
    if status.status == "completed":
        break
    time.sleep(30)

# 获取结果
result = client.get_task_result(task.task_id)
print(f"输出路径: {result.output.dataset_path}")
```

### JavaScript客户端示例

```javascript
import { SpharxClient } from '@spharx/client';

const client = new SpharxClient({
  baseUrl: 'http://localhost:8000',
  apiKey: 'your-api-key'
});

// 提交任务
const task = await client.submitPipeline({
  pipelineType: 'full',
  inputPath: '/data/input/my_dataset/',
  config: { samModel: 'vit_h' }
});

// 监听任务进度
client.onTaskProgress(task.taskId, (progress) => {
  console.log(`进度: ${progress}%`);
});

// 获取最终结果
const result = await client.getTaskResult(task.taskId);
console.log('输出路径:', result.output.datasetPath);
```

---
*API版本: v1.0*  
*最后更新: 2024年*