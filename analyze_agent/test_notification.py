#!/usr/bin/env python3
"""
测试通知消息功能
监听 messages.notification subject，验证 analyze_agent 发送的通知消息
"""

import asyncio
import json
import logging
from datetime import datetime

import nats

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class NotificationListener:
    """通知消息监听器"""
    
    def __init__(self):
        self.nats_client = None
        self.message_count = 0
    
    async def connect(self):
        """连接到NATS服务器"""
        try:
            self.nats_client = await nats.connect(servers=['nats://localhost:4222'])
            logger.info("NATS连接成功")
        except Exception as e:
            logger.error(f"NATS连接失败: {e}")
            raise
    
    async def start_listening(self):
        """开始监听通知消息"""
        if not self.nats_client:
            raise ValueError("NATS客户端未连接")
        
        # 订阅通知subject
        await self.nats_client.subscribe('messages.notification', cb=self._notification_handler)
        logger.info("已订阅 messages.notification subject")
        
        # 也订阅原始消息，用于对比
        await self.nats_client.subscribe('messages.stream', cb=self._stream_handler)
        logger.info("已订阅 messages.stream subject")
        
        logger.info("开始监听消息...")
        logger.info("请确保 telegramstream 和 analyze_agent 都在运行")
        
        try:
            # 保持运行
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("收到停止信号")
        finally:
            if self.nats_client:
                await self.nats_client.close()
    
    async def _stream_handler(self, msg):
        """处理原始流消息"""
        try:
            message_data = json.loads(msg.data.decode())
            logger.info(f"📨 收到原始消息: type={message_data.get('type')}, "
                       f"chat={message_data.get('data', {}).get('chat_title', 'Unknown')}")
        except Exception as e:
            logger.error(f"处理原始消息失败: {e}")
    
    async def _notification_handler(self, msg):
        """处理通知消息"""
        try:
            self.message_count += 1
            notification_data = json.loads(msg.data.decode())
            
            logger.info(f"🔔 收到通知消息 #{self.message_count}")
            
            # 验证消息结构
            self._validate_notification_structure(notification_data)
            
            # 提取关键信息
            original_msg = notification_data.get('data', {}).get('original_message', {})
            analysis_results = notification_data.get('data', {}).get('analysis_results', [])
            summary = notification_data.get('data', {}).get('summary', {})
            
            # 显示分析结果
            print("\n" + "="*80)
            print(f"📊 分析结果通知 #{self.message_count}")
            print(f"时间: {datetime.now().isoformat()}")
            print("-"*80)
            
            # 原始消息信息
            original_data = original_msg.get('data', {})
            print(f"📱 原始消息:")
            print(f"   来源: {original_data.get('chat_title', 'Unknown')}")
            print(f"   内容: {original_data.get('text', '')[:100]}...")
            print(f"   发送者: {original_data.get('username', 'Unknown')}")
            
            # 分析结果
            print(f"\n🤖 分析结果:")
            for i, result in enumerate(analysis_results, 1):
                agent_name = result.get('agent_name', 'Unknown')
                agent_result = result.get('result', {})
                processing_time = result.get('processing_time_ms', 0)
                
                print(f"   Agent {i}: {agent_name}")
                print(f"   情绪: {agent_result.get('sentiment', 'Unknown')}")
                print(f"   理由: {agent_result.get('reason', 'Unknown')}")
                print(f"   评分: {agent_result.get('score', 0.0)}")
                print(f"   耗时: {processing_time}ms")
                print(f"   LLM: {result.get('llm_provider', 'Unknown')}")
            
            # 汇总信息
            print(f"\n📈 汇总:")
            print(f"   总Agent数: {summary.get('total_agents', 0)}")
            print(f"   成功分析: {summary.get('successful_analyses', 0)}")
            print(f"   失败分析: {summary.get('failed_analyses', 0)}")
            print(f"   综合情绪: {summary.get('overall_sentiment', 'Unknown')}")
            print(f"   综合评分: {summary.get('overall_score', 0.0)}")
            print(f"   总耗时: {summary.get('total_processing_time_ms', 0)}ms")
            
            print("="*80)
            
        except Exception as e:
            logger.error(f"处理通知消息失败: {e}")
            logger.error(f"原始消息: {msg.data.decode()[:500]}...")
    
    def _validate_notification_structure(self, notification_data: dict):
        """验证通知消息结构"""
        required_fields = ['type', 'timestamp', 'source', 'sender', 'data']
        for field in required_fields:
            if field not in notification_data:
                raise ValueError(f"缺少必需字段: {field}")
        
        if notification_data['type'] != 'messages.notification':
            raise ValueError(f"消息类型错误: {notification_data['type']}")
        
        if notification_data['source'] != 'analyze_agent':
            raise ValueError(f"消息源错误: {notification_data['source']}")
        
        data = notification_data['data']
        required_data_fields = ['original_message', 'analysis_results', 'summary']
        for field in required_data_fields:
            if field not in data:
                raise ValueError(f"缺少数据字段: {field}")
        
        logger.debug("✅ 通知消息结构验证通过")

async def main():
    """主函数"""
    listener = NotificationListener()
    
    try:
        await listener.connect()
        await listener.start_listening()
    except Exception as e:
        logger.error(f"程序运行失败: {e}")
        return 1
    
    return 0

if __name__ == '__main__':
    import sys
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("程序被用户中断")
        sys.exit(0)
    except Exception as e:
        logger.error(f"程序异常退出: {e}")
        sys.exit(1) 