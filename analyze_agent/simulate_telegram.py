#!/usr/bin/env python3
"""
模拟 telegramstream 发送消息的测试脚本
用于测试 analyze_agent 是否能正确接收和处理消息
"""

import asyncio
import json
import time
from datetime import datetime

import nats

async def send_test_messages():
    """发送测试消息"""
    print("🚀 开始发送测试消息...")
    
    # 连接NATS
    nc = await nats.connect("nats://localhost:4222")
    print("✅ NATS连接成功")
    
    # 测试消息列表
    test_messages = [
        {
            "type": "telegram.message",
            "timestamp": int(time.time() * 1000),
            "source": "telegram",
            "sender": "telegramstream",
            "data": {
                "message_id": 12345,
                "chat_id": -1001234567890,
                "chat_title": "Crypto Signals",
                "text": "🚀 BTC突破10万美元！牛市来了！",
                "extracted_data": {
                    "raw_text": "BTC突破10万美元！牛市来了！",
                    "symbols": ["BTC"],
                    "sentiment": "positive"
                }
            }
        },
        {
            "type": "telegram.message",
            "timestamp": int(time.time() * 1000),
            "source": "telegram",
            "sender": "telegramstream",
            "data": {
                "message_id": 12346,
                "chat_id": -1001234567890,
                "chat_title": "Crypto Signals",
                "text": "⚠️ 市场出现大幅回调，注意风险控制",
                "extracted_data": {
                    "raw_text": "市场出现大幅回调，注意风险控制",
                    "symbols": [],
                    "sentiment": "negative"
                }
            }
        },
        {
            "type": "telegram.message",
            "timestamp": int(time.time() * 1000),
            "source": "telegram",
            "sender": "telegramstream",
            "data": {
                "message_id": 12347,
                "chat_id": -1001234567890,
                "chat_title": "Crypto Signals",
                "text": "ETH价格分析：技术指标显示中性信号",
                "extracted_data": {
                    "raw_text": "ETH价格分析：技术指标显示中性信号",
                    "symbols": ["ETH"],
                    "sentiment": "neutral"
                }
            }
        }
    ]
    
    subject = "messages.stream"  # 使用analyze_agent配置的subject
    
    for i, message in enumerate(test_messages, 1):
        message_json = json.dumps(message, ensure_ascii=False)
        await nc.publish(subject, message_json.encode())
        print(f"📤 已发送测试消息 {i}/{len(test_messages)}: {message['data']['text'][:30]}...")
        
        # 间隔发送
        await asyncio.sleep(2)
    
    await nc.close()
    print("✅ 所有测试消息发送完成")

async def main():
    """主函数"""
    print("🧪 Telegram 消息模拟器")
    print("=" * 50)
    print("这个脚本会模拟 telegramstream 发送消息到 NATS")
    print("请确保 analyze_agent 正在运行以接收这些消息")
    print()
    
    try:
        await send_test_messages()
        print("\n✅ 测试完成！")
        print("如果 analyze_agent 正在运行，你应该能看到分析结果输出")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")

if __name__ == '__main__':
    asyncio.run(main()) 