# 模型预加载功能实现总结

## 功能概述

在 `main.py` 启动时增加了去重模型的检测和预加载功能，确保在启用去重功能时，模型能够正确加载。

## 实现的功能

### 1. 模型存在性检测

在 `deduplication.py` 中新增了以下函数：

- `check_model_exists(model_name)`: 检查模型是否存在（本地路径或HuggingFace缓存）
- `download_model(model_name)`: 下载模型（如果不存在）
- `ensure_model_available(model_name)`: 确保模型可用（检查存在性，如不存在则下载）

### 2. 启动时模型预检测

在 `main.py` 的 `AnalyzeAgent.initialize()` 方法中增加了：

```python
# 检测和初始化去重器
dedup_config = self.config.get_deduplication_config()
if dedup_config.get('enabled', False):
    logger.info("检测消息去重配置...")
    
    # 获取模型名称
    model_name = dedup_config.get('model_name', 'BAAI/bge-m3')
    logger.info(f"去重模型: {model_name}")
    
    # 检查并确保模型可用
    logger.info("检查去重模型可用性...")
    model_available = await ensure_model_available(model_name)
    
    if not model_available:
        logger.error(f"去重模型不可用: {model_name}")
        logger.error("请检查网络连接或模型路径，或在配置中禁用去重功能")
        raise RuntimeError(f"去重模型不可用: {model_name}")
    
    # 初始化去重器（此时模型已确保可用）
    logger.info("初始化消息去重器...")
    self.deduplicator = await get_deduplicator(dedup_config)
    logger.info("消息去重器初始化完成")
```

### 3. 配置参数过滤

修复了 `get_deduplicator()` 函数，过滤掉不属于 `MessageDeduplicator` 构造函数的参数：

```python
# 过滤掉不属于MessageDeduplicator构造函数的参数
filtered_config = {k: v for k, v in config.items() 
                 if k in ['model_name', 'similarity_threshold', 'time_window_hours', 
                        'max_cache_size', 'cache_file']}
```

## 支持的模型配置格式

### 1. HuggingFace模型名称（推荐）
```yaml
deduplication:
  model_name: 'BAAI/bge-m3'  # 自动下载和缓存
```

### 2. 本地模型路径
```yaml
deduplication:
  model_name: '/path/to/your/model'  # 使用本地模型
```

### 3. 相对路径
```yaml
deduplication:
  model_name: './models/bge-m3'  # 相对路径
```

### 4. 使用huggingface-cli下载的模型
```bash
# 先下载模型
huggingface-cli download BAAI/bge-m3 --local-dir ./models/bge-m3

# 然后配置使用本地路径
deduplication:
  model_name: './models/bge-m3'
```

## 工作流程

1. **启动检测**：系统启动时检查去重配置是否启用
2. **模型检测**：如果启用，检查配置的模型是否存在
3. **自动下载**：如果是HuggingFace模型且不存在，自动下载
4. **预加载**：在初始化阶段就加载模型，避免首次使用时的延迟
5. **错误处理**：如果模型不可用，抛出明确的错误信息

## 测试功能

### 1. 模型检测测试
```bash
python3 test_model_detection.py
```

### 2. 启动过程测试
```bash
python3 test_startup.py
```

### 3. 完整功能测试
```bash
python3 test_deduplication.py
```

## 日志输出示例

```
2025-05-25 12:19:50,355 - main - INFO - 检测消息去重配置...
2025-05-25 12:19:50,355 - main - INFO - 去重模型: BAAI/bge-m3
2025-05-25 12:19:50,355 - main - INFO - 检查去重模型可用性...
2025-05-25 12:19:50,358 - deduplication - INFO - 找到缓存的HuggingFace模型: BAAI/bge-m3
2025-05-25 12:19:50,358 - main - INFO - 初始化消息去重器...
2025-05-25 12:19:50,358 - deduplication - INFO - 初始化消息去重器: model=BAAI/bge-m3, threshold=0.85, window=2h
2025-05-25 12:19:50,358 - deduplication - INFO - 开始加载句向量模型: BAAI/bge-m3
2025-05-25 12:19:55,945 - deduplication - INFO - 模型加载完成: 维度=1024, 耗时=5.59s
2025-05-25 12:19:55,945 - main - INFO - 消息去重器初始化完成
```

## 错误处理

如果模型不可用，系统会抛出明确的错误信息：

```
RuntimeError: 去重模型不可用: model_name
```

并提示用户：
- 检查网络连接
- 检查模型路径
- 或在配置中禁用去重功能

## 性能优化

- **异步下载**：模型下载在线程池中进行，避免阻塞主线程
- **缓存检测**：优先检查本地缓存，避免重复下载
- **预加载**：启动时加载模型，避免首次使用时的延迟
- **错误快速失败**：模型不可用时立即报错，避免后续处理失败 