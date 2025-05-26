#!/usr/bin/env python3
"""
模拟发送Telegram消息到 messages.stream
用于测试 analyze_agent 的通知功能
"""

import asyncio
import json
import time
import logging

import nats

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MessageSimulator:
    """消息模拟器"""
    
    def __init__(self):
        self.nats_client = None
    
    async def connect(self):
        """连接到NATS服务器"""
        try:
            self.nats_client = await nats.connect(servers=['nats://localhost:4222'])
            logger.info("NATS连接成功")
        except Exception as e:
            logger.error(f"NATS连接失败: {e}")
            raise
    
    async def send_test_messages(self):
        """发送测试消息"""
        if not self.nats_client:
            raise ValueError("NATS客户端未连接")
        
        test_messages = [
            {
                "text": "🚀 BTC突破10万美元！牛市来了！",
                "sentiment_expected": "利多"
            },
            {
                "text": "市场大跌，BTC暴跌20%，恐慌情绪蔓延",
                "sentiment_expected": "利空"
            },
            {
                "text": "ETH技术分析显示中性信号，等待突破",
                "sentiment_expected": "中性"
            },
            {
                "text": "DOGE to the moon! 🌙 马斯克又发推了！",
                "sentiment_expected": "利多"
            },
            {
                "text": "监管政策不明朗，投资者观望情绪浓厚",
                "sentiment_expected": "利空"
            }
        ]
        
        for i, msg_info in enumerate(test_messages, 1):
            logger.info(f"发送测试消息 {i}/{len(test_messages)}: {msg_info['text'][:50]}...")
            
            # 构建模拟的telegram消息
            message_data = self._create_telegram_message(msg_info['text'], i)
            
            # 发送到 messages.stream
            message_json = json.dumps(message_data, ensure_ascii=False, separators=(',', ':'))
            await self.nats_client.publish('messages.stream', message_json.encode())
            
            logger.info(f"✅ 消息 {i} 已发送，预期情绪: {msg_info['sentiment_expected']}")
            
            # 等待一段时间再发送下一条
            await asyncio.sleep(3)
        
        logger.info("所有测试消息发送完成")
    
    def _create_telegram_message(self, text: str, message_id: int) -> dict:
        """创建模拟的telegram消息"""
        current_time = int(time.time() * 1000)
        
        return {
            "type": "telegram.message",
            "timestamp": current_time,
            "source": "telegram",
            "sender": "telegramstream",
            "data": {
                "message_id": message_id + 10000,
                "chat_id": -1001234567890,
                "chat_title": "测试加密货币群",
                "chat_type": "channel",
                "user_id": 123456789,
                "username": "crypto_test_user",
                "first_name": "Test",
                "is_bot": False,
                "date": current_time,
                "text": text,
                "raw_text": text,
                "reply_to_message_id": None,
                "forward_from_chat_id": None,
                "entities": [],
                "media": None,
                "extracted_data": {
                    "addresses": {
                        "ethereum": [],
                        "solana": [],
                        "bitcoin": []
                    },
                    "symbols": self._extract_symbols(text),
                    "crypto_currencies": [],
                    "urls": [],
                    "prices": [],
                    "keywords": [],
                    "sentiment": "neutral",
                    "raw_text": text
                }
            }
        }
    
    def _extract_symbols(self, text: str) -> list:
        """简单提取符号（用于测试）"""
        symbols = []
        text_upper = text.upper()
        
        common_symbols = ['BTC', 'ETH', 'DOGE', 'ADA', 'SOL', 'USDT', 'USDC']
        for symbol in common_symbols:
            if symbol in text_upper:
                symbols.append(symbol)
        
        return symbols
    
    async def close(self):
        """关闭连接"""
        if self.nats_client:
            await self.nats_client.close()

async def main():
    """主函数"""
    simulator = MessageSimulator()
    
    try:
        await simulator.connect()
        
        print("🧪 开始发送测试消息...")
        print("请确保 analyze_agent 正在运行以接收和处理这些消息")
        print("你也可以运行 test_notification.py 来监听通知消息")
        print()
        
        await simulator.send_test_messages()
        
        print("\n✅ 测试完成！")
        print("检查 analyze_agent 的输出和 test_notification.py 的结果")
        
    except Exception as e:
        logger.error(f"测试失败: {e}")
        return 1
    finally:
        await simulator.close()
    
    return 0

if __name__ == '__main__':
    import sys
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("测试被用户中断")
        sys.exit(0)
    except Exception as e:
        logger.error(f"测试异常退出: {e}")
        sys.exit(1) 