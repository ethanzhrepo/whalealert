# Twitter Monitor Extension 安装指南

## 前置要求

1. **Chrome浏览器** (版本88+)
2. **NATS服务器** 支持WebSocket连接
3. **analyze_agent** (可选，用于消息分析)

## 第一步：安装扩展

### 方法1：开发者模式安装

1. 打开Chrome浏览器
2. 在地址栏输入 `chrome://extensions/`
3. 开启右上角的"开发者模式"开关
4. 点击"加载已解压的扩展程序"按钮
5. 选择 `x_extansion` 文件夹
6. 扩展安装完成后会出现在扩展列表中

### 方法2：打包安装 (推荐生产环境)

1. 在 `chrome://extensions/` 页面点击"打包扩展程序"
2. 选择 `x_extansion` 文件夹
3. 生成 `.crx` 文件
4. 拖拽 `.crx` 文件到Chrome浏览器安装

## 第二步：配置NATS服务器

### 启动NATS服务器

```bash
# 使用Docker启动NATS (推荐)
docker run -d --name nats-server -p 4222:4222 -p 8222:8222 nats:latest --websocket_port 4222

# 或者使用本地安装的NATS
nats-server --websocket_port 4222
```

### 验证NATS连接

```bash
# 测试WebSocket连接
curl -i -N -H "Connection: Upgrade" \
     -H "Upgrade: websocket" \
     -H "Sec-WebSocket-Key: test" \
     -H "Sec-WebSocket-Version: 13" \
     http://localhost:4222/
```

## 第三步：配置扩展

1. **打开扩展配置**
   - 点击Chrome工具栏中的扩展图标
   - 或者右键点击扩展图标选择"选项"

2. **配置NATS连接**
   ```
   NATS服务器: ws://localhost:4222
   消息主题: twitter.messages
   ```

3. **设置监控参数**
   ```
   最大消息数量: 5
   检查间隔: 5000 (毫秒)
   ```

4. **添加Twitter列表**
   - 复制Twitter列表URL，例如：
     - `https://twitter.com/i/lists/123456789`
     - `https://x.com/i/lists/987654321`
   - 粘贴到"添加Twitter列表URL"输入框
   - 点击"添加列表"按钮

5. **启用监控**
   - 切换"启用监控"开关
   - 确认状态指示器显示为绿色

## 第四步：配置analyze_agent (可选)

如果要使用AI分析功能，需要配置analyze_agent：

1. **更新配置文件**
   ```yaml
   # analyze_agent/config.yml
   nats:
     enabled: true
     servers: 
       - 'nats://localhost:4222'
     subject: 
       - 'telegram.messages'
       - 'twitter.messages'  # 添加这行
   ```

2. **启动analyze_agent**
   ```bash
   cd analyze_agent
   python main.py
   ```

## 第五步：测试监控

1. **打开Twitter列表页面**
   - 在Chrome中访问已配置的Twitter列表URL
   - 扩展会自动检测并开始监控

2. **验证消息推送**
   - 查看扩展的控制台日志
   - 检查NATS服务器是否收到消息
   - 如果配置了analyze_agent，查看分析结果

## 故障排除

### 常见问题

#### 1. NATS连接失败
**症状**: 状态指示器显示红色，控制台显示连接错误

**解决方案**:
- 确认NATS服务器正在运行
- 检查端口4222是否开放
- 验证WebSocket支持是否启用
- 尝试使用不同的端口

#### 2. 无法检测到推文
**症状**: 页面有新推文但扩展没有推送消息

**解决方案**:
- 确认Twitter列表URL格式正确
- 检查页面是否完全加载
- 查看浏览器控制台是否有JavaScript错误
- 尝试刷新页面

#### 3. 消息重复推送
**症状**: 同一条推文被多次推送

**解决方案**:
- 检查浏览器存储是否正常
- 清除扩展的本地存储数据
- 重新配置时间戳设置

#### 4. 扩展无法加载
**症状**: 扩展安装后无法正常工作

**解决方案**:
- 检查manifest.json语法是否正确
- 确认所有文件都在正确位置
- 查看Chrome扩展管理页面的错误信息
- 尝试重新加载扩展

### 调试方法

#### 1. 查看扩展日志
```javascript
// 在扩展的background页面控制台中
chrome.runtime.getBackgroundPage(function(bg) {
  console.log(bg.console);
});
```

#### 2. 监控NATS消息
```bash
# 使用NATS CLI工具订阅消息
nats sub twitter.messages
```

#### 3. 检查网络连接
```javascript
// 在浏览器控制台中测试WebSocket连接
const ws = new WebSocket('ws://localhost:4222');
ws.onopen = () => console.log('连接成功');
ws.onerror = (error) => console.error('连接失败:', error);
```

## 高级配置

### 自定义消息格式

可以修改 `content.js` 中的 `formatMessage` 方法来自定义消息格式：

```javascript
async formatMessage(tweetData) {
  return {
    type: 'twitter.message',
    timestamp: Date.now(),
    source: 'twitter',
    sender: 'x_extension',
    data: {
      // 自定义字段
      custom_field: 'custom_value',
      // ... 其他字段
    }
  };
}
```

### 配置多个NATS服务器

在扩展配置中可以添加多个NATS服务器地址：

```
ws://localhost:4222
ws://backup-server:4222
wss://remote-server:4223
```

### 自定义检测规则

可以修改 `extractStructuredData` 方法来自定义数据提取规则：

```javascript
async extractStructuredData(text) {
  // 自定义符号检测
  const customSymbols = ['CUSTOM', 'TOKEN'];
  
  // 自定义价格模式
  const customPricePattern = /价格[:：]\s*(\d+(?:\.\d+)?)/gi;
  
  // ... 其他自定义逻辑
}
```

## 性能优化

### 减少资源消耗

1. **调整检查间隔**: 增加检查间隔可以减少CPU使用
2. **限制消息数量**: 减少最大消息数量可以降低内存使用
3. **优化选择器**: 使用更精确的CSS选择器提高性能

### 监控性能指标

```javascript
// 在控制台中查看性能统计
chrome.runtime.sendMessage({type: 'get_stats'}, (response) => {
  console.log('性能统计:', response.stats);
});
```

## 安全注意事项

1. **权限最小化**: 扩展只请求必要的权限
2. **数据加密**: 敏感配置应该加密存储
3. **网络安全**: 使用WSS协议进行加密传输
4. **输入验证**: 所有用户输入都经过验证

## 更新和维护

### 更新扩展

1. 下载新版本文件
2. 在 `chrome://extensions/` 页面点击"重新加载"
3. 检查配置是否需要更新

### 备份配置

```javascript
// 导出配置
chrome.storage.sync.get(null, (config) => {
  console.log('当前配置:', JSON.stringify(config, null, 2));
});

// 导入配置
const config = { /* 配置对象 */ };
chrome.storage.sync.set(config);
```

## 技术支持

如果遇到问题，请提供以下信息：

1. Chrome版本号
2. 扩展版本号
3. 错误日志
4. 复现步骤
5. 系统环境信息

联系方式：[在此添加联系信息] 