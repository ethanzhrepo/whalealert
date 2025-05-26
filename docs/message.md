# 全域消息结构定义

## Aave 监控消息结构

所有 Aave 监控消息使用通用信封结构:

```json
{
  "type": "string",  // 消息类型，例如: "aave.borrow", "aave.liquidation", "aave.reserve_data"
  "timestamp": 1234567890,  // Unix 时间戳
  "data": {}  // 消息数据，根据消息类型不同而结构不同
}
```

### 借款事件消息 (aave.borrow)

```json
{
  "type": "aave.borrow",
  "timestamp": 1234567890,
  "data": {
    "symbol": "WETH",  // 借款代币符号
    "amount": 10.5,  // 借款数量
    "amount_usd": 31500.0,  // 借款数量美元价值
    "user": "0x1234...",  // 借款用户地址
    "on_behalf_of": "0x5678...",  // 被借款人地址（可能与用户地址相同）
    "borrow_rate_mode": 2,  // 借款利率模式: 1=稳定, 2=可变
    "borrow_rate": 0.035,  // 借款利率
    "block_number": 12345678,  // 区块号
    "tx_hash": "0xabcd..."  // 交易哈希
  }
}
```

### 清算事件消息 (aave.liquidation)

```json
{
  "type": "aave.liquidation",
  "timestamp": 1234567890,
  "data": {
    "collateral_symbol": "WETH",  // 抵押品代币符号
    "debt_symbol": "USDC",  // 债务代币符号
    "collateral_amount": 5.2,  // 清算的抵押品数量
    "debt_amount": 15000.0,  // 清算的债务数量
    "debt_amount_usd": 15000.0,  // 清算的债务价值（美元）
    "user": "0x1234...",  // 被清算的用户地址
    "liquidator": "0x5678...",  // 清算人地址
    "receive_atoken": false,  // 是否接收aToken而非底层资产
    "block_number": 12345678,  // 区块号
    "tx_hash": "0xabcd..."  // 交易哈希
  }
}
```

### 储备数据消息 (aave.reserve_data)

```json
{
  "type": "aave.reserve_data",
  "timestamp": 1234567890,
  "data": {
    "symbol": "WETH",  // 代币符号
    "supply_apy": 0.01,  // 存款年利率
    "variable_borrow_apy": 0.035,  // 可变借款年利率
    "stable_borrow_apy": 0.045,  // 稳定借款年利率
    "total_supply": "1000000000000000000000",  // 总供应量（以wei为单位的字符串）
    "total_borrowed": "500000000000000000000",  // 总借款量（以wei为单位的字符串）
    "supply_ratio": 0.5,  // 借款比例（总借款/总供应）
    "timestamp": 1234567890  // 数据获取时间戳
  }
}
```