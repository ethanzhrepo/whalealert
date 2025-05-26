#!/usr/bin/env python3
"""
通知消息订阅者示例
展示如何在实际应用中处理 analyze_agent 发送的通知消息
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any

import nats

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CryptoSignalProcessor:
    """加密货币信号处理器"""
    
    def __init__(self):
        self.nats_client = None
        self.signal_count = 0
        self.strong_signals = []
    
    async def connect(self):
        """连接到NATS服务器"""
        try:
            self.nats_client = await nats.connect(servers=['nats://localhost:4222'])
            logger.info("NATS连接成功")
        except Exception as e:
            logger.error(f"NATS连接失败: {e}")
            raise
    
    async def start_processing(self):
        """开始处理通知消息"""
        if not self.nats_client:
            raise ValueError("NATS客户端未连接")
        
        # 订阅通知消息
        await self.nats_client.subscribe('messages.notification', cb=self._process_notification)
        logger.info("已订阅 messages.notification，开始处理信号...")
        
        try:
            # 保持运行
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("收到停止信号")
        finally:
            if self.nats_client:
                await self.nats_client.close()
    
    async def _process_notification(self, msg):
        """处理通知消息"""
        try:
            self.signal_count += 1
            notification_data = json.loads(msg.data.decode())
            
            # 提取数据
            original_msg = notification_data.get('data', {}).get('original_message', {})
            analysis_results = notification_data.get('data', {}).get('analysis_results', [])
            summary = notification_data.get('data', {}).get('summary', {})
            
            # 处理信号
            signal = self._analyze_signal(original_msg, analysis_results, summary)
            
            if signal:
                await self._handle_signal(signal)
            
        except Exception as e:
            logger.error(f"处理通知消息失败: {e}")
    
    def _analyze_signal(self, original_msg: Dict[str, Any], 
                       analysis_results: list, summary: Dict[str, Any]) -> Dict[str, Any]:
        """分析信号强度和类型"""
        
        # 提取原始消息信息
        original_data = original_msg.get('data', {})
        chat_title = original_data.get('chat_title', 'Unknown')
        text = original_data.get('text', '')
        symbols = original_data.get('extracted_data', {}).get('symbols', [])
        
        # 分析情绪结果
        sentiment_results = [r for r in analysis_results if r.get('agent_type') == 'sentiment_analysis']
        
        if not sentiment_results:
            return None
        
        sentiment_result = sentiment_results[0].get('result', {})
        sentiment = sentiment_result.get('sentiment', '中性')
        score = sentiment_result.get('score', 0.0)
        reason = sentiment_result.get('reason', '')
        
        # 计算信号强度
        signal_strength = self._calculate_signal_strength(score, symbols, text)
        
        # 构建信号对象
        signal = {
            'timestamp': datetime.now().isoformat(),
            'signal_id': f"signal_{self.signal_count}",
            'source': {
                'chat_title': chat_title,
                'message_text': text[:200] + '...' if len(text) > 200 else text,
                'symbols': symbols
            },
            'analysis': {
                'sentiment': sentiment,
                'score': score,
                'reason': reason,
                'confidence': signal_strength
            },
            'action': self._determine_action(sentiment, signal_strength),
            'priority': self._determine_priority(signal_strength),
            'processing_stats': {
                'total_processing_time': summary.get('total_processing_time_ms', 0),
                'successful_analyses': summary.get('successful_analyses', 0)
            }
        }
        
        return signal
    
    def _calculate_signal_strength(self, score: float, symbols: list, text: str) -> float:
        """计算信号强度（0-1）"""
        base_strength = abs(score)  # 基础强度基于情绪评分
        
        # 符号加权：主流币种权重更高
        major_coins = ['BTC', 'ETH', 'BNB', 'ADA', 'SOL']
        symbol_weight = 1.0
        
        for symbol in symbols:
            if symbol in major_coins:
                symbol_weight += 0.2
            else:
                symbol_weight += 0.1
        
        # 文本长度加权：更长的分析通常更可靠
        text_weight = min(1.0 + len(text) / 1000, 1.5)
        
        # 关键词加权
        strong_keywords = ['突破', '暴涨', '暴跌', '牛市', '熊市', '崩盘', '飞涨']
        keyword_weight = 1.0
        
        for keyword in strong_keywords:
            if keyword in text:
                keyword_weight += 0.1
        
        # 计算最终强度
        final_strength = base_strength * symbol_weight * text_weight * keyword_weight
        
        # 限制在0-1范围内
        return min(final_strength, 1.0)
    
    def _determine_action(self, sentiment: str, strength: float) -> str:
        """确定推荐操作"""
        if strength < 0.3:
            return 'HOLD'  # 持有
        elif sentiment == '利多':
            if strength > 0.8:
                return 'STRONG_BUY'  # 强烈买入
            elif strength > 0.5:
                return 'BUY'  # 买入
            else:
                return 'WEAK_BUY'  # 弱买入
        elif sentiment == '利空':
            if strength > 0.8:
                return 'STRONG_SELL'  # 强烈卖出
            elif strength > 0.5:
                return 'SELL'  # 卖出
            else:
                return 'WEAK_SELL'  # 弱卖出
        else:
            return 'HOLD'  # 中性持有
    
    def _determine_priority(self, strength: float) -> str:
        """确定信号优先级"""
        if strength > 0.8:
            return 'HIGH'
        elif strength > 0.5:
            return 'MEDIUM'
        elif strength > 0.3:
            return 'LOW'
        else:
            return 'IGNORE'
    
    async def _handle_signal(self, signal: Dict[str, Any]):
        """处理信号"""
        action = signal['action']
        priority = signal['priority']
        
        # 记录信号
        logger.info(f"🚨 新信号: {action} | 优先级: {priority} | "
                   f"强度: {signal['analysis']['confidence']:.2f}")
        
        # 高优先级信号特殊处理
        if priority == 'HIGH':
            self.strong_signals.append(signal)
            await self._send_alert(signal)
        
        # 输出详细信息
        self._print_signal_details(signal)
        
        # 这里可以添加更多业务逻辑：
        # - 发送到交易系统
        # - 存储到数据库
        # - 发送通知到其他系统
        # - 触发自动交易策略
    
    async def _send_alert(self, signal: Dict[str, Any]):
        """发送高优先级信号告警"""
        logger.warning(f"⚠️  高优先级信号告警: {signal['action']}")
        logger.warning(f"   来源: {signal['source']['chat_title']}")
        logger.warning(f"   符号: {', '.join(signal['source']['symbols'])}")
        logger.warning(f"   情绪: {signal['analysis']['sentiment']} "
                      f"(评分: {signal['analysis']['score']:.2f})")
        logger.warning(f"   理由: {signal['analysis']['reason']}")
        
        # 这里可以集成告警系统：
        # - 发送邮件
        # - 推送到手机
        # - 发送到Slack/Discord
        # - 调用Webhook
    
    def _print_signal_details(self, signal: Dict[str, Any]):
        """打印信号详情"""
        print("\n" + "="*60)
        print(f"📊 信号详情 #{signal['signal_id']}")
        print(f"时间: {signal['timestamp']}")
        print("-"*60)
        
        # 来源信息
        source = signal['source']
        print(f"📱 来源: {source['chat_title']}")
        print(f"💬 内容: {source['message_text']}")
        print(f"🪙 符号: {', '.join(source['symbols']) if source['symbols'] else '无'}")
        
        # 分析结果
        analysis = signal['analysis']
        print(f"\n🤖 分析:")
        print(f"   情绪: {analysis['sentiment']}")
        print(f"   评分: {analysis['score']:.2f}")
        print(f"   理由: {analysis['reason']}")
        print(f"   强度: {analysis['confidence']:.2f}")
        
        # 推荐操作
        print(f"\n💡 推荐:")
        print(f"   操作: {signal['action']}")
        print(f"   优先级: {signal['priority']}")
        
        # 性能统计
        stats = signal['processing_stats']
        print(f"\n⏱️  性能:")
        print(f"   处理耗时: {stats['total_processing_time']}ms")
        print(f"   成功分析: {stats['successful_analyses']}")
        
        print("="*60)

async def main():
    """主函数"""
    processor = CryptoSignalProcessor()
    
    try:
        await processor.connect()
        
        print("🚀 加密货币信号处理器已启动")
        print("正在监听 messages.notification...")
        print("请确保 analyze_agent 正在运行")
        print()
        
        await processor.start_processing()
        
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