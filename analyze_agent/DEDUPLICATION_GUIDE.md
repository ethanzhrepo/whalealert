# 消息去重功能使用指南

## 概述

消息去重模块使用语义向量技术对中英文混合的Telegram消息进行近重复检测，避免重复处理相似的新闻内容。

## 功能特性

- **语义相似度检测**: 使用BGE-M3模型进行中英文混合文本的向量化
- **高效索引**: 使用FAISS进行快速向量相似度搜索
- **时间窗口**: 只在指定时间窗口内检测重复（默认2小时）
- **可配置阈值**: 支持调整相似度阈值（默认0.85）
- **持久化缓存**: 支持缓存持久化，重启后保持去重状态
- **实时统计**: 提供详细的去重统计信息

## 配置说明

在 `config.yml` 中添加以下配置：

```yaml
# 消息去重配置
deduplication:
  enabled: true  # 是否启用消息去重
  model_name: 'BAAI/bge-m3'  # 句向量模型名称
  similarity_threshold: 0.85  # 相似度阈值 (0.0-1.0)
  time_window_hours: 2  # 时间窗口（小时）
  max_cache_size: 10000  # 最大缓存大小
  cache_file: 'message_cache.pkl'  # 缓存文件路径
```

### 配置参数说明

- `enabled`: 是否启用去重功能
- `model_name`: 句向量模型，支持以下格式：
  - HuggingFace模型名称：`BAAI/bge-m3`（推荐）
  - 本地模型路径：`/path/to/local/model`
  - 相对路径：`./models/bge-m3`
- `similarity_threshold`: 相似度阈值，范围0.0-1.0，越高越严格
- `time_window_hours`: 时间窗口，只在此时间内检测重复
- `max_cache_size`: 最大缓存消息数量
- `cache_file`: 缓存文件路径，支持持久化

#### 模型配置说明

**HuggingFace模型（推荐）：**
```yaml
deduplication:
  model_name: 'BAAI/bge-m3'  # 自动下载和缓存
```

**本地模型路径：**
```yaml
deduplication:
  model_name: '/path/to/your/model'  # 使用本地模型
```

**使用huggingface-cli下载的模型：**
```bash
# 先下载模型
huggingface-cli download BAAI/bge-m3 --local-dir ./models/bge-m3

# 然后配置使用本地路径
deduplication:
  model_name: './models/bge-m3'
```

## 安装依赖

### 方法1: 使用安装脚本（推荐）

```bash
# 完整安装（包含去重功能）
./setup.sh

# 跳过去重功能测试（如果网络较慢）
./setup.sh --skip-dedup-test
```

### 方法2: 手动安装

```bash
pip install sentence-transformers faiss-cpu numpy
```

## 使用方法

### 1. 基本使用

去重功能已集成到主程序中，启动时会自动初始化：

```bash
python main.py
```

### 2. 测试去重功能

运行测试脚本验证去重效果：

```bash
python test_deduplication.py
```

### 3. 测试模型检测

测试模型检测和下载功能：

```bash
python test_model_detection.py
```

### 4. 独立使用去重器

```python
from deduplication import MessageDeduplicator

# 创建去重器
deduplicator = MessageDeduplicator(
    model_name="BAAI/bge-m3",
    similarity_threshold=0.85,
    time_window_hours=2
)

# 初始化
await deduplicator.initialize()

# 检查消息是否重复
is_duplicate, similar_record, score = await deduplicator.check_duplicate(message_data)

if not is_duplicate:
    # 添加到缓存
    await deduplicator.add_message(message_data)
```

## 工作原理

### 1. 文本向量化

- 使用BGE-M3模型将中英文混合文本转换为语义向量
- 向量归一化后使用余弦相似度进行比较

### 2. 相似度检测

- 使用FAISS IndexFlatIP进行高效向量搜索
- 在时间窗口内搜索最相似的消息
- 相似度超过阈值则判定为重复

### 3. 缓存管理

- 维护消息记录和FAISS索引
- 定期清理过期消息
- 支持缓存持久化

## 性能优化

### 1. 模型选择

- **BGE-M3**: 推荐，支持中英文混合，效果好
- **BGE-Large**: 更高精度，但速度较慢
- **BGE-Base**: 平衡选择

### 2. 阈值调优

- **0.9+**: 非常严格，只检测几乎相同的消息
- **0.85**: 推荐值，检测语义相似的消息
- **0.8-**: 较宽松，可能误判

### 3. 缓存优化

- 合理设置时间窗口，避免缓存过大
- 定期清理过期记录
- 监控内存使用情况

## 日志和监控

### 1. 日志级别

- `INFO`: 重复消息检测结果
- `DEBUG`: 详细的处理过程
- `ERROR`: 错误信息

### 2. 统计信息

```python
stats = deduplicator.get_stats()
print(f"总消息: {stats['total_messages']}")
print(f"重复消息: {stats['duplicates_found']}")
print(f"缓存大小: {stats['cache_size']}")
```

### 3. 通知消息

系统会发送以下类型的通知：

- `messages.duplicate`: 重复消息通知
- `messages.notification`: 包含去重统计的分析结果

## 故障排除

### 1. 模型加载失败

```
错误: 模型加载失败
解决: 检查网络连接，确保能下载HuggingFace模型
```

### 2. 内存不足

```
错误: FAISS索引操作失败
解决: 减少max_cache_size或增加系统内存
```

### 3. 缓存文件损坏

```
错误: 缓存加载失败
解决: 删除缓存文件，重新开始
```

### 4. Keras 3兼容性问题

```
错误: Your currently installed version of Keras is Keras 3, but this is not yet supported in Transformers
解决方案:
1. 运行修复脚本: python3 fix_keras_compatibility.py
2. 手动安装: pip install tf-keras
3. 或降级Keras: pip install keras==2.15.0
```

**详细说明:**
- 当前版本的transformers库还不完全支持Keras 3
- 安装tf-keras包可以提供向后兼容性
- 这是一个已知的兼容性问题，未来版本会修复

## 最佳实践

### 1. 配置建议

- 生产环境使用0.85阈值
- 时间窗口设置为1-4小时
- 缓存大小根据消息量调整

### 2. 监控建议

- 定期检查去重统计
- 监控缓存文件大小
- 关注模型加载时间

### 3. 维护建议

- 定期备份缓存文件
- 监控磁盘空间使用
- 根据效果调整阈值

## 示例场景

### 1. 币圈新闻去重

```
原消息: "Binance 将上线新币 DOGE/USDT Trading Pair"
相似消息: "币安即将推出 DOGE/USDT 交易对"
相似度: 0.87 > 0.85 → 判定为重复
```

### 2. 中英文混合

```
原消息: "Bitcoin price reaches $50,000"
相似消息: "比特币价格达到5万美元"
相似度: 0.82 < 0.85 → 判定为不重复
```

## 扩展功能

### 1. 自定义模型

可以替换为其他句向量模型：

```python
deduplicator = MessageDeduplicator(
    model_name="your-custom-model"
)
```

### 2. 多语言支持

BGE-M3支持多种语言，可以处理其他语言的消息。

### 3. 集群部署

可以使用Redis等外部存储替换本地缓存，支持多实例部署。 