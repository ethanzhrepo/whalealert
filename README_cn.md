# WhaleBot - 智能加密货币交易信号系统

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![NATS](https://img.shields.io/badge/NATS-messaging-green.svg)](https://nats.io/)

一个全面的多智能体加密货币交易信号系统，监控Telegram频道和Twitter列表，使用AI分析消息，并提供智能通知。专为高频交易场景设计，具有低延迟消息处理和语义去重功能。

## 🌟 核心特性

- **🎯 多源监控**: 实时监控Telegram频道/群组和Twitter列表
- **🐦 Twitter集成**: Chrome扩展程序监控Twitter列表，支持自动刷新和重连
- **🤖 AI驱动分析**: 使用LLM进行多智能体情绪分析（Ollama/OpenAI/Anthropic）
- **🔄 消息去重**: 针对中英文混合内容的语义级重复检测
- **📊 智能过滤**: 基于情绪评分和关键词的高级过滤
- **⚡ 低延迟**: 针对金融套利场景优化，最小化处理延迟
- **🔔 智能通知**: 格式化的Telegram通知，内容丰富
- **🏗️ 微服务架构**: 模块化设计，集成NATS消息队列
- **🌐 多语言支持**: 处理中英文混合的加密货币内容
- **🔄 自动重连**: 强大的连接管理，支持指数退避算法
- **📱 浏览器扩展**: Chrome扩展程序实时监控Twitter，带状态显示

## 🏛️ 系统架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  TelegramStream │───▶│                 │───▶│  Analyze Agent  │───▶│ Notification Bot│    │   X Extension   │
│                 │    │   NATS Queue    │    │                 │    │                 │    │                 │
│ • 消息监控      │    │ messages.stream │    │ • 情绪分析      │    │ • Telegram Bot  │    │ • Twitter列表   │
│ • 数据提取      │    │ twitter.messages│    │ • 消息去重      │    │ • 多群组支持    │    │ • 自动刷新      │
│ • 实时处理      │    │                 │    │ • 多LLM支持     │    │ • 丰富格式      │    │ • 实时监控      │
│                 │    │ • 低延迟        │    │ • 智能过滤      │    │ • 限流保护      │    │ • WebSocket     │
│                 │    │ • 可靠传输      │    │ • JSON安全      │    │ • 错误重试      │    │ • 自动重连      │
│                 │    │ • 可扩展        │    │                 │    │                 │    │ • 状态监控      │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📦 组件介绍

### 1. TelegramStream（电报流监控）
- **用途**: 监控Telegram频道/群组的加密货币信号
- **功能**: 
  - 多频道监控
  - 智能数据提取（地址、符号、URL）
  - 情绪关键词检测
  - 低延迟消息处理
- **位置**: `./telegramstream/`

### 2. X Extension（Twitter扩展 - 新增）
- **用途**: Chrome浏览器扩展程序，用于监控Twitter列表
- **功能**:
  - 实时Twitter列表监控
  - 自动刷新，可配置间隔（10秒-3600秒）
  - NATS WebSocket集成，支持自动重连
  - 结构化数据提取（加密货币符号、价格、地址）
  - 情绪分析和重复检测
  - 用户友好的配置界面
  - 连接状态监控，带可视化指示器
- **位置**: `./x_extansion/`

### 3. Analyze Agent（分析智能体）
- **用途**: AI驱动的消息分析与去重
- **功能**:
  - 多智能体情绪分析
  - 使用BGE-M3模型的语义消息去重
  - 支持Ollama、OpenAI和Anthropic LLM
  - 可配置相似度阈值
  - 实时处理与缓存
  - JSON序列化安全，支持numpy类型
  - 同时支持Telegram和Twitter消息
- **位置**: `./analyze_agent/`

### 4. Notification Bot（通知机器人）
- **用途**: 向Telegram群组发送格式化通知
- **功能**:
  - 多群组广播
  - 丰富的消息格式
  - 限流和错误处理
  - 可配置过滤
- **位置**: `./notification/`

## 🚀 快速开始

### 前置要求

- Python 3.8+
- 支持WebSocket的NATS服务器
- Telegram API凭据
- LLM服务（Ollama/OpenAI/Anthropic）
- Chrome浏览器（用于X Extension）

### 1. 克隆仓库

```bash
git clone https://github.com/ethanzhrepo/whalealert.git
cd whalebot
```

### 2. 设置支持WebSocket的NATS服务器

```bash
# 使用Docker启用WebSocket支持
docker run -p 4222:4222 -p 8222:8222 nats:latest -js -m 8222

# 或本地安装并启用WebSocket支持
# 访问: https://docs.nats.io/running-a-nats-service/introduction/installation
```

### 3. 设置TelegramStream

```bash
cd telegramstream
./setup.sh
cp config.yml.example config.yml
# 编辑config.yml，填入您的Telegram API凭据
python main.py config  # 交互式频道选择
python main.py start   # 开始监控
```

### 4. 设置X Extension

```bash
cd ../x_extansion
# 打开Chrome浏览器，访问 chrome://extensions/
# 启用"开发者模式"
# 点击"加载已解压的扩展程序"，选择x_extansion文件夹
# 在扩展程序弹窗中配置NATS服务器和Twitter列表
```

### 5. 设置Analyze Agent

```bash
cd ../analyze_agent
./setup.sh
cp config.yml.example config.yml
# 配置LLM提供商和去重设置
# 在NATS主题中添加'twitter.messages'
python main.py  # 启动分析服务
```

### 6. 设置Notification Bot

```bash
cd ../notification
./setup.sh
cp config.yml.example config.yml
# 配置Telegram Bot token和目标群组
./run.sh  # 启动通知服务
```

## ⚙️ 配置说明

### TelegramStream配置

```yaml
telegram:
  api_id: 'your_api_id'
  api_hash: 'your_api_hash'
  phone: 'your_phone_number'

nats:
  enabled: true
  servers: ['nats://localhost:4222']
  subject: 'messages.stream'
```

### X Extension配置

```yaml
# 通过Chrome扩展程序弹窗配置
nats_servers: ['ws://localhost:4222']
nats_subject: 'twitter.messages'
monitored_lists: 
  - 'https://twitter.com/i/lists/123456789'
auto_refresh: true
refresh_interval: 300  # 秒（最低10秒）
max_messages: 5
```

### Analyze Agent配置

```yaml
# LLM配置
llm:
  provider: 'ollama'  # ollama/openai/anthropic
  ollama:
    base_url: 'http://localhost:11434'
    model: 'llama3.1:8b'

# NATS配置（已更新）
nats:
  enabled: true
  servers: ['nats://localhost:4222']
  subject:
    - 'messages.stream'    # Telegram消息
    - 'twitter.messages'   # Twitter消息（新增）

# 消息去重
deduplication:
  enabled: true
  model_name: 'BAAI/bge-m3'
  similarity_threshold: 0.85
  time_window_hours: 2

# 智能体配置
agents:
  sentiment_analysis:
    enabled: true
```

### Notification Bot配置

```yaml
telegram:
  bot_token: 'your_bot_token'
  target_groups:
    - chat_id: -1001234567890
      name: '主要信号群'
      enabled: true
```

## 🔧 高级功能

### X Extension功能

#### 自动重连
- **指数退避**: 1秒 → 2秒 → 4秒 → 8秒 → 16秒 → 最大30秒
- **持续重试**: 达到最大重连次数后，60秒重置计数器继续尝试
- **可视化状态**: 实时连接指示器，带动画效果
- **手动控制**: 可根据需要启用/禁用重连功能

#### 自动刷新
- **智能检测**: 仅在被监控的Twitter列表页面刷新
- **可配置间隔**: 10秒到1小时
- **安全机制**: 页面切换或监控禁用时自动停止
- **性能优化**: 最小化资源使用

#### 数据提取
- **加密货币符号**: BTC、ETH、SOL和自定义模式
- **价格信息**: USD/USDT/USDC价格检测
- **区块链地址**: Ethereum和Solana地址提取
- **情绪分析**: 基于关键词的看涨/看跌检测

### 消息去重

系统包含复杂的语义去重功能：

- **BGE-M3模型**: 处理中英文混合内容
- **FAISS索引**: 快速相似度搜索
- **时间窗口**: 可配置的去重时间段
- **相似度阈值**: 可调节的检测敏感度
- **JSON安全**: 正确处理numpy类型的序列化

重复检测示例：
```
原消息: "Binance 将上线新币 DOGE/USDT Trading Pair"
相似消息: "币安即将推出 DOGE/USDT 交易对"
相似度: 0.87 > 0.85阈值 → 标记为重复
```

### 多LLM支持

支持多个LLM提供商：

- **Ollama**: 本地部署，支持Llama、Qwen等模型
- **OpenAI**: GPT-4、GPT-3.5-turbo
- **Anthropic**: Claude-3系列

### 智能数据提取

自动提取：
- **区块链地址**: Ethereum、Solana、Bitcoin
- **代币符号**: 2-10字符大写组合
- **URL**: DEX追踪器、区块链浏览器、交易所
- **情绪关键词**: 看涨/看跌指标

## 📊 消息流程

### Telegram消息流程
```json
{
  "type": "telegram.message",
  "timestamp": 1734567890123,
  "source": "telegram",
  "data": {
    "message_id": 12345,
    "chat_title": "加密信号群",
    "text": "🚀 BTC突破10万美元！牛市来了！",
    "extracted_data": {
      "symbols": ["BTC"],
      "sentiment": "positive",
      "keywords": ["突破", "牛市"]
    }
  }
}
```

### Twitter消息流程（新增）
```json
{
  "type": "twitter.message",
  "timestamp": 1734567890123,
  "source": "twitter",
  "sender": "x_extension",
  "data": {
    "message_id": "1234567890",
    "list_url": "https://twitter.com/i/lists/123456789",
    "username": "crypto_trader",
    "text": "🚀 $BTC breaking $100k! Bull run confirmed!",
    "extracted_data": {
      "symbols": ["BTC"],
      "prices": [{"price": 100000, "currency": "USD"}],
      "sentiment": "positive",
      "keywords": ["breaking", "bull run"]
    }
  }
}
```

### 分析结果
```json
{
  "type": "analysis.sentiment",
  "data": {
    "sentiment": "利多",
    "reason": "消息提到BTC突破新高，市场情绪积极",
    "score": 0.8,
    "processing_time": 150,
    "llm_provider": "ollama"
  }
}
```

## 🧪 测试

每个组件都包含全面的测试：

```bash
# 测试TelegramStream
cd telegramstream && python test_symbol_util.py

# 测试X Extension
# 在Chrome中打开 x_extansion/test.html
# 打开 x_extansion/test_reconnect.html 测试重连功能
# 打开 x_extansion/test_autorefresh.html 测试自动刷新功能

# 测试Analyze Agent
cd analyze_agent && python test_deduplication.py

# 测试Notification Bot
cd notification && python test_notification.py
```

## 📚 文档

### 核心组件
- [TelegramStream指南](./telegramstream/README.md)
- [X Extension指南](./x_extansion/README.md)
- [Analyze Agent指南](./analyze_agent/README.md)
- [Notification Bot指南](./notification/README.md)

### 专业指南
- [X Extension安装指南](./x_extansion/INSTALLATION.md)
- [X Extension重连指南](./x_extansion/RECONNECT_GUIDE.md)
- [消息去重指南](./analyze_agent/DEDUPLICATION_GUIDE.md)
- [Keras兼容性修复](./analyze_agent/KERAS_FIX_GUIDE.md)

## 🔧 故障排除

### 常见问题

1. **NATS连接失败**
   - 确保NATS服务器在4222端口运行并支持WebSocket
   - 检查TCP和WebSocket连接的防火墙设置
   - 验证WebSocket端点：`ws://localhost:4222`

2. **X Extension问题**
   - 代码更改后重新加载扩展程序
   - 检查Chrome开发者控制台的错误信息
   - 验证Twitter列表URL是否可访问
   - 确保NATS WebSocket连接已建立

3. **Telegram API问题**
   - 验证API凭据
   - 检查目标频道的账户权限

4. **LLM连接问题**
   - Ollama: 确保服务在localhost:11434运行
   - OpenAI/Anthropic: 验证API密钥

5. **JSON序列化错误**
   - 最新版本已修复numpy类型清理问题
   - 如果问题持续，请重启analyze_agent

6. **Keras 3兼容性**
   - 运行: `python3 analyze_agent/fix_keras_compatibility.py`
   - 或安装: `pip install tf-keras`

### 性能优化

- **内存**: 根据可用RAM调整去重缓存大小
- **延迟**: 为高频场景调整NATS缓冲区大小
- **准确性**: 根据内容特征调整相似度阈值
- **浏览器性能**: 使用较长的自动刷新间隔以获得更好的性能

## 🆕 最新更新

### v2.0.0 - Twitter集成
- **新增**: X Extension用于Twitter列表监控
- **新增**: 可配置间隔的自动刷新功能
- **新增**: 带指数退避的NATS自动重连
- **新增**: 实时连接状态监控
- **修复**: numpy类型的JSON序列化问题
- **改进**: 跨平台内容的消息去重
- **增强**: 配置管理和用户界面

### 主要改进
- 支持Telegram和Twitter双消息源
- 强大的连接管理，带可视化反馈
- 增强的加密货币内容数据提取
- 更好的错误处理和恢复机制

## 🤝 贡献

1. Fork仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 打开Pull Request

## 📄 许可证

本项目采用MIT许可证 - 详见[LICENSE](LICENSE)文件。

## 🙏 致谢

- [NATS](https://nats.io/) 提供可靠的消息传递
- [BGE-M3](https://huggingface.co/BAAI/bge-m3) 提供多语言嵌入
- [LangChain](https://langchain.com/) 提供LLM集成
- [Telegram](https://telegram.org/) 提供消息平台
- [Chrome Extensions API](https://developer.chrome.com/docs/extensions/) 提供浏览器集成

## 📞 支持

- 💬 Twitter [@0x99_Ethan](https://x.com/0x99_Ethan)
- 🐛 问题反馈: [GitHub Issues](https://github.com/ethanzhrepo/whalealert/issues)

---

⭐ **如果觉得有用，请给这个仓库点个星！**
