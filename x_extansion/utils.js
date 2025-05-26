// 配置管理类
class Config {
  static async load() {
    const result = await chrome.storage.sync.get({
      natsServers: ['ws://localhost:4222'],
      natsSubject: 'twitter.messages',
      monitoredLists: [],
      enabled: false,
      maxMessages: 5,
      checkInterval: 5000, // 5秒检查一次
      autoRefresh: false, // 自动刷新开关
      refreshInterval: 300000 // 自动刷新间隔（5分钟，最低10秒）
    });
    return result;
  }

  static async save(config) {
    await chrome.storage.sync.set(config);
  }

  static async get(key) {
    const config = await this.load();
    return config[key];
  }

  static async set(key, value) {
    const config = await this.load();
    config[key] = value;
    await this.save(config);
  }
}

// NATS WebSocket连接管理
class NATSConnection {
  constructor() {
    this.ws = null;
    this.connected = false;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 10; // 增加最大重连次数
    this.reconnectDelay = 1000;
    this.servers = [];
    this.reconnectTimer = null;
    this.isReconnecting = false;
    this.shouldReconnect = true; // 控制是否应该重连
    this.onConnectionChange = null; // 连接状态变化回调
  }

  async connect(servers) {
    this.servers = servers; // 保存服务器列表用于重连
    this.shouldReconnect = true;
    
    for (const server of servers) {
      try {
        const wsUrl = server.replace('nats://', 'ws://').replace('nats-ws://', 'ws://');
        console.log(`尝试连接到 NATS: ${wsUrl}`);
        
        this.ws = new WebSocket(wsUrl);
        
        return new Promise((resolve, reject) => {
          const timeout = setTimeout(() => {
            if (this.ws && this.ws.readyState === WebSocket.CONNECTING) {
              this.ws.close();
            }
            reject(new Error('连接超时'));
          }, 10000); // 10秒超时

          this.ws.onopen = () => {
            clearTimeout(timeout);
            console.log('NATS WebSocket连接成功');
            this.connected = true;
            this.reconnectAttempts = 0;
            this.isReconnecting = false;
            
            // 发送CONNECT命令以建立NATS协议连接
            const connectMsg = JSON.stringify({
              verbose: false,
              pedantic: false,
              tls_required: false,
              name: 'x_extension',
              lang: 'javascript',
              version: '1.0.0'
            });
            this.ws.send(`CONNECT ${connectMsg}\r\n`);
            
            // 通知连接状态变化
            if (this.onConnectionChange) {
              this.onConnectionChange(true);
            }
            
            resolve();
          };

          this.ws.onerror = (error) => {
            clearTimeout(timeout);
            console.error('NATS WebSocket连接错误:', error);
            reject(error);
          };

          this.ws.onclose = (event) => {
            clearTimeout(timeout);
            console.log(`NATS WebSocket连接关闭 (code: ${event.code}, reason: ${event.reason})`);
            this.connected = false;
            
            // 通知连接状态变化
            if (this.onConnectionChange) {
              this.onConnectionChange(false);
            }
            
            // 只有在应该重连且不是手动断开的情况下才重连
            if (this.shouldReconnect && event.code !== 1000) {
              this.scheduleReconnect();
            }
          };

          this.ws.onmessage = (event) => {
            // 处理NATS服务器的响应消息
            const message = event.data.toString();
            console.log('收到NATS消息:', message.substring(0, 100));
            
            // 处理INFO消息
            if (message.startsWith('INFO')) {
              console.log('收到NATS服务器信息');
            }
            // 处理PING消息
            else if (message.startsWith('PING')) {
              this.ws.send('PONG\r\n');
            }
          };
        });
      } catch (error) {
        console.error(`连接到 ${server} 失败:`, error);
        continue;
      }
    }
    throw new Error('所有NATS服务器连接失败');
  }

  scheduleReconnect() {
    if (!this.shouldReconnect || this.isReconnecting) {
      return;
    }

    // 清除之前的重连定时器
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
    }

    this.isReconnecting = true;
    this.reconnectAttempts++;
    
    // 计算延迟时间，使用指数退避算法，但有最大限制
    const baseDelay = this.reconnectDelay;
    const maxDelay = 30000; // 最大30秒
    const delay = Math.min(baseDelay * Math.pow(2, this.reconnectAttempts - 1), maxDelay);
    
