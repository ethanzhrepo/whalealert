# Telegram 消息结构定义

## 通用消息结构

所有 Telegram 监控消息使用通用信封结构:

```json
{
  "type": "string",  // 消息类型，例如: "telegram.message", "telegram.edit", "telegram.delete"
  "timestamp": 1234567890,  // Unix 时间戳 (毫秒)
  "source": "telegram",  // 消息来源标识
  "sender": "telegramstream",  // 发送者标识，固定为 telegramstream
  "data": {}  // 消息数据，根据消息类型不同而结构不同
}
```

## 消息类型

### 新消息事件 (telegram.message)

```json
{
  "type": "telegram.message",
  "timestamp": 1734567890123,
  "source": "telegram",
  "sender": "telegramstream",
  "data": {
    "message_id": 12345,  // 消息 ID
    "chat_id": -1001234567890,  // 群组/频道 ID
    "chat_title": "Crypto Signals",  // 群组/频道名称
    "chat_type": "channel",  // 类型: "group", "channel", "supergroup"
    "user_id": 123456789,  // 发送者用户 ID (可能为空，如频道消息)
    "username": "crypto_trader",  // 发送者用户名 (可能为空)
    "first_name": "John",  // 发送者名字 (可能为空)
    "is_bot": false,  // 是否为机器人
    "date": 1734567890123,  // 消息发送时间 (Unix 时间戳，毫秒)
    "text": "🚀 WETH/USDC pair showing strong momentum...",  // 消息文本内容
    "raw_text": "WETH/USDC pair showing strong momentum...",  // 去除表情符号的文本
    "reply_to_message_id": 12344,  // 回复的消息 ID (可能为空)
    "forward_from_chat_id": null,  // 转发来源群组 ID (可能为空)
    "entities": [  // 消息实体信息
      {
        "type": "text_link",
        "offset": 50,
        "length": 10,
        "url": "https://dexscreener.com/ethereum/0x1234..."
      }
    ],
    "media": {  // 媒体信息 (可能为空)
      "type": "photo",  // 媒体类型: "photo", "video", "document", "audio"
      "file_id": "BAADBAADrwADBM0AA...",
      "file_size": 102400,
      "caption": "Chart analysis for WETH"
    },
    "extracted_data": {  // 提取的结构化数据
      "addresses": {  // 提取的区块链地址
        "ethereum": ["0x1234567890abcdef1234567890abcdef12345678"],
        "solana": ["11111111111111111111111111111112"],
        "bitcoin": ["1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"]
      },
      "symbols": ["WETH", "USDC", "BTC", "ETH"],  // 提取的代币符号列表（向后兼容）
      "crypto_currencies": [  // 新增：匹配到的完整数字货币信息（来自CoinGecko API）
        {
          "id": "ethereum",
          "symbol": "eth",
          "name": "Ethereum",
          "image": "https://coin-images.coingecko.com/coins/images/279/large/ethereum.png",
          "current_price": 2250.50,
          "market_cap": 270895123456,
          "market_cap_rank": 2,
          "fully_diluted_valuation": 270895123456,
          "total_volume": 15234567890,
          "high_24h": 2290.75,
          "low_24h": 2210.30,
          "price_change_24h": 45.20,
          "price_change_percentage_24h": 2.05,
          "market_cap_change_24h": 5432109876,
          "market_cap_change_percentage_24h": 2.05,
          "circulating_supply": 120442405.374,
          "total_supply": 120442405.374,
          "max_supply": null,
          "ath": 4878.26,
          "ath_change_percentage": -53.85,
          "ath_date": "2021-11-10T14:24:19.604Z",
          "atl": 0.432979,
          "atl_change_percentage": 519673.67,
          "atl_date": "2015-10-20T00:00:00.000Z",
          "roi": {
            "times": 86.8168,
            "currency": "eth",
            "percentage": 8681.68
          },
          "last_updated": "2024-12-23T10:30:00.000Z"
        },
        {
          "id": "bitcoin",
          "symbol": "btc",
          "name": "Bitcoin",
          "image": "https://coin-images.coingecko.com/coins/images/1/large/bitcoin.png",
          "current_price": 97500.25,
          "market_cap": 1925678901234,
          "market_cap_rank": 1,
          // ... 完整的CoinGecko API响应数据
        }
      ],
      "urls": [  // 提取的链接
        {
          "url": "https://dexscreener.com/ethereum/0x1234...",
          "domain": "dexscreener.com",
          "type": "dex_tracker"
        }
      ],
      "prices": [  // 提取的价格信息
        {
          "price": 3500.50,
          "currency": "USD"
        }
      ],
      "keywords": ["momentum", "bullish", "pump"],  // 关键词
      "sentiment": "positive",  // 情感分析: "positive", "negative", "neutral"
      "raw_text": "WETH/USDC pair showing strong momentum..."  // 去除表情符号的原始文本
    }
  }
}
```

