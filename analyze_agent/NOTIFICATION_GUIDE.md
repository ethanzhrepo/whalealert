# 分析结果通知功能指南

## 概述

analyze_agent 现在支持将分析结果与原始消息合并，发送到 `messages.notification` subject。这个功能允许下游系统同时获得原始 Telegram 消息和 AI 分析结果，无需额外查询。

## 功能特性

### 🔄 消息流程
1. **telegramstream** 发送原始消息到 `messages.stream`
2. **analyze_agent** 接收并分析消息
3. **analyze_agent** 将原始消息和分析结果合并，发送到 `messages.notification`

### 📊 通知消息内容
- **完整原始消息**: 包含所有 Telegram 消息数据
- **分析结果数组**: 所有 Agent 的分析结果
- **汇总信息**: 处理统计和综合评估
- **性能指标**: 处理时间、成功/失败统计

## 配置

### NATS Subject 配置

在 `config.yml` 中配置通知 subject：

```yaml
nats:
  enabled: true
  servers: 
    - 'nats://localhost:4222'
  subject: 
    - 'messages.stream'  # 监听的输入subject
  notification_subject: 'messages.notification'  # 通知输出subject
```

## 使用方法

### 1. 启动系统组件

```bash
# 1. 启动 NATS 服务器
nats-server

# 2. 启动 telegramstream（可选，用于真实消息）
cd telegramstream
python main.py start

# 3. 启动 analyze_agent
cd analyze_agent
python main.py
```

### 2. 监听通知消息

使用提供的测试脚本监听通知：

```bash
cd analyze_agent
python test_notification.py
```

### 3. 发送测试消息

使用模拟器发送测试消息：

```bash
cd analyze_agent
python simulate_message.py
```

## 测试工具

### test_notification.py
- **功能**: 监听 `messages.notification` subject
- **特性**: 
  - 验证消息结构
  - 格式化显示分析结果
  - 同时监听原始消息流
  - 提供详细的调试信息

**运行示例**:
```bash
python test_notification.py
```

### simulate_message.py
- **功能**: 模拟发送 Telegram 消息到 `messages.stream`
- **特性**:
  - 发送多种情绪类型的测试消息
  - 预期分析结果验证
  - 自动间隔发送

**运行示例**:
```bash
python simulate_message.py
```

## 消息格式

### 通知消息结构

```json
{
  "type": "messages.notification",
  "timestamp": 1734567890123,
  "source": "analyze_agent",
  "sender": "analyze_agent",
  "data": {
    "original_message": {
      // 完整的原始 Telegram 消息
    },
    "analysis_results": [
      {
        "agent_name": "情绪分析Agent",
        "agent_type": "sentiment_analysis",
        "result": {
          "sentiment": "利多",
          "reason": "BTC突破重要价格关口",
          "score": 0.9
        },
        "processing_time_ms": 1250,
        "llm_provider": "ollama",
        "analysis_time": "2024-12-23T10:30:15.123Z"
      }
    ],
    "summary": {
      "total_agents": 1,
      "successful_analyses": 1,
      "failed_analyses": 0,
      "overall_sentiment": "利多",
      "overall_score": 0.9,
      "processing_start_time": "2024-12-23T10:30:14.000Z",
      "processing_end_time": "2024-12-23T10:30:15.123Z",
      "total_processing_time_ms": 1123
    }
  }
}
```

详细格式说明请参考 `telegramstream/message.md` 中的 "分析结果通知消息" 部分。

## 集成示例

### Python 订阅者示例

```python
import asyncio
import json
import nats

async def notification_handler(msg):
    """处理通知消息"""
    data = json.loads(msg.data.decode())
    
    # 提取原始消息
    original_msg = data['data']['original_message']
    
    # 提取分析结果
    analysis_results = data['data']['analysis_results']
    
    # 提取汇总信息
    summary = data['data']['summary']
    
    # 处理业务逻辑
    for result in analysis_results:
        if result['agent_type'] == 'sentiment_analysis':
            sentiment = result['result']['sentiment']
            score = result['result']['score']
            
            # 根据情绪分析结果执行相应操作
            if sentiment == '利多' and score > 0.8:
                print("强烈看涨信号！")
            elif sentiment == '利空' and score < -0.8:
                print("强烈看跌信号！")

async def main():
    nc = await nats.connect("nats://localhost:4222")
    await nc.subscribe("messages.notification", cb=notification_handler)
    
    # 保持运行
    while True:
        await asyncio.sleep(1)

if __name__ == '__main__':
    asyncio.run(main())
```

## 性能监控

### 处理时间指标
- `processing_time_ms`: 单个 Agent 处理时间
- `total_processing_time_ms`: 总处理时间
- `analysis_time`: 分析完成时间戳

### 成功率统计
- `total_agents`: 参与分析的 Agent 总数
- `successful_analyses`: 成功分析数量
- `failed_analyses`: 失败分析数量

## 故障排除

### 常见问题

1. **未收到通知消息**
   - 检查 NATS 服务器是否运行
   - 确认 analyze_agent 配置正确
   - 验证 subject 名称匹配

2. **分析结果为空**
   - 检查 LLM 服务是否可用
   - 查看 analyze_agent 日志
   - 确认 Agent 配置已启用

3. **消息格式错误**
   - 验证输入消息格式
   - 检查 JSON 解析错误
   - 查看详细错误日志

### 调试技巧

1. **启用详细日志**:
   ```yaml
   logging:
     level: 'DEBUG'
   ```

2. **使用测试工具**:
   ```bash
   # 监听所有消息
   python test_notification.py
   
   # 发送测试消息
   python simulate_message.py
   ```

3. **检查 NATS 连接**:
   ```bash
   nats sub "messages.notification"
   ```

## 扩展开发

### 添加新的 Agent

1. 创建新的 Agent 类继承 `BaseAgent`
2. 在 `AgentManager._initialize_agents()` 中注册
3. 在 `_get_agent_type()` 中添加类型映射
4. 更新配置文件启用新 Agent

### 自定义通知格式

可以通过修改 `AnalyzeAgent._send_notification()` 方法来自定义通知消息格式，但建议保持向后兼容性。

## 最佳实践

1. **订阅者设计**: 使用异步处理避免阻塞
2. **错误处理**: 实现重试机制和降级策略
3. **性能优化**: 监控处理时间，优化慢速 Agent
4. **数据存储**: 考虑将通知消息持久化存储
5. **监控告警**: 基于分析结果设置业务告警 