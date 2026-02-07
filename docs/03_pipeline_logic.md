# 流水线执行逻辑详解

## 核心概念

Spharx Toolchain采用模块化的流水线架构，每个处理阶段都是独立的组件，通过统一的接口进行通信和数据传递。

## 执行流程

### 1. 流水线初始化
```python
# 流水线引擎初始化
engine = PipelineEngine(config)

# 注册处理阶段
engine.register_stage(InputValidationStage())
engine.register_stage(AutoAnnotationStage())
engine.register_stage(ProductAssemblyStage())
```

### 2. 数据流转机制
```
输入数据 → 阶段1 → 阶段2 → 阶段3 → ... → 输出产品
     ↓        ↓        ↓        ↓           ↓
  {input}  {result1} {result2} {result3}  {final}
```

### 3. 阶段执行生命周期

每个阶段遵循标准的执行生命周期：

```python
class PipelineStage:
    def __init__(self):
        self.enabled = True
        self.required = True
        
    def validate(self, input_data):
        """输入验证"""
        # 检查必需的数据是否存在
        # 验证数据格式和完整性
        pass
        
    def execute(self, input_data):
        """执行核心逻辑"""
        # 处理输入数据
        # 返回处理结果
        pass
        
    def cleanup(self):
        """清理资源"""
        # 释放临时文件
        # 关闭连接
        pass
```

## 阶段详细说明

### 00 输入验证阶段
```python
class InputValidationStage(PipelineStage):
    def validate(self, input_data):
        # 检查输入路径是否存在
        # 验证图像文件格式
        # 统计图像数量和质量
        pass
        
    def execute(self, input_data):
        return {
            'validated': True,
            'image_count': count,
            'valid_formats': formats,
            'total_size': size
        }
```

### 01 2D自动标注阶段
```python
class AutoAnnotationStage(PipelineStage):
    def execute(self, input_data):
        # 加载SAM模型
        # 批量处理图像
        # 生成边界框和掩码
        # 应用置信度过滤
        
        return {
            'annotations': {
                'boxes': [...],
                'masks': [...],
                'scores': [...]
            },
            'processing_stats': {...}
        }
```

### 02 2D产品打包阶段
```python
class ProductAssembly2DStage(PipelineStage):
    def execute(self, input_data):
        # 转换为COCO格式
        # 生成类别映射
        # 创建数据集结构
        # 验证输出完整性
        
        return {
            'coco_dataset': {...},
            'dataset_path': '/output/dataset',
            'format_version': '1.0'
        }
```

### 03 3D重建阶段
```python
class Reconstruction3DStage(PipelineStage):
    def execute(self, input_data):
        # 调用COLMAP进行特征提取
        # 执行图像匹配
        # 进行稀疏重建
        # 生成密集点云
        
        return {
            'point_cloud': {...},
            'cameras': [...],
            'reconstruction_metrics': {...}
        }
```

## 错误处理机制

### 1. 阶段级错误处理
```python
try:
    result = stage.execute(input_data)
except ValidationError as e:
    logger.error(f"Validation failed: {e}")
    if stage.required:
        raise
elif stage.enabled:
    # 记录警告但继续执行
    logger.warning(f"Stage {stage.name} failed but continuing")
```

### 2. 全局错误策略
```yaml
# pipeline_default.yaml
pipeline:
  continue_on_error: false  # 全局错误处理策略
  retry_attempts: 3         # 重试次数
  timeout_per_stage: 3600   # 阶段超时时间
```

## 并行处理支持

### 1. 批量处理
```python
def process_batch(self, image_batch):
    """批量处理图像"""
    with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
        futures = [
            executor.submit(self.process_single_image, img) 
            for img in image_batch
        ]
        results = [future.result() for future in futures]
    return results
```

### 2. GPU资源管理
```python
class GPUPool:
    def __init__(self, num_gpus):
        self.available_gpus = list(range(num_gpus))
        self.lock = threading.Lock()
        
    def acquire_gpu(self):
        with self.lock:
            if self.available_gpus:
                return self.available_gpus.pop()
            return None
            
    def release_gpu(self, gpu_id):
        with self.lock:
            self.available_gpus.append(gpu_id)
```

## 状态管理和监控

### 1. 执行状态跟踪
```python
class PipelineState:
    def __init__(self):
        self.stage_status = {}
        self.execution_time = {}
        self.resource_usage = {}
        
    def update_stage_status(self, stage_id, status, metrics=None):
        self.stage_status[stage_id] = {
            'status': status,  # running/success/failed
            'timestamp': time.time(),
            'metrics': metrics or {}
        }
```

### 2. 进度报告
```python
def generate_progress_report(self):
    return {
        'completed_stages': len([s for s in self.stages if s.status == 'success']),
        'total_stages': len(self.stages),
        'current_stage': self.current_stage.name,
        'estimated_time_remaining': self.calculate_eta(),
        'resource_utilization': self.get_resource_usage()
    }
```

## 配置驱动执行

### 1. 动态阶段配置
```yaml
# pipeline_default.yaml
stages:
  - id: "01_2d_annotation"
    enabled: true
    parameters:
      model_type: "sam_hq_vit_l"
      confidence_threshold: 0.8
      batch_size: 8
```

### 2. 条件执行逻辑
```python
def should_execute_stage(self, stage, input_data):
    # 基于输入数据决定是否执行阶段
    if stage.id == "03_3d_reconstruction":
        return input_data.get('enable_3d', False)
    return stage.enabled
```

## 性能优化策略

### 1. 缓存机制
```python
class ResultCache:
    def __init__(self, cache_dir):
        self.cache_dir = cache_dir
        self.cache = {}
        
    def get_cached_result(self, stage_id, input_hash):
        cache_key = f"{stage_id}_{input_hash}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        # 检查磁盘缓存...
```

### 2. 内存管理
```python
def optimize_memory_usage(self):
    # 及时释放不需要的大对象
    if hasattr(self, 'large_temp_data'):
        del self.large_temp_data
        gc.collect()
        
    # 使用生成器处理大数据集
    def process_large_dataset(self, dataset):
        for batch in self.batch_generator(dataset):
            yield self.process_batch(batch)
```

## 扩展机制

### 1. 自定义阶段开发
```python
class CustomProcessingStage(PipelineStage):
    def __init__(self, custom_param):
        super().__init__()
        self.custom_param = custom_param
        
    def execute(self, input_data):
        # 实现自定义处理逻辑
        result = self.custom_processing(input_data)
        return {'custom_result': result}
```

### 2. 插件注册
```python
# 在配置文件中注册自定义阶段
pipeline:
  custom_stages:
    - module: "my_custom_module.CustomStage"
      parameters:
        param1: value1
```

---
*最后更新: 2026-02-07*
*版本: 1.0*