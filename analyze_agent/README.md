# Analyze Agent - 多Agent消息分析系统

## 概述

Analyze Agent 是一个基于多Agent架构的消息分析系统，专门用于分析来自Telegram的加密货币相关消息。系统监听NATS消息队列，使用AI Agent对原始消息进行智能分析和加工。

## 功能特性

### 🤖 多Agent架构
- **可扩展设计**：支持添加多种分析Agent
- **情绪分析Agent**：分析币圈新闻的市场情绪
- **预留扩展**：价格分析、风险评估等Agent

### 🧠 多LLM支持
- **Ollama**：本地部署的开源模型
- **OpenAI**：GPT系列模型
- **Anthropic**：Claude系列模型
- **LangChain集成**：统一的LLM接口

### 🔄 智能消息去重
- **语义相似度检测**：使用BGE-M3模型进行中英文混合文本的向量化
- **高效索引**：使用FAISS进行快速向量相似度搜索
- **时间窗口**：只在指定时间窗口内检测重复（默认2小时）
- **可配置阈值**：支持调整相似度阈值（默认0.85）
- **持久化缓存**：支持缓存持久化，重启后保持去重状态

### 📡 消息处理
- **NATS监听**：实时监听消息队列
- **智能过滤**：只处理Telegram来源的消息
- **结构化输出**：标准化的JSON分析结果

## 系统架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  TelegramStream │───▶│   NATS Queue    │───▶│  Analyze Agent  │
│                 │    │ messages.stream │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
                                               ┌───────▼───────┐
                                               │  Agent Manager │
                                               └───────┬───────┘
                                                       │
                                    ┌──────────────────┼──────────────────┐
                                    │                  │                  │
                            ┌───────▼───────┐ ┌───────▼───────┐ ┌───────▼───────┐
                            │ Sentiment     │ │ Price Analysis│ │ Risk Assessment│
                            │ Analysis Agent│ │ Agent (Future)│ │ Agent (Future) │
                            └───────────────┘ └───────────────┘ └───────────────┘
```

## 安装和配置

### 1. 安装依赖

#### 使用安装脚本（推荐）

```bash
# 完整安装（包含去重功能）
./setup.sh

# 跳过去重功能测试（如果网络较慢）
./setup.sh --skip-dedup-test
```

#### 手动安装

```bash
pip install -r requirements.txt
```

### 2. 配置文件

复制并编辑配置文件：

```bash
cp config.yml.example config.yml
```

#### NATS配置
```yaml
nats:
  enabled: true
  servers: 
    - 'nats://localhost:4222'
  subject: 
    - 'messages.stream'
```

#### LLM配置

**使用Ollama（推荐）：**
```yaml
llm:
  provider: 'ollama'
  ollama:
    base_url: 'http://localhost:11434'
    model: 'llama3.1:8b'
    temperature: 0.1
```

**使用OpenAI：**
```yaml
llm:
  provider: 'openai'
  openai:
    api_key: 'your-openai-api-key'
    model: 'gpt-4o-mini'
    temperature: 0.1
```

**使用Anthropic：**
```yaml
llm:
  provider: 'anthropic'
  anthropic:
    api_key: 'your-anthropic-api-key'
    model: 'claude-3-haiku-20240307'
    temperature: 0.1
```

**使用DeepSeek：**
```yaml
llm:
  provider: 'deepseek'
  deepseek:
    api_key: 'your-deepseek-api-key'
    model: 'deepseek-chat'  # 支持: deepseek-chat, deepseek-reasoner
    temperature: 0.1
```

#### Agent配置
```yaml
agents:
  sentiment_analysis:
    enabled: true
    name: '情绪分析Agent'
```

#### 消息去重配置
```yaml
deduplication:
  enabled: true  # 是否启用消息去重
  model_name: 'BAAI/bge-m3'  # 句向量模型名称
  similarity_threshold: 0.85  # 相似度阈值 (0.0-1.0)
  time_window_hours: 2  # 时间窗口（小时）
  max_cache_size: 10000  # 最大缓存大小
  cache_file: 'message_cache.pkl'  # 缓存文件路径
```

**配置说明：**
- `enabled`: 是否启用去重功能
- `model_name`: 句向量模型，推荐使用 `BAAI/bge-m3` 支持中英文混合
- `similarity_threshold`: 相似度阈值，范围0.0-1.0，越高越严格
- `time_window_hours`: 时间窗口，只在此时间内检测重复
- `max_cache_size`: 最大缓存消息数量
- `cache_file`: 缓存文件路径，支持持久化

### 3. 启动服务

#### 启动NATS服务器
```bash
# 使用Docker
docker run -p 4222:4222 nats:latest