    console.log(`${delay}ms后尝试重连 (第${this.reconnectAttempts}次/${this.maxReconnectAttempts})`);
    
    this.reconnectTimer = setTimeout(async () => {
      if (!this.shouldReconnect) {
        this.isReconnecting = false;
        return;
      }

      try {
        await this.connect(this.servers);
        console.log('重连成功');
      } catch (error) {
        console.error('重连失败:', error);
        this.isReconnecting = false;
        
        // 如果还没达到最大重连次数，继续尝试
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
          this.scheduleReconnect();
        } else {
          console.warn(`已达到最大重连次数 (${this.maxReconnectAttempts})，停止重连`);
          console.log('将在60秒后重置重连计数器并继续尝试...');
          
          // 60秒后重置重连计数器，继续尝试
          setTimeout(() => {
            if (this.shouldReconnect && !this.connected) {
              console.log('重置重连计数器，继续尝试连接...');
              this.reconnectAttempts = 0;
              this.scheduleReconnect();
            }
          }, 60000);
        }
      }
    }, delay);
  }

  async publish(subject, data) {
    if (!this.connected || !this.ws || this.ws.readyState !== WebSocket.OPEN) {
      throw new Error('NATS未连接');
    }

    try {
      // 确保数据是字符串格式
      const dataStr = typeof data === 'string' ? data : JSON.stringify(data);
      const dataBytes = new TextEncoder().encode(dataStr);
      
      // NATS协议消息格式: PUB <subject> [reply-to] <#bytes>\r\n[payload]\r\n
      const message = `PUB ${subject} ${dataBytes.length}\r\n${dataStr}\r\n`;
      
      console.log(`发送NATS消息到主题 ${subject}, 大小: ${dataBytes.length} bytes`);
      this.ws.send(message);
    } catch (error) {
      console.error('发送NATS消息失败:', error);
      throw error;
    }
  }

  disconnect() {
    this.shouldReconnect = false; // 停止重连
    
    // 清除重连定时器
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    
    if (this.ws) {
      this.ws.close(1000, 'Manual disconnect'); // 正常关闭
      this.ws = null;
    }
    
    this.connected = false;
    this.isReconnecting = false;
    this.reconnectAttempts = 0;
    
    console.log('NATS连接已手动断开');
  }

  // 新增方法：启用重连
  enableReconnect() {
    this.shouldReconnect = true;
    console.log('已启用NATS自动重连');
  }

  // 新增方法：禁用重连
  disableReconnect() {
    this.shouldReconnect = false;
    
    // 清除重连定时器
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    
    this.isReconnecting = false;
    console.log('已禁用NATS自动重连');
  }

  // 新增方法：获取连接状态
  getStatus() {
    return {
      connected: this.connected,
      reconnecting: this.isReconnecting,
      reconnectAttempts: this.reconnectAttempts,
      maxReconnectAttempts: this.maxReconnectAttempts,
      shouldReconnect: this.shouldReconnect
    };
  }

  // 新增方法：设置连接状态变化回调
  setConnectionChangeCallback(callback) {
    this.onConnectionChange = callback;
  }
}

// 消息提取和格式化工具
class MessageExtractor {
  static extractTweetData(tweetElement) {
    try {
      // 提取推文文本
      const textElement = tweetElement.querySelector('[data-testid="tweetText"]');
      const text = textElement ? textElement.innerText : '';

      // 提取用户信息
      const userElement = tweetElement.querySelector('[data-testid="User-Name"]');
      const username = userElement ? userElement.querySelector('span')?.innerText : '';
      
      // 提取时间戳
      const timeElement = tweetElement.querySelector('time');
      const timestamp = timeElement ? new Date(timeElement.getAttribute('datetime')).getTime() : Date.now();

      // 提取推文ID (从链接中)
      const linkElement = tweetElement.querySelector('a[href*="/status/"]');
      const tweetId = linkElement ? linkElement.href.match(/\/status\/(\d+)/)?.[1] : null;

      // 提取媒体信息
      const mediaElements = tweetElement.querySelectorAll('[data-testid="tweetPhoto"], [data-testid="videoPlayer"]');
      const media = Array.from(mediaElements).map(el => ({
        type: el.getAttribute('data-testid') === 'tweetPhoto' ? 'photo' : 'video',
        url: el.querySelector('img')?.src || el.querySelector('video')?.src || ''
      }));

      // 提取链接
      const linkElements = tweetElement.querySelectorAll('a[href^="http"]');
      const urls = Array.from(linkElements).map(link => ({
        url: link.href,
        display_url: link.innerText
      }));

      return {
        id: tweetId,
        text: text,
        username: username,
        timestamp: timestamp,
        media: media,
        urls: urls,
        raw_element: tweetElement.outerHTML.substring(0, 1000) // 限制大小
      };
    } catch (error) {
      console.error('提取推文数据失败:', error);
      return null;
    }
  }

