# 🚀 Analyze Agent 快速开始指南

## 一键安装和运行

### 1. 安装程序依赖

```bash
./setup.sh
```

这个脚本会自动：
- ✅ 检查Python版本（需要3.8+）
- ✅ 安装所有Python依赖包
- ✅ 创建配置文件
- ✅ 运行基础测试

**注意**: 本程序是系统的一个组件，需要外部NATS服务器和LLM服务支持。

### 2. 启动外部服务

**在启动程序前，请确保以下服务已运行：**

**NATS服务器：**
```bash
# 使用Docker启动NATS
docker run -d --name nats -p 4222:4222 nats:latest
```

**LLM服务（选择其一）：**
```bash
# 选项1: Ollama（本地LLM）
ollama serve

# 选项2: 配置OpenAI API密钥（编辑config.yml）
# 选项3: 配置Anthropic API密钥（编辑config.yml）
```

### 3. 启动程序

```bash
./run.sh
```

这个脚本会自动：
- ✅ 检查配置文件
- ✅ 检查外部服务连接状态
- ✅ 运行预检测试
- ✅ 启动分析系统

## 🛠️ 高级用法

### 安装选项

```bash
# 基础安装
./setup.sh

# 如果安装过程中断，可以重新运行
./setup.sh
```

### 运行选项

```bash
# 正常启动（会检查外部服务连接）
./run.sh

# 只检查服务状态，不启动
./run.sh --check-only

# 跳过外部服务连接检查，直接启动
./run.sh --skip-service-check

# 显示帮助信息
./run.sh --help
```

## 📋 系统要求

### 必需
- **Python 3.8+** (支持python或python3命令)
- **pip** (Python包管理器)

### 外部服务依赖（需要手动启动）
- **NATS服务器** (端口4222) - 消息队列
- **LLM服务** - 以下之一:
  - Ollama (端口11434) - 本地LLM
  - OpenAI API - 云端LLM
  - Anthropic API - 云端LLM

### 可选
- **Docker** (用于启动NATS服务器)

## ⚙️ 配置说明

### LLM提供商配置

编辑 `config.yml` 文件：

**使用Ollama（默认）：**
```yaml
llm:
  provider: 'ollama'
  ollama:
    base_url: 'http://localhost:11434'
    model: 'llama3.1:8b'
```

**使用OpenAI：**
```yaml
llm:
  provider: 'openai'
  openai:
    api_key: 'your-openai-api-key'
    model: 'gpt-4o-mini'
```

**使用Anthropic：**
```yaml
llm:
  provider: 'anthropic'
  anthropic:
    api_key: 'your-anthropic-api-key'
    model: 'claude-3-haiku-20240307'
```

### NATS配置

```yaml
nats:
  enabled: true
  servers: 
    - 'nats://localhost:4222'
  subject: 
    - 'messages.stream'
```

## 🔧 外部服务设置

### NATS服务器

**选项1: 使用Docker（推荐）**
```bash
docker run -d --name nats -p 4222:4222 nats:latest
```

**选项2: 手动安装**
- 访问 https://nats.io/download/
- 下载并安装NATS服务器
- 启动: `nats-server`

### LLM服务

**选项1: Ollama（本地LLM）**
```bash
# 安装Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# 启动服务
ollama serve

# 下载模型
ollama pull llama3.1:8b
```

**选项2: OpenAI API**
- 获取API密钥: https://platform.openai.com/
- 在config.yml中配置api_key

**选项3: Anthropic API**
- 获取API密钥: https://console.anthropic.com/
- 在config.yml中配置api_key

## 🔍 故障排除

### 常见问题

1. **Python版本或命令问题**
   ```bash
   # 检查Python版本
   python --version
   python3 --version
   
   # 确保版本 >= 3.8
   ```

2. **NATS连接失败**
   ```bash
   # 检查NATS服务器
   nc -z localhost 4222
   
   # 启动NATS服务器
   docker run -d --name nats -p 4222:4222 nats:latest
   ```

3. **LLM服务不可用**
   ```bash
   # 检查Ollama服务
   curl http://localhost:11434/api/version
   
   # 启动Ollama服务
   ollama serve
   
   # 或者配置使用OpenAI/Anthropic API
   ```

4. **依赖安装失败**
   ```bash
   # 升级pip
   pip install --upgrade pip
   
   # 手动安装依赖
   pip install -r requirements.txt
   ```

5. **权限问题**
   ```bash
   # 给脚本添加执行权限
   chmod +x setup.sh run.sh
   ```

### 日志查看

```bash
# 查看详细日志
./run.sh

# 只检查服务状态
./run.sh --check-only

# 跳过服务检查直接启动
./run.sh --skip-service-check

# 运行测试
python simple_test.py
python test_agent.py
```

## 📊 验证安装

### 1. 运行基础测试
```bash
python simple_test.py
```

### 2. 运行完整测试（需要LLM服务）
```bash
python test_agent.py
```

### 3. 检查服务状态
```bash
./run.sh --check-only
```

## 🎯 使用流程

1. **安装**: `./setup.sh`
2. **启动外部服务**: 
   ```bash
   # NATS服务器
   docker run -d --name nats -p 4222:4222 nats:latest
   
   # LLM服务（选择其一）
   ollama serve  # 或配置API密钥
   ```
3. **配置**: 编辑 `config.yml`（如需要）
4. **启动**: `./run.sh`
5. **监控**: 查看控制台输出的分析结果
6. **停止**: 按 `Ctrl+C`

## 📈 输出示例

系统启动后，会实时输出分析结果：

```json
{
  "type": "analysis.sentiment",
  "timestamp": 1748142870135,
  "source": "analyze_agent",
  "sender": "sentiment_analysis_agent",
  "data": {
    "sentiment": "利多",
    "reason": "消息提到BTC突破新高，市场情绪积极",
    "score": 0.8,
    "analysis_time": "2024-12-23T10:30:00.000Z"
  }
}
```

## 🔧 开发模式

如果你想进行开发或调试：

```bash
# 手动启动各个组件
docker run -d --name nats -p 4222:4222 nats:latest
ollama serve  # 或配置其他LLM
python main.py

# 或者跳过服务检查
./run.sh --skip-service-check
```

## 🏗️ 系统集成

本程序设计为系统的一个组件：

```
TelegramStream → NATS → AnalyzeAgent → 分析结果
```

- **输入**: 来自TelegramStream的消息（通过NATS）
- **处理**: 使用LLM进行情绪分析
- **输出**: 结构化的分析结果（JSON格式）

## ⚠️ 重要提醒

**本程序只负责分析处理，不会启动任何外部服务。**

在运行程序前，请确保：
1. ✅ NATS服务器已启动并可访问
2. ✅ LLM服务已启动并可访问（Ollama/OpenAI/Anthropic）
3. ✅ 配置文件正确设置

## 📞 获取帮助

- 查看详细文档: `README.md`
- 运行帮助命令: `./run.sh --help`
- 检查配置: `python simple_test.py`

---

🎉 **Analyze Agent 已准备就绪，等待外部服务和消息输入！** 