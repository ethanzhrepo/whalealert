// 导入工具类
importScripts('utils.js');

class TwitterMonitorBackground {
  constructor() {
    this.natsConnection = null;
    this.monitoringTabs = new Set();
    this.isEnabled = false;
  }

  async initialize() {
    console.log('Twitter Monitor Background 初始化');
    
    // 监听扩展安装/启动
    chrome.runtime.onStartup.addListener(() => this.onStartup());
    chrome.runtime.onInstalled.addListener(() => this.onInstalled());
    
    // 监听来自content script的消息
    chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
      this.handleMessage(message, sender, sendResponse);
      return true; // 保持消息通道开放
    });

    // 监听标签页更新
    chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
      this.onTabUpdated(tabId, changeInfo, tab);
    });

    // 监听标签页关闭
    chrome.tabs.onRemoved.addListener((tabId) => {
      this.monitoringTabs.delete(tabId);
    });

    // 加载配置并初始化NATS连接
    await this.loadConfigAndConnect();
  }

  async onStartup() {
    console.log('扩展启动');
    await this.loadConfigAndConnect();
  }

  async onInstalled() {
    console.log('扩展安装完成');
    // 设置默认配置
    const defaultConfig = {
      natsServers: ['ws://localhost:4222'],
      natsSubject: 'twitter.messages',
      monitoredLists: [],
      enabled: false,
      maxMessages: 5,
      checkInterval: 5000,
      autoRefresh: false,
      refreshInterval: 300000 // 最低10秒
    };
    await Config.save(defaultConfig);
  }

  async loadConfigAndConnect() {
    try {
      const config = await Config.load();
      this.isEnabled = config.enabled;
      
      if (this.isEnabled && config.natsServers.length > 0) {
        await this.connectToNATS(config.natsServers);
      }
    } catch (error) {
      console.error('加载配置失败:', error);
    }
  }

  async connectToNATS(servers) {
    try {
      if (this.natsConnection) {
        this.natsConnection.disconnect();
      }
      
      this.natsConnection = new NATSConnection();
      
      // 设置连接状态变化回调
      this.natsConnection.setConnectionChangeCallback((connected) => {
        if (connected) {
          console.log('NATS连接已建立');
          this.broadcastToMonitoringTabs({ type: 'nats_connected' });
        } else {
          console.log('NATS连接已断开');
          this.broadcastToMonitoringTabs({ type: 'nats_disconnected' });
        }
      });
      
      await this.natsConnection.connect(servers);
      console.log('NATS连接成功');
      
    } catch (error) {
      console.error('NATS连接失败:', error);
      this.broadcastToMonitoringTabs({ type: 'nats_error', error: error.message });
      
      // 如果监控已启用，确保重连功能开启
      if (this.isEnabled && this.natsConnection) {
        this.natsConnection.enableReconnect();
      }
    }
  }

  async handleMessage(message, sender, sendResponse) {
    try {
      switch (message.type) {
        case 'get_config':
          const config = await Config.load();
          sendResponse({ success: true, config });
          break;

        case 'save_config':
          await Config.save(message.config);
          const wasEnabled = this.isEnabled;
          this.isEnabled = message.config.enabled;
          
          // 处理监控状态变化
          if (this.isEnabled && message.config.natsServers.length > 0) {
            // 启用监控
            await this.connectToNATS(message.config.natsServers);
          } else if (!this.isEnabled && this.natsConnection) {
            // 禁用监控
            this.natsConnection.disableReconnect(); // 禁用自动重连
            this.natsConnection.disconnect();
            this.natsConnection = null;
          }
          
          // 如果从禁用变为启用，或者服务器配置改变，重新连接
          if (this.isEnabled && this.natsConnection && wasEnabled) {
            this.natsConnection.enableReconnect(); // 确保重连功能开启
          }
          
          // 通知所有监控标签页配置已更新
          this.broadcastToMonitoringTabs({ 
            type: 'config_updated', 
            config: message.config 
          });
          
          sendResponse({ success: true });
          break;

        case 'start_monitoring':
          if (sender.tab) {
            this.monitoringTabs.add(sender.tab.id);
            console.log(`开始监控标签页 ${sender.tab.id}: ${sender.tab.url}`);
          }
          sendResponse({ success: true, enabled: this.isEnabled });
          break;

        case 'stop_monitoring':
          if (sender.tab) {
            this.monitoringTabs.delete(sender.tab.id);
            console.log(`停止监控标签页 ${sender.tab.id}`);
          }
          sendResponse({ success: true });
          break;

        case 'send_message':
          await this.sendMessageToNATS(message.data);
          sendResponse({ success: true });
          break;

        case 'get_status':
          const natsStatus = this.natsConnection ? this.natsConnection.getStatus() : {
            connected: false,
            reconnecting: false,
            reconnectAttempts: 0,
            maxReconnectAttempts: 0,
            shouldReconnect: false
          };
          
          sendResponse({
            success: true,
            status: {
              enabled: this.isEnabled,
              natsConnected: natsStatus.connected,
              natsReconnecting: natsStatus.reconnecting,
              natsReconnectAttempts: natsStatus.reconnectAttempts,
              natsMaxReconnectAttempts: natsStatus.maxReconnectAttempts,
              natsShouldReconnect: natsStatus.shouldReconnect,
              monitoringTabs: this.monitoringTabs.size
            }
          });
          break;

        default:
          sendResponse({ success: false, error: '未知消息类型' });
      }
    } catch (error) {
      console.error('处理消息失败:', error);
      sendResponse({ success: false, error: error.message });
    }
  }

  async sendMessageToNATS(messageData) {
    if (!this.natsConnection || !this.natsConnection.connected) {
      throw new Error('NATS未连接');
    }

    const config = await Config.load();
    const subject = config.natsSubject || 'twitter.messages';
    const messageJson = JSON.stringify(messageData);
    
    await this.natsConnection.publish(subject, messageJson);
    console.log(`消息已发送到NATS: ${subject}`, messageData);
  }

  onTabUpdated(tabId, changeInfo, tab) {
    // 检查是否是Twitter列表页面
    if (changeInfo.status === 'complete' && tab.url) {
      this.isTwitterListUrl(tab.url).then(isTwitterList => {
        if (isTwitterList && this.isEnabled) {
          // 通知content script开始监控
          chrome.tabs.sendMessage(tabId, { type: 'start_monitoring' }).catch(() => {
            // 忽略错误，可能是页面还没有加载content script
          });
        }
      });
    }
  }

  async isTwitterListUrl(url) {
    try {
      const config = await Config.load();
      if (!config.monitoredLists || config.monitoredLists.length === 0) {
        return false;
      }
      
      return config.monitoredLists.some(listUrl => {
        // 简单的URL匹配
        return url.includes(listUrl) || listUrl.includes(url.split('?')[0]);
      });
    } catch (error) {
      console.error('检查URL匹配失败:', error);
      return false;
    }
  }

  broadcastToMonitoringTabs(message) {
    this.monitoringTabs.forEach(tabId => {
      chrome.tabs.sendMessage(tabId, message).catch(() => {
        // 标签页可能已关闭，从集合中移除
        this.monitoringTabs.delete(tabId);
      });
    });
  }
}

// 初始化后台服务
const twitterMonitor = new TwitterMonitorBackground();
twitterMonitor.initialize().catch(console.error); 