  static async extractStructuredData(text) {
    if (!text) return {};

    // 提取加密货币符号 (简化版本)
    const symbolPattern = /\b[A-Z]{2,10}\b/g;
    const symbols = [...new Set((text.match(symbolPattern) || []).filter(s => 
      ['BTC', 'ETH', 'SOL', 'ADA', 'DOT', 'LINK', 'UNI', 'AAVE'].includes(s) ||
      s.length >= 3
    ))];

    // 提取价格信息
    const pricePattern = /\$?(\d+(?:\.\d+)?)\s*(?:USD|USDT|USDC|\$)/gi;
    const prices = [];
    let match;
    while ((match = pricePattern.exec(text)) !== null) {
      prices.push({
        price: parseFloat(match[1]),
        currency: 'USD'
      });
    }

    // 提取地址 (简化版本)
    const ethAddressPattern = /0x[a-fA-F0-9]{40}/g;
    const solAddressPattern = /[1-9A-HJ-NP-Za-km-z]{32,44}/g;
    
    const addresses = {
      ethereum: [...new Set(text.match(ethAddressPattern) || [])],
      solana: [...new Set(text.match(solAddressPattern) || [])].filter(addr => 
        addr.length >= 32 && addr.length <= 44
      )
    };

    // 情绪关键词分析
    const bullishKeywords = ['pump', 'moon', 'bullish', 'buy', 'long', 'rocket', 'up', 'rise', 'gain'];
    const bearishKeywords = ['dump', 'bear', 'bearish', 'sell', 'short', 'crash', 'down', 'fall', 'loss'];
    
    const textLower = text.toLowerCase();
    const bullishCount = bullishKeywords.filter(kw => textLower.includes(kw)).length;
    const bearishCount = bearishKeywords.filter(kw => textLower.includes(kw)).length;
    
    let sentiment = 'neutral';
    if (bullishCount > bearishCount) sentiment = 'positive';
    else if (bearishCount > bullishCount) sentiment = 'negative';

    return {
      symbols,
      prices,
      addresses,
      sentiment,
      keywords: [...bullishKeywords, ...bearishKeywords].filter(kw => textLower.includes(kw))
    };
  }

  static async formatMessage(tweetData, listUrl) {
    const extractedData = await this.extractStructuredData(tweetData.text);
    
    return {
      type: 'twitter.message',
      timestamp: Date.now(),
      source: 'twitter',
      sender: 'x_extension',
      data: {
        message_id: tweetData.id,
        list_url: listUrl,
        user_id: tweetData.username,
        username: tweetData.username,
        date: tweetData.timestamp,
        text: tweetData.text,
        raw_text: tweetData.text,
        media: tweetData.media,
        urls: tweetData.urls,
        extracted_data: extractedData
      }
    };
  }
}

// 时间戳管理
class TimestampManager {
  static async getLastTimestamp(listUrl) {
    const key = `lastTimestamp_${this.hashUrl(listUrl)}`;
    const result = await chrome.storage.local.get(key);
    return result[key] || 0;
  }

  static async setLastTimestamp(listUrl, timestamp) {
    const key = `lastTimestamp_${this.hashUrl(listUrl)}`;
    await chrome.storage.local.set({ [key]: timestamp });
  }

  static hashUrl(url) {
    // 简单的URL哈希函数
    let hash = 0;
    for (let i = 0; i < url.length; i++) {
      const char = url.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // 转换为32位整数
    }
    return Math.abs(hash).toString();
  }
}

// 导出工具类
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { Config, NATSConnection, MessageExtractor, TimestampManager };
} 