#!/usr/bin/env python3
"""
NATS 消息测试脚本
用于测试 telegramstream 和 analyze_agent 之间的消息传递
"""

import asyncio
import json
import time
from datetime import datetime

import nats

async def test_nats_publisher():
    """测试发送消息到NATS"""
    print("=== NATS 发送测试 ===")
    
    # 连接NATS
    nc = await nats.connect("nats://localhost:4222")
    print("✅ NATS连接成功")
    
    # 构造测试消息
    test_message = {
        "type": "telegram.message",
        "timestamp": int(time.time() * 1000),
        "source": "telegram",
        "sender": "telegramstream",
        "data": {
            "message_id": 12345,
            "chat_id": -1001234567890,
            "chat_title": "测试频道",
            "text": "🚀 BTC突破10万美元！牛市来了！",
            "extracted_data": {
                "raw_text": "BTC突破10万美元！牛市来了！",
                "symbols": ["BTC"],
                "sentiment": "positive"
            }
        }
    }
    
    # 发送到不同的subject
    subjects = ["messages.stream", "telegram.messages"]
    
    for subject in subjects:
        message_json = json.dumps(test_message, ensure_ascii=False)
        await nc.publish(subject, message_json.encode())
        print(f"📤 已发送测试消息到: {subject}")
    
    await nc.close()
    print("✅ 发送测试完成")

async def test_nats_subscriber():
    """测试从NATS接收消息"""
    print("=== NATS 接收测试 ===")
    
    # 连接NATS
    nc = await nats.connect("nats://localhost:4222")
    print("✅ NATS连接成功")
    
    received_messages = []
    
    async def message_handler(msg):
        try:
            data = json.loads(msg.data.decode())
            received_messages.append({
                'subject': msg.subject,
                'data': data,
                'timestamp': datetime.now().isoformat()
            })
            print(f"📥 收到消息 [subject: {msg.subject}]: {data.get('type', 'unknown')}")
        except Exception as e:
            print(f"❌ 解析消息失败: {e}")
    
    # 订阅不同的subject
    subjects = ["messages.stream", "telegram.messages"]
    
    for subject in subjects:
        await nc.subscribe(subject, cb=message_handler)
        print(f"👂 已订阅: {subject}")
    
    print("⏳ 等待消息... (10秒)")
    await asyncio.sleep(10)
    
    await nc.close()
    
    print(f"\n📊 接收统计:")
    print(f"总共收到 {len(received_messages)} 条消息")
    for msg in received_messages:
        print(f"  - {msg['timestamp']}: {msg['subject']} -> {msg['data'].get('type')}")
    
    return received_messages

async def test_analyze_agent_config():
    """测试analyze_agent的配置"""
    print("=== Analyze Agent 配置测试 ===")
    
    import yaml
    
    # 读取配置
    with open('config.yml', 'r') as f:
        config = yaml.safe_load(f)
    
    nats_config = config.get('nats', {})
    subjects = nats_config.get('subject', [])
    
    print(f"NATS启用: {nats_config.get('enabled')}")
    print(f"NATS服务器: {nats_config.get('servers')}")
    print(f"监控subjects: {subjects}")
    print(f"subjects类型: {type(subjects)}")
    
    return subjects

async def main():
    """主测试函数"""
    print("🧪 NATS 消息流测试")
    print("=" * 50)
    
    try:
        # 测试配置
        subjects = await test_analyze_agent_config()
        print()
        
        # 启动订阅者（在后台）
        subscriber_task = asyncio.create_task(test_nats_subscriber())
        
        # 等待一下让订阅者准备好
        await asyncio.sleep(2)
        
        # 发送测试消息
        await test_nats_publisher()
        
        # 等待订阅者完成
        received_messages = await subscriber_task
        
        print("\n🎯 测试结果:")
        if received_messages:
            print("✅ NATS消息传递正常")
            for msg in received_messages:
                if msg['subject'] in subjects:
                    print(f"✅ analyze_agent应该能收到来自 {msg['subject']} 的消息")
                else:
                    print(f"⚠️  analyze_agent不会收到来自 {msg['subject']} 的消息")
        else:
            print("❌ 没有收到任何消息，请检查NATS服务器")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")

if __name__ == '__main__':
    asyncio.run(main()) 