# 或者本地安装
nats-server
```

#### 启动Ollama（如果使用）
```bash
# 安装Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# 下载模型
ollama pull llama3.1:8b

# 启动服务
ollama serve
```

#### 启动Analyze Agent
```bash
python main.py
```

## 使用方法

### 1. 运行测试
```bash
python test_agent.py
```

### 2. 测试消息去重
```bash
python test_deduplication.py
```

### 3. 测试模型检测
```bash
python test_model_detection.py
```

### 4. 启动监控
```bash
python main.py
```

### 5. 查看分析结果
系统会实时输出分析结果到控制台：

```json
{
  "type": "analysis.sentiment",
  "timestamp": 1748142870135,
  "source": "analyze_agent",
  "sender": "sentiment_analysis_agent",
  "agent_name": "情绪分析Agent",
  "original_message_id": 12345,
  "original_chat_id": -1001234567890,
  "data": {
    "sentiment": "利多",
    "reason": "消息提到BTC突破新高，市场情绪积极",
    "score": 0.8,
    "analysis_time": "2024-12-23T10:30:00.000Z",
    "llm_provider": "ollama"
  }
}
```

## 消息格式

### 输入消息（来自TelegramStream）
```json
{
  "type": "telegram.message",
  "timestamp": 1748142870135,
  "source": "telegram",
  "sender": "telegramstream",
  "data": {
    "message_id": 12345,
    "chat_id": -1001234567890,
    "text": "🚀 BTC突破10万美元！牛市来了！",
    "extracted_data": {
      "raw_text": "BTC突破10万美元！牛市来了！",
      "symbols": ["BTC"],
      "crypto_currencies": [...]
    }
  }
}
```

### 输出消息（分析结果）
```json
{
  "type": "analysis.sentiment",
  "timestamp": 1748142870135,
  "source": "analyze_agent",
  "sender": "sentiment_analysis_agent",
  "data": {
    "sentiment": "利多/利空/中性",
    "reason": "分析理由",
    "score": 0.8,
    "analysis_time": "2024-12-23T10:30:00.000Z"
  }
}
```

## 扩展开发

### 添加新的Agent

1. **创建Agent类**：
```python
class PriceAnalysisAgent(BaseAgent):
    def __init__(self, llm_manager: LLMManager):
        super().__init__("价格分析Agent", llm_manager)
    
    async def process(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        # 实现价格分析逻辑
        pass
```

2. **在AgentManager中注册**：
```python
if agents_config.get('price_analysis', {}).get('enabled', False):
    self.agents.append(PriceAnalysisAgent(self.llm_manager))
```

3. **更新配置文件**：
```yaml
agents:
  price_analysis:
    enabled: true
    name: '价格分析Agent'
```

### 添加新的LLM提供商

1. **在LLMManager中添加支持**：
```python
elif self.provider == 'new_provider':
    config = self.config.get('new_provider', {})
    return NewProviderLLM(**config)
```

2. **更新配置文件**：
```yaml
llm:
  provider: 'new_provider'
  new_provider:
    api_key: 'your-api-key'
    model: 'model-name'
```

## 性能优化

### 1. 并发处理
- 系统支持多Agent并发处理
- 每个Agent独立处理，互不影响

### 2. 错误处理
- 完善的异常处理机制
- Agent失败不影响其他Agent
- 自动降级和重试

### 3. 资源管理
- 连接池管理
- 内存优化
- 日志级别控制

## 监控和调试

### 日志配置
```yaml
logging:
  level: 'DEBUG'  # DEBUG, INFO, WARNING, ERROR
  format: '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
```

### 常见问题

1. **NATS连接失败**
   - 检查NATS服务器是否启动
   - 确认端口配置正确

2. **LLM调用失败**
   - 检查API密钥配置
   - 确认模型名称正确
   - 检查网络连接

3. **Agent不工作**
   - 确认Agent在配置中已启用
   - 检查消息格式是否正确

4. **Keras 3兼容性问题**
   - 如果遇到 "Keras 3 not supported" 错误
   - 运行修复脚本: `python3 fix_keras_compatibility.py`
   - 或手动安装: `pip install tf-keras`
   - 详细解决方案请参考: [KERAS_FIX_GUIDE.md](KERAS_FIX_GUIDE.md)

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request！ 