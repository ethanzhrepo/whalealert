#!/usr/bin/env python3
"""
测试通知消息发送
模拟 analyze_agent 发送通知消息到 messages.notification subject
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

class NotificationTester:
    """通知消息测试器"""
    
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
    
    async def send_test_notifications(self):
        """发送测试通知消息"""
        if not self.nats_client:
            raise ValueError("NATS客户端未连接")
        
        test_notifications = [
            {
                "sentiment": "利多",
                "score": 0.85,
                "reason": "BTC突破重要价格关口，市场情绪极度乐观",
                "text": "🚀 BTC突破10万美元！牛市来了！",
                "username": "crypto_trader",
                "chat_title": "Crypto Signals"
            },
            {
                "sentiment": "利空",
                "score": -0.75,
                "reason": "市场出现大幅回调，恐慌情绪蔓延",
                "text": "市场大跌，BTC暴跌20%，恐慌情绪蔓延",
                "username": "market_analyst",
                "chat_title": "Market Analysis"
            },
            {
                "sentiment": "中性",
                "score": 0.1,
                "reason": "技术指标显示中性信号",
                "text": "ETH技术分析显示中性信号，等待突破",
                "username": "tech_analyst",
                "chat_title": "Technical Analysis"
            },
            {
                "sentiment": "利多",
                "score": 0.95,
                "reason": "重大利好消息推动市场情绪",
                "text": "DOGE to the moon! 🌙 马斯克又发推了！",
                "username": "doge_fan",
                "chat_title": "DOGE Community"
            },
            {
                "sentiment": "利空",
                "score": -0.6,
                "reason": "监管不确定性影响市场信心",
                "text": "监管政策不明朗，投资者观望情绪浓厚",
                "username": "news_bot",
                "chat_title": "Crypto News"
            }
        ]
        
        for i, notification_info in enumerate(test_notifications, 1):
            logger.info(f"发送测试通知 {i}/{len(test_notifications)}: {notification_info['sentiment']} ({notification_info['score']:.2f})")
            
            # 构建通知消息
            notification_data = self._create_notification_message(notification_info, i)
            
            # 发送到 messages.notification
            notification_json = json.dumps(notification_data, ensure_ascii=False, separators=(',', ':'))
            await self.nats_client.publish('messages.notification', notification_json.encode())
            
            logger.info(f"✅ 通知 {i} 已发送")
            
            # 等待一段时间再发送下一条
            await asyncio.sleep(5)
        
        logger.info("所有测试通知发送完成")
    
    def _create_notification_message(self, info: dict, message_id: int) -> dict:
        """创建通知消息"""
        current_time = int(time.time() * 1000)
        
        return {
            "type": "messages.notification",
            "timestamp": current_time,
            "source": "analyze_agent",
            "sender": "analyze_agent",
            "data": {
                "original_message": {
                    "type": "telegram.message",
                    "timestamp": current_time - 1000,
                    "source": "telegram",
                    "sender": "telegramstream",
                    "data": {
                        "message_id": message_id + 20000,
                        "chat_id": -1001234567890,
                        "chat_title": info['chat_title'],
                        "chat_type": "channel",
                        "user_id": 123456789 + message_id,
                        "username": info['username'],
                        "first_name": info['username'].replace('_', ' ').title(),
                        "is_bot": False,
                        "date": current_time - 1000,
                        "text": info['text'],
                        "raw_text": info['text'],
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
                            "symbols": self._extract_symbols(info['text']),
                            "crypto_currencies": [],
                            "urls": [],
                            "prices": [],
                            "keywords": [],
                            "sentiment": "neutral",
                            "raw_text": info['text']
                        }
                    }
                },
                "analysis_results": [
                    {
                        "agent_name": "情绪分析Agent",
                        "agent_type": "sentiment_analysis",
                        "result": {
                            "sentiment": info['sentiment'],
                            "reason": info['reason'],
                            "score": info['score'],
                            "processing_time": 1200 + message_id * 100
                        },
                        "processing_time_ms": 1200 + message_id * 100,
                        "llm_provider": "ollama",
                        "analysis_time": f"2024-12-23T{10 + message_id}:30:{15 + message_id}.123Z"
                    }
                ],
                "summary": {
                    "total_agents": 1,
                    "successful_analyses": 1,
                    "failed_analyses": 0,
                    "overall_sentiment": info['sentiment'],
                    "overall_score": info['score'],
                    "processing_start_time": f"2024-12-23T{10 + message_id}:30:{14 + message_id}.000Z",
                    "processing_end_time": f"2024-12-23T{10 + message_id}:30:{15 + message_id}.123Z",
                    "total_processing_time_ms": 1123 + message_id * 50
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
    tester = NotificationTester()
    
    try:
        await tester.connect()
        
        print("🧪 开始发送测试通知消息...")
        print("请确保 notification bot 正在运行以接收这些消息")
        print("你也可以运行 analyze_agent/test_notification.py 来监听消息")
        print()
        
        await tester.send_test_notifications()
        
        print("\n✅ 测试完成！")
        print("检查 notification bot 的输出和 Telegram 群组中的消息")
        
    except Exception as e:
        logger.error(f"测试失败: {e}")
        return 1
    finally:
        await tester.close()
    
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