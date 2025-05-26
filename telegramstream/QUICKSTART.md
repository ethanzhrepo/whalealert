# 快速开始指南

## 一键安装和配置

### 1. 运行安装脚本

```bash
cd telegramstream
./setup.sh
```

安装脚本会：
- ✅ 检查 conda 是否安装
- ✅ 创建名为 `telegram` 的 conda 环境（Python 3.9）
- ✅ 安装所有必需的依赖包
- ✅ 引导您配置 Telegram API 信息

### 2. 配置监控群组/频道

```bash
./run.sh config
```

程序会显示交互界面，让您：
- 查看所有已加入的群组和频道
- **已配置的群组/频道会自动显示为选中状态**
- 使用 ↑↓ 键选择，空格键勾选/取消
- 标题栏实时显示已选择的数量
- 使用 Tab 键在列表和按钮之间切换焦点
- 按 **F8** 键快速保存并退出
- 按 **ESC** 键退出（按两次确认）
- 保存选择的监控配置

### 快捷键说明

| 快捷键 | 功能 |
|--------|------|
| ↑↓ | 在列表中移动 |
| 空格 | 选择/取消选择当前项 |
| Tab | 向前切换焦点（列表 → 保存按钮 → 取消按钮） |
| Shift+Tab | 向后切换焦点 |
| F8 | 保存配置并退出 |
| ESC | 退出（按两次确认） |
| Ctrl+C | 强制退出 |

### 3. 启动监控

```bash
./run.sh start
```

程序开始实时监控配置的群组和频道，输出 JSON 格式的消息数据。

## 获取 Telegram API 凭据

1. 访问 [https://my.telegram.org](https://my.telegram.org)
2. 使用手机号登录
3. 点击 "API development tools"
4. 创建新应用，填写：
   - App title: `Telegram Monitor`
   - Short name: `telegram_monitor`
   - Platform: `Desktop`
5. 记录显示的 `api_id` 和 `api_hash`

## 配置 NATS 消息队列（可选）

编辑 `config.yml` 文件：

```yaml
nats:
  enabled: true
  servers: 
    - 'nats://localhost:4222'
  subject: 'telegram.messages'
```

## 常用命令

```bash
# 查看帮助
./run.sh help

# 重新配置监控群组
./run.sh config

# 启动监控
./run.sh start

# 激活 conda 环境（手动操作）
conda activate telegram
```

## 故障排除

### 1. conda 命令未找到
安装 Anaconda 或 Miniconda：
- [Anaconda](https://www.anaconda.com/products/distribution)
- [Miniconda](https://docs.conda.io/en/latest/miniconda.html)

### 2. Telegram 登录失败
- 确认 API ID 和 API Hash 正确
- 确认手机号格式包含国家代码（如 +8613812345678）
- 检查网络连接

### 3. 找不到群组/频道
- 确认已加入要监控的群组/频道
- 某些私有群组可能无法通过 API 访问

### 4. 消息接收延迟
- 检查网络连接
- 监控大量活跃群组时会有 API 限制
- 考虑减少监控的群组数量

## 输出示例

```json
{
  "type": "telegram.message",
  "timestamp": 1734567890123,
  "source": "telegram",
  "data": {
    "message_id": 12345,
    "chat_title": "Crypto Signals",
    "text": "🚀 WETH/USDC showing bullish momentum!",
    "extracted_data": {
      "symbols": ["WETH", "USDC"],
      "sentiment": "positive",
      "keywords": ["bullish", "momentum"]
    }
  }
}
```

## 进一步阅读

- [完整文档](README.md)
- [消息结构说明](message.md)
- [配置文件示例](config.yml.example) 