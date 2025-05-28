# Notification Bot

Telegram通知机器人，用于接收analyze_agent的分析结果并发送到指定的Telegram群组。

## 功能特性

- 🔔 **实时通知**: 监听NATS消息队列，实时接收分析结果
- 🤖 **Telegram集成**: 通过Telegram Bot发送格式化消息
- 🎯 **多群组支持**: 支持同时发送到多个Telegram群组
- 🔍 **智能过滤**: 基于情绪、评分的消息过滤
- 🚦 **限流保护**: 防止消息发送过于频繁
- 🔄 **错误重试**: 自动重试失败的消息发送
- 📊 **丰富格式**: 支持HTML格式、表情符号、@用户等
- 💰 **币种显示**: 自动识别并显示相关数字货币符号
- 🔗 **Twitter链接**: 自动为Twitter来源消息添加原文链接

## 消息格式示例

### Telegram消息

```
🚀 分析结果: 利多
📊 评分: 0.85
💡 理由: BTC突破重要价格关口，市场情绪极度乐观
📱 来源: Crypto Signals
💰 相关币种: $BTC $ETH $USDT

<pre>BTC突破10万美元！牛市来了！</pre>

👤 @crypto_trader
⏰ 14:30:25
```

### Twitter消息

```
📈 分析结果: 利多
📊 评分: 0.80
💡 理由: 提到价格上涨和买入机会，表现出积极的情绪
🐦 来源: Twitter - 列表 123456789
👤 用户: elonmusk (@elonmusk)
🔗 查看推文 [可点击链接]

<pre>Dogecoin to the moon! 🚀🌙</pre>

⏰ 14:30:25
```

## 安装和配置

### 1. 安装依赖

```bash
# 运行安装脚本
./setup.sh

# 或手动安装
pip install -r requirements.txt
```

### 2. 创建Telegram Bot

