class PopupManager {
  constructor() {
    this.config = null;
    this.status = null;
    this.initialize();
  }

  async initialize() {
    console.log('Popup Manager 初始化');
    
    // 绑定事件监听器
    this.bindEventListeners();
    
    // 加载配置和状态
    await this.loadConfig();
    await this.updateStatus();
    
    // 定期更新状态
    setInterval(() => this.updateStatus(), 2000);
  }

  bindEventListeners() {
    // 启用/禁用切换
    document.getElementById('enableToggle').addEventListener('click', () => {
      this.toggleEnabled();
    });

    // 自动刷新切换
    document.getElementById('autoRefreshToggle').addEventListener('click', () => {
      this.toggleAutoRefresh();
    });

    // 添加列表
    document.getElementById('addListBtn').addEventListener('click', () => {
      this.addList();
    });

    // 保存配置
    document.getElementById('saveBtn').addEventListener('click', () => {
      this.saveConfig();
    });

    // 回车键添加列表
    document.getElementById('newListUrl').addEventListener('keypress', (e) => {
      if (e.key === 'Enter') {
        this.addList();
      }
    });
  }

  async loadConfig() {
    try {
      const response = await chrome.runtime.sendMessage({ type: 'get_config' });
      if (response.success) {
        this.config = response.config;
        this.updateUI();
      } else {
        this.showError('加载配置失败');
      }
    } catch (error) {
      console.error('加载配置失败:', error);
      this.showError('加载配置失败: ' + error.message);
    }
  }

  async updateStatus() {
    try {
      const response = await chrome.runtime.sendMessage({ type: 'get_status' });
      if (response.success) {
        this.status = response.status;
        this.updateStatusUI();
      }
    } catch (error) {
      console.error('更新状态失败:', error);
    }
  }

  updateUI() {
    if (!this.config) return;

    // 更新NATS配置
    document.getElementById('natsServers').value = this.config.natsServers.join('\n');
    document.getElementById('natsSubject').value = this.config.natsSubject;

    // 更新监控设置
    document.getElementById('maxMessages').value = this.config.maxMessages;
    document.getElementById('checkInterval').value = this.config.checkInterval;

    // 更新自动刷新设置
    document.getElementById('refreshInterval').value = this.config.refreshInterval / 1000; // 转换为秒
    
    // 更新启用状态
    const enableToggle = document.getElementById('enableToggle');
    if (this.config.enabled) {
      enableToggle.classList.add('enabled');
    } else {
      enableToggle.classList.remove('enabled');
    }

    // 更新自动刷新状态
    const autoRefreshToggle = document.getElementById('autoRefreshToggle');
    if (this.config.autoRefresh) {
      autoRefreshToggle.classList.add('enabled');
    } else {
      autoRefreshToggle.classList.remove('enabled');
    }

    // 更新监控列表
    this.updateListsUI();
  }

  updateStatusUI() {
    if (!this.status) return;

    // 更新状态指示器
    const enabledStatus = document.getElementById('enabledStatus');
    const natsStatus = document.getElementById('natsStatus');

    enabledStatus.className = 'status-indicator';
    natsStatus.className = 'status-indicator';

    if (this.status.enabled) {
      enabledStatus.classList.add('enabled');
    }

    // 更新NATS连接状态
    if (this.status.natsConnected) {
      natsStatus.classList.add('connected');
      natsStatus.title = 'NATS已连接';
    } else if (this.status.natsReconnecting) {
      natsStatus.classList.add('reconnecting');
      natsStatus.title = `NATS重连中... (${this.status.natsReconnectAttempts}/${this.status.natsMaxReconnectAttempts})`;
    } else if (this.status.enabled) {
      natsStatus.classList.add('error');
      if (this.status.natsShouldReconnect) {
        natsStatus.title = 'NATS连接断开，将自动重连';
      } else {
        natsStatus.title = 'NATS连接失败';
      }
    } else {
      natsStatus.title = 'NATS未连接';
    }

    // 更新统计信息
    document.getElementById('monitoringTabs').textContent = this.status.monitoringTabs;
    
    // 更新重连信息显示
    this.updateReconnectInfo();
  }

  updateReconnectInfo() {
    const reconnectInfo = document.getElementById('reconnectInfo');
    if (!reconnectInfo) return;

    if (this.status.natsReconnecting) {
      reconnectInfo.textContent = `重连中... (${this.status.natsReconnectAttempts}/${this.status.natsMaxReconnectAttempts})`;
      reconnectInfo.classList.remove('hidden');
    } else if (this.status.enabled && !this.status.natsConnected && this.status.natsShouldReconnect) {
      reconnectInfo.textContent = '等待重连...';
      reconnectInfo.classList.remove('hidden');
    } else {
      reconnectInfo.classList.add('hidden');
    }
  }

  updateListsUI() {
    const container = document.getElementById('listContainer');
    container.innerHTML = '';

    this.config.monitoredLists.forEach((listUrl, index) => {
      const listItem = document.createElement('div');
      listItem.className = 'list-item';
      
      listItem.innerHTML = `
        <div class="list-url">${this.truncateUrl(listUrl)}</div>
        <button class="remove-btn" data-index="${index}">删除</button>
      `;

      // 绑定删除按钮事件
      listItem.querySelector('.remove-btn').addEventListener('click', (e) => {
        const index = parseInt(e.target.getAttribute('data-index'));
        this.removeList(index);
      });

      container.appendChild(listItem);
    });
  }