### 消息编辑事件 (telegram.edit)

```json
{
  "type": "telegram.edit",
  "timestamp": 1734567890123,
  "source": "telegram",
  "sender": "telegramstream",
  "data": {
    "message_id": 12345,
    "chat_id": -1001234567890,
    "chat_title": "Crypto Signals",
    "chat_type": "channel",
    "user_id": 123456789,
    "username": "crypto_trader",
    "first_name": "John",
    "is_bot": false,
    "date": 1734567890123,
    "text": "Updated message content",
    "raw_text": "Updated message content",
    "edit_date": 1734567895123,  // 编辑时间 (Unix 时间戳，毫秒)
    "reply_to_message_id": null,
    "forward_from_chat_id": null,
    "entities": [],
    "media": null,
    "extracted_data": {
      // 同新消息结构，包含crypto_currencies字段
    }
  }
}
```

### 消息删除事件 (telegram.delete)

```json
{
  "type": "telegram.delete",
  "timestamp": 1734567890123,
  "source": "telegram",
  "sender": "telegramstream",
  "data": {
    "message_ids": [12345, 12346],  // 被删除的消息ID列表
    "chat_id": -1001234567890,
    "chat_title": "Crypto Signals",
    "deleted_at": 1734567900123  // 删除时间 (Unix 时间戳，毫秒)
  }
}
```

## 数据提取规则

### 数字货币符号识别 (增强版)

系统现在使用 **CoinGecko API** 进行智能符号匹配，具有以下特性：

- **实时数据**: 每小时从CoinGecko获取最新的前100个数字货币数据
- **智能匹配**: 同时匹配symbol（如"BTC"）和name（如"Bitcoin"），大小写不敏感
- **完整信息**: 返回包含价格、市值、排名等完整信息的CoinGecko API响应
- **降级处理**: 当API不可用时，自动降级到正则表达式匹配
- **重复防护**: 避免同一货币的重复匹配

#### 匹配逻辑
1. 优先使用CoinGecko API匹配symbol和name
2. 如果API匹配失败或无结果，使用正则表达式作为备选：`\b[A-Z]{2,10}\b`
3. 符号列表(`symbols`)保持向后兼容，包含所有匹配的符号
4. 新增数字货币信息(`crypto_currencies`)包含完整的CoinGecko数据

#### CoinGecko数据字段说明
- `id`: CoinGecko唯一标识符
- `symbol`: 代币符号（小写）
- `name`: 完整名称
- `current_price`: 当前USD价格
- `market_cap`: 市值
- `market_cap_rank`: 市值排名
- `price_change_24h`: 24小时价格变化
- `price_change_percentage_24h`: 24小时价格变化百分比
- `volume_24h`: 24小时交易量
- `ath`: 历史最高价
- `atl`: 历史最低价
- 更多字段详见CoinGecko API文档

### 地址识别模式

- **Ethereum**: `0x[a-fA-F0-9]{40}`
- **Solana**: Base58 编码，长度 32-44 字符
- **Bitcoin**: 以 `1`, `3`, `bc1` 开头的有效地址

### URL 分类

- **DEX 追踪器**: dexscreener.com, dextools.io, birdeye.so
- **区块链浏览器**: etherscan.io, solscan.io, blockchain.info
- **交易所**: binance.com, coinbase.com, okx.com
- **社交媒体**: twitter.com, telegram.me, discord.gg

### 关键词分类

- **看涨信号**: pump, moon, bullish, buy, long, rocket
- **看跌信号**: dump, bear, bearish, sell, short, crash
- **中性分析**: analysis, chart, support, resistance, volume

## 性能和缓存

- **CoinGecko数据缓存**: 每小时自动刷新一次，减少API调用
- **失败降级**: 网络问题时自动切换到正则表达式匹配
- **异步处理**: 所有API调用均为异步，不阻塞消息处理
- **日志记录**: 完整的调试日志，便于问题排查

## 分析结果通知消息 (messages.notification)

### 概述

当 `analyze_agent` 完成对 Telegram 消息的分析后，会将原始消息数据和分析结果合并，发送到 `messages.notification` subject。这种设计允许下游系统同时获得原始消息和分析结果，无需额外查询。

### 消息结构