1. 联系 [@BotFather](https://t.me/BotFather)
2. 发送 `/newbot` 创建新Bot
3. 按提示设置Bot名称和用户名
4. 获取Bot Token（格式：`123456789:ABCdefGHIjklMNOpqrsTUVwxyz`）

### 3. 获取群组ID

有几种方法获取Telegram群组ID：

**方法1: 使用Bot**
1. 将Bot添加到目标群组
2. 在群组中发送任意消息
3. 访问：`https://api.telegram.org/bot<BOT_TOKEN>/getUpdates`
4. 查找 `chat.id` 字段（负数）

**方法2: 使用第三方Bot**
1. 添加 [@userinfobot](https://t.me/userinfobot) 到群组
2. 发送 `/start`，Bot会显示群组ID

**方法3: 转发消息**
1. 从群组转发消息到 [@userinfobot](https://t.me/userinfobot)
2. Bot会显示原群组信息

### 4. 配置文件

编辑 `config.yml`：

```yaml
# Telegram Bot配置
telegram:
  bot_token: '你的Bot Token'
  target_groups:
    - chat_id: -1001234567890  # 替换为实际群组ID
      name: '主要信号群'
      enabled: true
    - chat_id: -1001234567891
      name: '测试群'
      enabled: false  # 禁用此群组

# 过滤配置
filters:
  min_score_threshold: 0.3   # 最低评分阈值（绝对值），评分范围-1到1，低于此绝对值不发送
  sentiment_filter:          # 情绪过滤
    - '利多'
    - '利空'
    # - '中性'  # 注释掉不发送中性消息
```

## 使用方法

### 启动程序

```bash
# 正常启动
./run.sh

# 调试模式
./run.sh --debug

# 检查配置
./run.sh --check-config

# 测试Bot连接
./run.sh --test-bot
```

### 检查状态

```bash
# 检查依赖
./run.sh --check-deps

# 查看帮助
./run.sh --help
```

## 配置说明

### NATS配置

```yaml
nats:
  enabled: true
  servers:
    - 'nats://localhost:4222'
  subject: 'messages.notification'
```

### Telegram配置

```yaml
telegram:
  bot_token: 'YOUR_BOT_TOKEN'
  target_groups:
    - chat_id: -1001234567890
      name: '群组名称'
      enabled: true
  
  message_format:
    include_score: true      # 包含评分
    include_reason: true     # 包含分析理由
    include_author: true     # @原作者
    include_source: true     # 包含来源群组
    include_symbols: false    # 包含相关币种符号（如 $BTC $ETH）
    max_text_length: 500     # 最大文本长度
```

### 过滤配置

```yaml
filters:
  min_score_threshold: 0.3   # 最低评分阈值（绝对值），评分范围-1到1，低于此绝对值不发送
  sentiment_filter:          # 情绪过滤
    - '利多'
    - '利空'
    # - '中性'  # 注释掉不发送中性消息
```

### 限流配置

```yaml
rate_limit:
  enabled: true
  max_messages_per_minute: 10  # 每分钟最大消息数
  cooldown_seconds: 3          # 消息间隔秒数
```

### 错误处理

```yaml
error_handling:
  retry_attempts: 3    # 重试次数
  retry_delay: 5       # 重试间隔
  fallback_enabled: true
```

## 故障排除

### 常见问题

1. **Bot Token无效**
   ```
   ❌ Bot连接失败: Unauthorized
   ```
   - 检查Bot Token是否正确
   - 确认Bot未被删除或禁用

2. **群组ID错误**
   ```
   ❌ 群组不存在或Bot未加入
   ```
   - 确认群组ID正确（负数）
   - 确保Bot已加入目标群组
   - 检查Bot是否有发送消息权限

3. **NATS连接失败**
   ```
   ❌ NATS连接失败: Connection refused
   ```
   - 确认NATS服务器正在运行
   - 检查服务器地址和端口

4. **没有收到消息**
   - 检查analyze_agent是否正在运行
   - 确认NATS subject配置一致
   - 查看过滤器设置

### 调试技巧

1. **启用调试模式**:
   ```bash
   ./run.sh --debug
   ```

2. **检查配置**:
   ```bash
   ./run.sh --check-config
   ```

3. **测试Bot连接**:
   ```bash
   ./run.sh --test-bot
   ```

4. **测试Twitter链接功能**:
   ```bash
   python3 test_twitter_links.py
   ```

5. **查看日志**:
   ```bash
   tail -f notification.log
   ```

## 系统架构

```
telegramstream → messages.stream → analyze_agent → messages.notification → notification bot → Telegram群组
```

## 消息流程

1. **analyze_agent** 分析Telegram消息
2. 发送通知到 `messages.notification` subject
3. **notification bot** 接收通知消息
4. 应用过滤规则
5. 格式化消息内容
6. 发送到配置的Telegram群组

## 安全建议

1. **保护Bot Token**: 不要将Token提交到版本控制
2. **限制Bot权限**: 只给Bot必要的权限
3. **监控日志**: 定期检查错误日志
4. **备份配置**: 定期备份配置文件

## 扩展开发

### 添加新的消息格式

修改 `MessageFormatter.format_notification()` 方法：

```python
def format_notification(self, notification_data: Dict[str, Any]) -> str:
    # 自定义格式化逻辑
    pass
```

### 添加新的过滤规则

修改 `MessageFilter.should_send()` 方法：

```python
def should_send(self, notification_data: Dict[str, Any]) -> bool:
    # 自定义过滤逻辑
    pass
```

### 集成其他通知渠道

继承 `TelegramNotifier` 类，实现其他通知方式：

```python
class SlackNotifier(TelegramNotifier):
    async def send_notification(self, notification_data: Dict[str, Any]):
        # Slack通知实现
        pass
```

## 许可证

MIT License

## 支持

如有问题，请查看：
1. 本文档的故障排除部分
2. 项目Issues页面
3. 相关日志文件