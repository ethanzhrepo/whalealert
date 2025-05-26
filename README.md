# WhaleBot - Intelligent Cryptocurrency Trading Signal System

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![NATS](https://img.shields.io/badge/NATS-messaging-green.svg)](https://nats.io/)

A comprehensive, multi-agent cryptocurrency trading signal system that monitors Telegram channels and Twitter lists, analyzes messages using AI, and delivers intelligent notifications. Designed for high-frequency trading scenarios with low-latency message processing and semantic deduplication.

## 🌟 Key Features

- **🎯 Multi-Source Monitoring**: Real-time monitoring of Telegram channels/groups and Twitter lists
- **🐦 Twitter Integration**: Chrome extension for monitoring Twitter lists with auto-refresh and reconnection
- **🤖 AI-Powered Analysis**: Multi-agent sentiment analysis using LLM (Ollama/OpenAI/Anthropic)
- **🔄 Message Deduplication**: Semantic-level duplicate detection for Chinese-English mixed content
- **📊 Intelligent Filtering**: Advanced filtering based on sentiment scores and keywords
- **⚡ Low Latency**: Optimized for financial arbitrage scenarios with minimal processing delay
- **🔔 Smart Notifications**: Formatted Telegram notifications with rich content
- **🏗️ Microservices Architecture**: Modular design with NATS message queue integration
- **🌐 Multi-Language Support**: Handles Chinese-English mixed cryptocurrency content
- **🔄 Auto-Reconnection**: Robust connection management with exponential backoff
- **📱 Browser Extension**: Chrome extension for Twitter monitoring with real-time status

## 🏛️ System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  TelegramStream │───▶│                 │───▶│  Analyze Agent  │───▶│ Notification Bot│    │   X Extension   │
│                 │    │   NATS Queue    │    │                 │    │                 │    │                 │
│ • Message       │    │ messages.stream │    │ • Sentiment     │    │ • Telegram Bot  │    │ • Twitter Lists │
│   Monitoring    │    │ twitter.messages│    │   Analysis      │    │ • Multi-Group   │    │ • Auto-Refresh  │
│ • Data          │    │                 │    │ • Deduplication │    │ • Rich Format   │    │ • Real-time     │
│   Extraction    │    │ • Low Latency   │    │ • Multi-LLM     │    │ • Rate Limiting │    │ • WebSocket     │
│ • Real-time     │    │ • Reliable      │    │ • Filtering     │    │ • Error Retry   │    │ • Auto-Reconnect│
│                 │    │   Delivery      │    │ • JSON Safe     │    │                 │    │ • Status Monitor│
└─────────────────┘    │ • Scalable      │    └─────────────────┘    └─────────────────┘    └─────────────────┘
                       └─────────────────┘
```

## 📦 Components

### 1. TelegramStream
- **Purpose**: Monitor Telegram channels/groups for cryptocurrency signals
- **Features**: 
  - Multi-channel monitoring
  - Smart data extraction (addresses, symbols, URLs)
  - Sentiment keyword detection
  - Low-latency message processing
- **Location**: `./telegramstream/`

### 2. X Extension (NEW)
- **Purpose**: Chrome browser extension for monitoring Twitter lists
- **Features**:
  - Real-time Twitter list monitoring
  - Auto-refresh with configurable intervals (10s-3600s)
  - NATS WebSocket integration with auto-reconnection
  - Structured data extraction (crypto symbols, prices, addresses)
  - Sentiment analysis and duplicate prevention
  - User-friendly configuration interface
  - Connection status monitoring with visual indicators
- **Location**: `./x_extansion/`

### 3. Analyze Agent
- **Purpose**: AI-powered message analysis with deduplication
- **Features**:
  - Multi-agent sentiment analysis
  - Semantic message deduplication using BGE-M3 model
  - Support for Ollama, OpenAI, and Anthropic LLMs
  - Configurable similarity thresholds
  - Real-time processing with caching
  - JSON serialization safety for numpy types
  - Support for both Telegram and Twitter messages
- **Location**: `./analyze_agent/`

### 4. Notification Bot
- **Purpose**: Deliver formatted notifications to Telegram groups
- **Features**:
  - Multi-group broadcasting
  - Rich message formatting
  - Rate limiting and error handling
  - Configurable filtering
- **Location**: `./notification/`

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- NATS Server with WebSocket support
- Telegram API credentials
- LLM service (Ollama/OpenAI/Anthropic)
- Chrome browser (for X Extension)

### 1. Clone Repository

```bash
git clone https://github.com/ethanzhrepo/whalealert.git
cd whalebot
```

### 2. Setup NATS Server with WebSocket Support

```bash
# Using Docker with WebSocket enabled
docker run -p 4222:4222 -p 8222:8222 nats:latest -js -m 8222

# Or install locally with WebSocket support
# Visit: https://docs.nats.io/running-a-nats-service/introduction/installation
```

### 3. Setup TelegramStream

```bash
cd telegramstream
./setup.sh
cp config.yml.example config.yml
# Edit config.yml with your Telegram API credentials
python main.py config  # Interactive channel selection
python main.py start   # Start monitoring
```

### 4. Setup X Extension

```bash
cd ../x_extansion
# Open Chrome and go to chrome://extensions/
# Enable "Developer mode"
# Click "Load unpacked" and select the x_extansion folder
# Configure NATS servers and Twitter lists in the extension popup
```

### 5. Setup Analyze Agent

```bash
cd ../analyze_agent
./setup.sh
cp config.yml.example config.yml
# Configure LLM provider and deduplication settings
# Add 'twitter.messages' to NATS subjects
python main.py  # Start analysis service
```

### 6. Setup Notification Bot

```bash
cd ../notification
./setup.sh
cp config.yml.example config.yml
# Configure Telegram Bot token and target groups
./run.sh  # Start notification service
```

## ⚙️ Configuration

### TelegramStream Configuration

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

### X Extension Configuration

```yaml
# Configure via Chrome extension popup
nats_servers: ['ws://localhost:4222']
nats_subject: 'twitter.messages'
monitored_lists: 
  - 'https://twitter.com/i/lists/123456789'
auto_refresh: true
refresh_interval: 300  # seconds (minimum 10s)
max_messages: 5
```

### Analyze Agent Configuration

```yaml
# LLM Configuration
llm:
  provider: 'ollama'  # ollama/openai/anthropic
  ollama:
    base_url: 'http://localhost:11434'
    model: 'llama3.1:8b'

# NATS Configuration (Updated)
nats:
  enabled: true
  servers: ['nats://localhost:4222']
  subject:
    - 'messages.stream'    # Telegram messages
    - 'twitter.messages'   # Twitter messages (NEW)

# Message Deduplication
deduplication:
  enabled: true
  model_name: 'BAAI/bge-m3'
  similarity_threshold: 0.85
  time_window_hours: 2

# Agent Configuration
agents:
  sentiment_analysis:
    enabled: true
```

### Notification Bot Configuration

```yaml
telegram:
  bot_token: 'your_bot_token'
  target_groups:
    - chat_id: -1001234567890
      name: 'Main Signals'
      enabled: true
```

## 🔧 Advanced Features

### X Extension Features

#### Auto-Reconnection
- **Exponential Backoff**: 1s → 2s → 4s → 8s → 16s → 30s max
- **Persistent Retry**: Continues after max attempts with 60s reset
- **Visual Status**: Real-time connection indicators with animations
- **Manual Control**: Enable/disable reconnection as needed

#### Auto-Refresh
- **Smart Detection**: Only refreshes monitored Twitter list pages
- **Configurable Interval**: 10 seconds to 1 hour
- **Safety Mechanisms**: Stops when page changes or monitoring disabled
- **Performance Optimized**: Minimal resource usage

#### Data Extraction
- **Crypto Symbols**: BTC, ETH, SOL, and custom patterns
- **Price Information**: USD/USDT/USDC price detection
- **Blockchain Addresses**: Ethereum and Solana address extraction
- **Sentiment Analysis**: Keyword-based bullish/bearish detection

### Message Deduplication

The system includes sophisticated semantic deduplication:

- **BGE-M3 Model**: Handles Chinese-English mixed content
- **FAISS Indexing**: Fast similarity search
- **Time Windows**: Configurable deduplication periods
- **Similarity Thresholds**: Adjustable detection sensitivity
- **JSON Safety**: Proper handling of numpy types for serialization

Example duplicate detection:
```
Original: "Binance 将上线新币 DOGE/USDT Trading Pair"
Similar:  "币安即将推出 DOGE/USDT 交易对"
Similarity: 0.87 > 0.85 threshold → Marked as duplicate
```

### Multi-LLM Support

Support for multiple LLM providers:

- **Ollama**: Local deployment with models like Llama, Qwen
- **OpenAI**: GPT-4, GPT-3.5-turbo
- **Anthropic**: Claude-3 series

### Smart Data Extraction

Automatic extraction of:
- **Blockchain Addresses**: Ethereum, Solana, Bitcoin
- **Token Symbols**: 2-10 character uppercase combinations
- **URLs**: DEX trackers, blockchain explorers, exchanges
- **Sentiment Keywords**: Bullish/bearish indicators

## 📊 Message Flow

### Telegram Message Flow
```json
{
  "type": "telegram.message",
  "timestamp": 1734567890123,
  "source": "telegram",
  "data": {
    "message_id": 12345,
    "chat_title": "Crypto Signals",
    "text": "🚀 BTC突破10万美元！牛市来了！",
    "extracted_data": {
      "symbols": ["BTC"],
      "sentiment": "positive",
      "keywords": ["突破", "牛市"]
    }
  }
}
```

### Twitter Message Flow (NEW)
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

### Analysis Result
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

## 🧪 Testing

Each component includes comprehensive testing:

```bash
# Test TelegramStream
cd telegramstream && python test_symbol_util.py

# Test X Extension
# Open x_extansion/test.html in Chrome
# Open x_extansion/test_reconnect.html for reconnection testing
# Open x_extansion/test_autorefresh.html for auto-refresh testing

# Test Analyze Agent
cd analyze_agent && python test_deduplication.py

# Test Notification Bot
cd notification && python test_notification.py
```

## 📚 Documentation

### Core Components
- [TelegramStream Guide](./telegramstream/README.md)
- [X Extension Guide](./x_extansion/README.md)
- [Analyze Agent Guide](./analyze_agent/README.md)
- [Notification Bot Guide](./notification/README.md)

### Specialized Guides
- [X Extension Installation](./x_extansion/INSTALLATION.md)
- [X Extension Reconnection Guide](./x_extansion/RECONNECT_GUIDE.md)
- [Message Deduplication Guide](./analyze_agent/DEDUPLICATION_GUIDE.md)
- [Keras Compatibility Fix](./analyze_agent/KERAS_FIX_GUIDE.md)

## 🔧 Troubleshooting

### Common Issues

1. **NATS Connection Failed**
   - Ensure NATS server is running with WebSocket support on port 4222
   - Check firewall settings for both TCP and WebSocket connections
   - Verify WebSocket endpoint: `ws://localhost:4222`

2. **X Extension Issues**
   - Reload extension after code changes
   - Check Chrome developer console for errors
   - Verify Twitter list URLs are accessible
   - Ensure NATS WebSocket connection is established

3. **Telegram API Issues**
   - Verify API credentials
   - Check account permissions for target channels

4. **LLM Connection Problems**
   - For Ollama: Ensure service is running on localhost:11434
   - For OpenAI/Anthropic: Verify API keys

5. **JSON Serialization Errors**
   - Fixed in latest version with numpy type sanitization
   - Restart analyze_agent if issues persist

6. **Keras 3 Compatibility**
   - Run: `python3 analyze_agent/fix_keras_compatibility.py`
   - Or install: `pip install tf-keras`

### Performance Optimization

- **Memory**: Adjust deduplication cache size based on available RAM
- **Latency**: Tune NATS buffer sizes for high-frequency scenarios
- **Accuracy**: Adjust similarity thresholds based on content characteristics
- **Browser Performance**: Use longer auto-refresh intervals for better performance

## 🆕 Recent Updates

### v2.0.0 - Twitter Integration
- **NEW**: X Extension for Twitter list monitoring
- **NEW**: Auto-refresh functionality with configurable intervals
- **NEW**: NATS auto-reconnection with exponential backoff
- **NEW**: Real-time connection status monitoring
- **FIXED**: JSON serialization issues with numpy types
- **IMPROVED**: Message deduplication for cross-platform content
- **ENHANCED**: Configuration management and user interface

### Key Improvements
- Support for both Telegram and Twitter message sources
- Robust connection management with visual feedback
- Enhanced data extraction for cryptocurrency content
- Better error handling and recovery mechanisms

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [NATS](https://nats.io/) for reliable messaging
- [BGE-M3](https://huggingface.co/BAAI/bge-m3) for multilingual embeddings
- [LangChain](https://langchain.com/) for LLM integration
- [Telegram](https://telegram.org/) for messaging platform
- [Chrome Extensions API](https://developer.chrome.com/docs/extensions/) for browser integration

## 📞 Support

- 💬 Twitter [@0x99_Ethan](https://x.com/0x99_Ethan)
- 🐛 Issues: [GitHub Issues](https://github.com/ethanzhrepo/whalealert/issues)

---

⭐ **Star this repository if you find it useful!**