```json
{
  "type": "messages.notification",
  "timestamp": 1734567890123,  // 通知发送时间 (Unix 时间戳，毫秒)
  "source": "analyze_agent",
  "sender": "analyze_agent",
  "data": {
    "original_message": {  // 完整的原始 Telegram 消息数据
      "type": "telegram.message",
      "timestamp": 1734567890123,
      "source": "telegram",
      "sender": "telegramstream",
      "data": {
        "message_id": 12345,
        "chat_id": -1001234567890,
        "chat_title": "Crypto Signals",
        "chat_type": "channel",
        "user_id": 123456789,
        "username": "crypto_trader",
        "first_name": "John",
        "is_bot": false,
        "date": 1734567890123,
        "text": "🚀 BTC突破10万美元！牛市来了！",
        "raw_text": "BTC突破10万美元！牛市来了！",
        "reply_to_message_id": null,
        "forward_from_chat_id": null,
        "entities": [],
        "media": null,
        "extracted_data": {
          "addresses": {
            "ethereum": [],
            "solana": [],
            "bitcoin": []
          },
          "symbols": ["BTC"],
          "crypto_currencies": [
            {
              "id": "bitcoin",
              "symbol": "btc",
              "name": "Bitcoin",
              "current_price": 100000.00,
              // ... 完整的CoinGecko数据
            }
          ],
          "urls": [],
          "prices": [
            {
              "price": 100000.00,
              "currency": "USD"
            }
          ],
          "keywords": ["突破", "牛市"],
          "sentiment": "positive",
          "raw_text": "BTC突破10万美元！牛市来了！"
        }
      }
    },
    "analysis_results": [  // 所有Agent的分析结果数组
      {
        "agent_name": "情绪分析Agent",
        "agent_type": "sentiment_analysis",
        "result": {
          "sentiment": "利多",
          "reason": "BTC突破重要价格关口，市场情绪极度乐观",
          "score": 0.9,
          "confidence": 0.95  // 置信度 (0-1)
        },
        "processing_time_ms": 1250,  // 处理耗时（毫秒）
        "llm_provider": "ollama",
        "analysis_time": "2024-12-23T10:30:15.123Z"
      }
      // 未来可能包含更多Agent的结果
      // {
      //   "agent_name": "价格分析Agent",
      //   "agent_type": "price_analysis",
      //   "result": {
      //     "trend": "bullish",
      //     "target_price": 120000,
      //     "support_level": 95000,
      //     "resistance_level": 105000
      //   },
      //   "processing_time_ms": 800,
      //   "analysis_time": "2024-12-23T10:30:16.456Z"
      // }
    ],
    "summary": {  // 分析结果汇总
      "total_agents": 1,
      "successful_analyses": 1,
      "failed_analyses": 0,
      "overall_sentiment": "利多",  // 综合情绪（如果有多个Agent）
      "overall_score": 0.9,  // 综合评分
      "processing_start_time": "2024-12-23T10:30:14.000Z",
      "processing_end_time": "2024-12-23T10:30:15.123Z",
      "total_processing_time_ms": 1123
    }
  }
}
```

### 字段说明

#### 顶层字段
- `type`: 固定为 `"messages.notification"`
- `timestamp`: 通知消息发送时间
- `source`: 固定为 `"analyze_agent"`
- `sender`: 固定为 `"analyze_agent"`

#### data.original_message
包含完整的原始 Telegram 消息数据，格式与 `telegram.message` 完全相同。这确保下游系统能够访问所有原始信息。

#### data.analysis_results
Agent分析结果数组，每个元素包含：
- `agent_name`: Agent的显示名称
- `agent_type`: Agent类型标识符
- `result`: 具体的分析结果（格式因Agent类型而异）
- `processing_time_ms`: 该Agent的处理耗时
- `llm_provider`: 使用的LLM提供商（如适用）
- `analysis_time`: 分析完成时间

#### data.summary
分析过程的汇总信息：
- `total_agents`: 参与分析的Agent总数
- `successful_analyses`: 成功完成分析的Agent数量
- `failed_analyses`: 分析失败的Agent数量
- `overall_sentiment`: 综合情绪判断（多Agent时的汇总结果）
- `overall_score`: 综合评分
- `processing_start_time`: 开始处理时间
- `processing_end_time`: 完成处理时间
- `total_processing_time_ms`: 总处理耗时

### 使用场景

1. **实时通知系统**: 下游服务可以订阅此subject获得实时的分析结果
2. **数据存储**: 可以直接存储完整的消息和分析结果
3. **API服务**: 为前端或其他服务提供结构化的分析数据
4. **监控告警**: 基于分析结果触发特定的业务逻辑

### 错误处理

如果所有Agent都分析失败，仍会发送通知消息，但 `analysis_results` 为空数组，`summary.failed_analyses` 会反映失败数量。

### 扩展性

该格式设计为可扩展的：
- 新增Agent时，只需在 `analysis_results` 数组中添加新的结果对象
- `summary` 部分会自动反映所有Agent的汇总信息
- 原始消息格式保持不变，确保向后兼容 