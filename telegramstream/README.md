# Telegram 消息监控程序

一个高性能的 Telegram 群组/频道消息监控程序，专为金融消息套利场景设计，支持实时消息提取、结构化数据解析和消息队列分发。

## 功能特性

- 🎯 **精准监控**: 支持同时监控多个 Telegram 群组和频道
- 🔍 **智能提取**: 自动提取区块链地址、代币符号、价格信息、URL 等关键数据
- 📊 **情感分析**: 内置关键词分析和情感倾向判断
- ⚡ **低延迟**: 针对金融套利场景优化，最小化消息处理延迟
- 🎛️ **交互配置**: 使用 prompt_toolkit 提供友好的群组选择界面
- 📨 **消息队列**: 支持 NATS 消息队列集成，便于下游系统接收
- 🔧 **灵活配置**: YAML 配置文件，支持高级过滤和提取选项

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置 Telegram API

1. 访问 [https://my.telegram.org](https://my.telegram.org) 获取 API 凭据
2. 复制配置文件模板并填入您的信息：

```bash
cp config.yml.example config.yml
```

编辑 `config.yml` 文件：

```yaml
telegram:
  api_id: 'your_api_id'
  api_hash: 'your_api_hash'
  phone: 'your_phone_number'
```

### 3. 配置监控群组/频道

```bash
python main.py config
```

程序会：
- 自动获取您加入的所有群组和频道
- 提供交互式界面供您选择要监控的群组/频道
- 保存配置到 `config.yml` 文件

### 4. 启动监控

```bash
python main.py start
```

## 配置选项

### NATS 消息队列配置

如需将消息发送到 NATS 队列，在 `config.yml` 中配置：

```yaml
nats:
  enabled: true
  servers: 
    - 'nats://localhost:4222'
  subject: 'telegram.messages'
```

### 高级过滤配置

```yaml
advanced:
  filters:
    min_message_length: 10  # 最小消息长度
    ignore_bots: true  # 忽略机器人消息
    keywords:  # 关键词过滤
      - "trading"
      - "crypto"
      - "DeFi"
```

## 消息结构

程序输出的消息遵循统一的 JSON 结构，详见 [message.md](./message.md)。

### 示例输出

```json
{
  "type": "telegram.message",
  "timestamp": 1734567890123,
  "source": "telegram",
  "data": {
    "message_id": 12345,
    "chat_title": "Crypto Signals",
    "text": "🚀 WETH pump incoming! Check 0x1234...5678",
    "extracted_data": {
      "addresses": {
        "ethereum": ["0x1234567890abcdef1234567890abcdef12345678"]
      },
      "symbols": ["WETH"],
      "sentiment": "positive",
      "keywords": ["pump"]
    }
  }
}
```

## 数据提取功能

程序可自动提取以下类型的数据：

### 区块链地址
- **Ethereum**: `0x[a-fA-F0-9]{40}`
- **Solana**: Base58 编码地址
- **Bitcoin**: BTC 地址格式

### 代币符号
- 2-10 位大写字母组合
- 支持主流币种和稳定币识别

### URL 分类
- DEX 追踪器 (dexscreener, dextools 等)
- 区块链浏览器 (etherscan, solscan 等)
- 交易所链接
- 社交媒体链接

### 情感分析
- **看涨信号**: pump, moon, bullish, buy, long
- **看跌信号**: dump, bear, bearish, sell, short
- **中性分析**: analysis, chart, support, resistance

## 性能优化

- 使用异步编程模型，支持高并发消息处理
- 针对金融场景优化延迟，确保消息实时性
- 支持多线程监控，每个群组/频道独立处理
- 内存优化的正则表达式引擎

## 注意事项

- 首次运行需要进行 Telegram 账户验证
- 确保账户已加入要监控的群组/频道
- 监控大量活跃群组时注意 API 速率限制
- 建议在生产环境中配置 NATS 集群以提高可靠性

## 许可证

MIT License