class TwitterContentMonitor {
  constructor() {
    this.isMonitoring = false;
    this.lastTimestamp = 0;
    this.processedTweets = new Set();
    this.observer = null;
    this.checkInterval = null;
    this.refreshInterval = null;
    this.maxMessages = 5;
    this.currentUrl = window.location.href;
    this.autoRefreshEnabled = false;
    this.refreshIntervalTime = 300000; // 5分钟
    this.lastRefreshTime = Date.now();
    
    console.log('Twitter Content Monitor 初始化');
    this.initialize();
  }

  async initialize() {
    // 监听来自background的消息
    chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
      this.handleMessage(message, sender, sendResponse);
      return true;
    });

    // 监听URL变化
    this.observeUrlChanges();

    // 检查当前页面是否需要监控
    await this.checkCurrentPage();
  }

  async handleMessage(message, sender, sendResponse) {
    try {
      switch (message.type) {
        case 'start_monitoring':
          await this.startMonitoring();
          sendResponse({ success: true });
          break;

        case 'stop_monitoring':
          this.stopMonitoring();
          sendResponse({ success: true });
          break;

        case 'nats_connected':
          console.log('NATS连接成功');
          break;

        case 'nats_disconnected':
          console.log('NATS连接断开');
          break;

        case 'nats_error':
          console.error('NATS连接错误:', message.error);
          break;

        case 'config_updated':
          await this.handleConfigUpdate(message.config);
          sendResponse({ success: true });
          break;

        default:
          sendResponse({ success: false, error: '未知消息类型' });
      }
    } catch (error) {
      console.error('处理消息失败:', error);
      sendResponse({ success: false, error: error.message });
    }
  }

  observeUrlChanges() {
    // 监听pushState和replaceState
    const originalPushState = history.pushState;
    const originalReplaceState = history.replaceState;

    history.pushState = function(...args) {
      originalPushState.apply(history, args);
      setTimeout(() => this.onUrlChange(), 100);
    }.bind(this);

    history.replaceState = function(...args) {
      originalReplaceState.apply(history, args);
      setTimeout(() => this.onUrlChange(), 100);
    }.bind(this);

    // 监听popstate事件
    window.addEventListener('popstate', () => {
      setTimeout(() => this.onUrlChange(), 100);
    });
  }

  async onUrlChange() {
    const newUrl = window.location.href;
    if (newUrl !== this.currentUrl) {
      console.log('URL变化:', this.currentUrl, '->', newUrl);
      this.currentUrl = newUrl;
      
      // 停止当前监控（包括自动刷新）
      this.stopMonitoring();
      
      // 检查新页面是否需要监控
      await this.checkCurrentPage();
    }
  }

  async checkCurrentPage() {
    try {
      // 获取配置
      const response = await chrome.runtime.sendMessage({ type: 'get_config' });
      if (!response.success) {
        console.error('获取配置失败');
        return;
      }

      const config = response.config;
      if (!config.enabled || !config.monitoredLists.length) {
        return;
      }

      // 检查当前URL是否匹配监控列表
      const isMonitoredList = config.monitoredLists.some(listUrl => {
        return this.isUrlMatch(this.currentUrl, listUrl);
      });

      if (isMonitoredList) {
        console.log('检测到监控列表页面，开始监控');
        await this.startMonitoring();
      }
    } catch (error) {
      console.error('检查当前页面失败:', error);
    }
  }

  async startMonitoring() {
    if (this.isMonitoring) {
      return;
    }

    console.log('开始监控Twitter列表');
    this.isMonitoring = true;

    // 通知background script
    try {
      await chrome.runtime.sendMessage({ type: 'start_monitoring' });
    } catch (error) {
      console.error('通知background失败:', error);
    }

    // 获取配置
    try {
      const response = await chrome.runtime.sendMessage({ type: 'get_config' });
      if (response.success) {
        this.maxMessages = response.config.maxMessages || 5;
        const checkInterval = response.config.checkInterval || 5000;
        this.autoRefreshEnabled = response.config.autoRefresh || false;
        this.refreshIntervalTime = response.config.refreshInterval || 300000;
        
        // 加载上次的时间戳
        this.lastTimestamp = await this.getLastTimestamp();
        
        // 开始定期检查
        this.startPeriodicCheck(checkInterval);
        
        // 设置DOM观察器
        this.setupDOMObserver();
        
        // 启动自动刷新（如果启用）
        if (this.autoRefreshEnabled) {
          this.startAutoRefresh();
        }
        
        // 立即检查一次
        await this.checkForNewTweets();
      }
    } catch (error) {
      console.error('获取配置失败:', error);
    }
  }

  stopMonitoring() {
    if (!this.isMonitoring) {
      return;
    }

    console.log('停止监控Twitter列表');
    this.isMonitoring = false;

    // 清理定时器
    if (this.checkInterval) {
      clearInterval(this.checkInterval);
      this.checkInterval = null;
    }

    // 清理自动刷新定时器
    if (this.refreshInterval) {
      clearInterval(this.refreshInterval);
      this.refreshInterval = null;
    }

    // 清理DOM观察器
    if (this.observer) {
      this.observer.disconnect();
      this.observer = null;
    }

    // 通知background script
    chrome.runtime.sendMessage({ type: 'stop_monitoring' }).catch(console.error);
  }

  startPeriodicCheck(interval) {
    this.checkInterval = setInterval(async () => {
      if (this.isMonitoring) {
        await this.checkForNewTweets();
      }
    }, interval);
  }

  startAutoRefresh() {
    if (!this.autoRefreshEnabled || this.refreshInterval) {
      return;
    }

    console.log(`启动自动刷新，间隔: ${this.refreshIntervalTime / 1000}秒`);
    this.lastRefreshTime = Date.now();

    this.refreshInterval = setInterval(() => {
      if (this.isMonitoring && this.autoRefreshEnabled) {
        this.performAutoRefresh();
      }
    }, this.refreshIntervalTime);
  }

  stopAutoRefresh() {
    if (this.refreshInterval) {
      console.log('停止自动刷新');
      clearInterval(this.refreshInterval);
      this.refreshInterval = null;
    }
  }

  async performAutoRefresh() {
    try {
      // 检查是否仍在被监控的列表页面
      const isStillMonitoredList = await this.isCurrentPageMonitored();
      if (!isStillMonitoredList) {
        console.log('当前页面不再是被监控的列表，停止自动刷新');
        this.stopAutoRefresh();
        return;
      }

      const now = Date.now();
      const timeSinceLastRefresh = now - this.lastRefreshTime;
      
      console.log(`执行自动刷新 (距离上次刷新: ${Math.round(timeSinceLastRefresh / 1000)}秒)`);
      
      // 记录刷新时间
      this.lastRefreshTime = now;
      
      // 刷新页面
      window.location.reload();
      
    } catch (error) {
      console.error('自动刷新失败:', error);
    }
  }

  async isCurrentPageMonitored() {
    try {
      const response = await chrome.runtime.sendMessage({ type: 'get_config' });
      if (!response.success) {
        return false;
      }

      const config = response.config;
      if (!config.enabled || !config.monitoredLists.length) {
        return false;
      }

      return config.monitoredLists.some(listUrl => {
        return this.isUrlMatch(this.currentUrl, listUrl);
      });
    } catch (error) {
      console.error('检查页面监控状态失败:', error);
      return false;
    }
  }

  async handleConfigUpdate(config) {
    try {
      console.log('处理配置更新');
      
      // 更新自动刷新配置
      const newAutoRefreshEnabled = config.autoRefresh || false;
      const newRefreshInterval = config.refreshInterval || 300000;
      
      // 如果自动刷新设置发生变化
      if (this.autoRefreshEnabled !== newAutoRefreshEnabled || 
          this.refreshIntervalTime !== newRefreshInterval) {
        
        this.autoRefreshEnabled = newAutoRefreshEnabled;
        this.refreshIntervalTime = newRefreshInterval;
        
        // 停止当前的自动刷新
        this.stopAutoRefresh();
        
        // 如果启用了自动刷新且正在监控，重新启动
        if (this.autoRefreshEnabled && this.isMonitoring) {
          const isMonitoredPage = await this.isCurrentPageMonitored();
          if (isMonitoredPage) {
            this.startAutoRefresh();
          }
        }
      }
      
      // 更新其他配置
      this.maxMessages = config.maxMessages || 5;
      
    } catch (error) {
      console.error('处理配置更新失败:', error);
    }
  }

  setupDOMObserver() {
    // 观察推文容器的变化
    const tweetContainer = document.querySelector('[data-testid="primaryColumn"]') || 
                          document.querySelector('[role="main"]') ||
                          document.body;

    if (tweetContainer) {
      this.observer = new MutationObserver((mutations) => {
        let hasNewTweets = false;
        mutations.forEach(mutation => {
          mutation.addedNodes.forEach(node => {
            if (node.nodeType === Node.ELEMENT_NODE) {
              // 检查是否包含推文元素
              if (node.querySelector && (
                  node.querySelector('[data-testid="tweet"]') ||
                  node.getAttribute('data-testid') === 'tweet'
                )) {
                hasNewTweets = true;
              }
            }
          });
        });

        if (hasNewTweets) {
          // 延迟检查，让DOM完全加载
          setTimeout(() => this.checkForNewTweets(), 1000);
        }
      });

      this.observer.observe(tweetContainer, {
        childList: true,
        subtree: true
      });
    }
  }

  async checkForNewTweets() {
    if (!this.isMonitoring) {
      return;
    }

    try {
      // 查找推文元素
      const tweetElements = document.querySelectorAll('[data-testid="tweet"]');
      const newTweets = [];

      for (const tweetElement of tweetElements) {
        const tweetData = this.extractTweetData(tweetElement);
        
        if (tweetData && 
            tweetData.id && 
            !this.processedTweets.has(tweetData.id) &&
            tweetData.timestamp > this.lastTimestamp) {
          
          newTweets.push(tweetData);
          this.processedTweets.add(tweetData.id);
        }
      }

      // 按时间戳排序，只取最新的几条
      newTweets.sort((a, b) => b.timestamp - a.timestamp);
      const tweetsToProcess = newTweets.slice(0, this.maxMessages);

      // 处理新推文
      for (const tweetData of tweetsToProcess) {
        await this.processTweet(tweetData);
      }

      // 更新时间戳
      if (tweetsToProcess.length > 0) {
        const latestTimestamp = Math.max(...tweetsToProcess.map(t => t.timestamp));
        this.lastTimestamp = latestTimestamp;
        await this.saveLastTimestamp(latestTimestamp);
      }

      // 清理旧的已处理推文ID（保持集合大小合理）
      if (this.processedTweets.size > 1000) {
        const tweetsArray = Array.from(this.processedTweets);
        this.processedTweets = new Set(tweetsArray.slice(-500));
      }

    } catch (error) {
      console.error('检查新推文失败:', error);
    }
  }

  extractTweetData(tweetElement) {
    try {
      // 提取推文文本
      const textElement = tweetElement.querySelector('[data-testid="tweetText"]');
      const text = textElement ? textElement.innerText : '';

      // 提取用户信息
      const userElement = tweetElement.querySelector('[data-testid="User-Name"]');
      const usernameElement = userElement ? userElement.querySelector('span') : null;
      const username = usernameElement ? usernameElement.innerText : '';
      
      // 提取时间戳
      const timeElement = tweetElement.querySelector('time');
      const timestamp = timeElement ? new Date(timeElement.getAttribute('datetime')).getTime() : Date.now();

      // 提取推文ID
      const linkElement = tweetElement.querySelector('a[href*="/status/"]');
      const tweetId = linkElement ? linkElement.href.match(/\/status\/(\d+)/)?.[1] : null;

      // 如果没有文本内容或ID，跳过
      if (!text.trim() || !tweetId) {
        return null;
      }

      // 提取媒体信息
      const mediaElements = tweetElement.querySelectorAll('[data-testid="tweetPhoto"], [data-testid="videoPlayer"]');
      const media = Array.from(mediaElements).map(el => ({
        type: el.getAttribute('data-testid') === 'tweetPhoto' ? 'photo' : 'video',
        url: el.querySelector('img')?.src || el.querySelector('video')?.src || ''
      }));

      // 提取链接
      const linkElements = tweetElement.querySelectorAll('a[href^="http"]:not([href*="/status/"])');
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
        urls: urls
      };
    } catch (error) {
      console.error('提取推文数据失败:', error);
      return null;
    }
  }

  async processTweet(tweetData) {
    try {
      console.log('处理新推文:', tweetData.username, tweetData.text.substring(0, 50) + '...');

      // 格式化消息
      const messageData = await this.formatMessage(tweetData);

      // 发送到background script
      const response = await chrome.runtime.sendMessage({
        type: 'send_message',
        data: messageData
      });

      if (response.success) {
        console.log('推文已发送到NATS');
      } else {
        console.error('发送推文失败:', response.error);
      }
    } catch (error) {
      console.error('处理推文失败:', error);
    }
  }

  async formatMessage(tweetData) {
    const extractedData = await this.extractStructuredData(tweetData.text);
    
    return {
      type: 'twitter.message',
      timestamp: Date.now(),
      source: 'twitter',
      sender: 'x_extension',
      data: {
        message_id: tweetData.id,
        list_url: this.currentUrl,
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

  async extractStructuredData(text) {
    if (!text) return {};

    // 提取加密货币符号
    const symbolPattern = /\b[A-Z]{2,10}\b/g;
    const symbols = [...new Set((text.match(symbolPattern) || []).filter(s => 
      ['BTC', 'ETH', 'SOL', 'ADA', 'DOT', 'LINK', 'UNI', 'AAVE', 'DOGE', 'SHIB'].includes(s) ||
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

    // 提取地址
    const ethAddressPattern = /0x[a-fA-F0-9]{40}/g;
    const solAddressPattern = /[1-9A-HJ-NP-Za-km-z]{32,44}/g;
    
    const addresses = {
      ethereum: [...new Set(text.match(ethAddressPattern) || [])],
      solana: [...new Set(text.match(solAddressPattern) || [])].filter(addr => 
        addr.length >= 32 && addr.length <= 44
      )
    };

    // 情绪分析
    const bullishKeywords = ['pump', 'moon', 'bullish', 'buy', 'long', 'rocket', 'up', 'rise', 'gain', '🚀', '📈'];
    const bearishKeywords = ['dump', 'bear', 'bearish', 'sell', 'short', 'crash', 'down', 'fall', 'loss', '📉'];
    
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

  async getLastTimestamp() {
    const key = `lastTimestamp_${this.hashUrl(this.currentUrl)}`;
    const result = await chrome.storage.local.get(key);
    return result[key] || 0;
  }

  async saveLastTimestamp(timestamp) {
    const key = `lastTimestamp_${this.hashUrl(this.currentUrl)}`;
    await chrome.storage.local.set({ [key]: timestamp });
  }

  hashUrl(url) {
    let hash = 0;
    for (let i = 0; i < url.length; i++) {
      const char = url.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash;
    }
    return Math.abs(hash).toString();
  }

  isUrlMatch(currentUrl, configuredUrl) {
    /**
     * 严格的URL匹配逻辑
     * 只有当前URL完全匹配配置的列表URL时才返回true
     */
    try {
      // 移除URL中的查询参数和片段标识符进行比较
      const cleanCurrentUrl = currentUrl.split('?')[0].split('#')[0];
      const cleanConfiguredUrl = configuredUrl.split('?')[0].split('#')[0];
      
      // 移除末尾的斜杠进行比较
      const normalizeUrl = (url) => url.replace(/\/$/, '');
      
      const normalizedCurrentUrl = normalizeUrl(cleanCurrentUrl);
      const normalizedConfiguredUrl = normalizeUrl(cleanConfiguredUrl);
      
      // 完全匹配
      if (normalizedCurrentUrl === normalizedConfiguredUrl) {
        return true;
      }
      
      // 检查是否是Twitter列表URL的变体
      // 支持的格式：
      // https://twitter.com/i/lists/123456789
      // https://x.com/i/lists/123456789
      // https://twitter.com/username/lists/listname
      // https://x.com/username/lists/listname
      
      const twitterListPattern = /^https?:\/\/(twitter\.com|x\.com)\/(.+)$/;
      const currentMatch = normalizedCurrentUrl.match(twitterListPattern);
      const configuredMatch = normalizedConfiguredUrl.match(twitterListPattern);
      
      if (currentMatch && configuredMatch) {
        // 提取路径部分进行比较
        const currentPath = currentMatch[2];
        const configuredPath = configuredMatch[2];
        
        // 路径完全匹配
        if (currentPath === configuredPath) {
          return true;
        }
        
        // 检查是否是同一个列表的不同域名 (twitter.com vs x.com)
        if (currentPath === configuredPath) {
          return true;
        }
      }
      
      return false;
    } catch (error) {
      console.error('URL匹配检查失败:', error);
      return false;
    }
  }
}

// 初始化内容监控器
const twitterMonitor = new TwitterContentMonitor(); 