  truncateUrl(url) {
    if (url.length > 50) {
      return url.substring(0, 47) + '...';
    }
    return url;
  }

  async toggleEnabled() {
    if (!this.config) return;

    this.config.enabled = !this.config.enabled;
    
    // 立即更新UI
    const enableToggle = document.getElementById('enableToggle');
    if (this.config.enabled) {
      enableToggle.classList.add('enabled');
    } else {
      enableToggle.classList.remove('enabled');
    }

    // 保存配置
    await this.saveConfigToBackground();
  }

  async toggleAutoRefresh() {
    if (!this.config) return;

    this.config.autoRefresh = !this.config.autoRefresh;
    
    // 立即更新UI
    const autoRefreshToggle = document.getElementById('autoRefreshToggle');
    if (this.config.autoRefresh) {
      autoRefreshToggle.classList.add('enabled');
    } else {
      autoRefreshToggle.classList.remove('enabled');
    }

    // 保存配置
    await this.saveConfigToBackground();
  }

  addList() {
    const input = document.getElementById('newListUrl');
    const url = input.value.trim();

    if (!url) {
      this.showError('请输入Twitter列表URL');
      return;
    }

    // 验证URL格式
    if (!this.isValidTwitterListUrl(url)) {
      this.showError('请输入有效的Twitter列表URL');
      return;
    }

    // 检查是否已存在
    if (this.config.monitoredLists.includes(url)) {
      this.showError('该列表已在监控中');
      return;
    }

    // 添加到配置
    this.config.monitoredLists.push(url);
    
    // 清空输入框
    input.value = '';
    
    // 更新UI
    this.updateListsUI();
    
    this.showSuccess('列表添加成功');
  }

  removeList(index) {
    if (index >= 0 && index < this.config.monitoredLists.length) {
      this.config.monitoredLists.splice(index, 1);
      this.updateListsUI();
      this.showSuccess('列表删除成功');
    }
  }

  isValidTwitterListUrl(url) {
    // 简单的Twitter列表URL验证
    const patterns = [
      /^https?:\/\/(twitter\.com|x\.com)\/i\/lists\/\d+/,
      /^https?:\/\/(twitter\.com|x\.com)\/\w+\/lists\/\w+/
    ];
    
    return patterns.some(pattern => pattern.test(url));
  }

  async saveConfig() {
    try {
      // 从UI获取配置
      const natsServers = document.getElementById('natsServers').value
        .split('\n')
        .map(s => s.trim())
        .filter(s => s.length > 0);

      const natsSubject = document.getElementById('natsSubject').value.trim();
      const maxMessages = parseInt(document.getElementById('maxMessages').value);
      const checkInterval = parseInt(document.getElementById('checkInterval').value);
      const refreshInterval = parseInt(document.getElementById('refreshInterval').value) * 1000; // 转换为毫秒

      // 验证配置
      if (natsServers.length === 0) {
        this.showError('请至少配置一个NATS服务器');
        return;
      }

      if (!natsSubject) {
        this.showError('请配置NATS消息主题');
        return;
      }

      if (maxMessages < 1 || maxMessages > 20) {
        this.showError('最大消息数量必须在1-20之间');
        return;
      }

      if (checkInterval < 1000 || checkInterval > 60000) {
        this.showError('检查间隔必须在1000-60000毫秒之间');
        return;
      }

      if (refreshInterval < 10000 || refreshInterval > 3600000) {
        this.showError('刷新间隔必须在10-3600秒之间');
        return;
      }

      // 更新配置
      this.config.natsServers = natsServers;
      this.config.natsSubject = natsSubject;
      this.config.maxMessages = maxMessages;
      this.config.checkInterval = checkInterval;
      this.config.refreshInterval = refreshInterval;

      // 保存到background
      await this.saveConfigToBackground();
      
      this.showSuccess('配置保存成功');
    } catch (error) {
      console.error('保存配置失败:', error);
      this.showError('保存配置失败: ' + error.message);
    }
  }

  async saveConfigToBackground() {
    try {
      const response = await chrome.runtime.sendMessage({
        type: 'save_config',
        config: this.config
      });

      if (!response.success) {
        throw new Error(response.error || '保存失败');
      }
    } catch (error) {
      console.error('保存到background失败:', error);
      this.showError('保存配置失败: ' + error.message);
    }
  }

  showError(message) {
    const errorElement = document.getElementById('errorMessage');
    const successElement = document.getElementById('successMessage');
    
    successElement.classList.add('hidden');
    errorElement.textContent = message;
    errorElement.classList.remove('hidden');
    
    setTimeout(() => {
      errorElement.classList.add('hidden');
    }, 5000);
  }

  showSuccess(message) {
    const errorElement = document.getElementById('errorMessage');
    const successElement = document.getElementById('successMessage');
    
    errorElement.classList.add('hidden');
    successElement.textContent = message;
    successElement.classList.remove('hidden');
    
    setTimeout(() => {
      successElement.classList.add('hidden');
    }, 3000);
  }
}

// 初始化弹出窗口管理器
document.addEventListener('DOMContentLoaded', () => {
  new PopupManager();
}); 