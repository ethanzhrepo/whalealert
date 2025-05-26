#!/usr/bin/env python3
"""
Notification Bot - 通知消息处理器
监听 analyze_agent 发送的通知消息，通过 Telegram Bot 发送到指定群组
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional
from collections import deque

import yaml
import nats
from telegram import Bot
from telegram.constants import ParseMode
from telegram.error import TelegramError, RetryAfter, TimedOut

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Config:
    """配置管理器"""
    
    def __init__(self, config_file: str = "config.yml"):
        self.config_file = config_file
        self.config = self._load_config()
        self._setup_logging()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        config_path = Path(self.config_file)
        if not config_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {config_path}")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def _setup_logging(self):
        """设置日志配置"""
        log_config = self.config.get('logging', {})
        level = getattr(logging, log_config.get('level', 'INFO'))
        format_str = log_config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        # 配置根日志记录器
        root_logger = logging.getLogger()
        root_logger.setLevel(level)
        
        # 清除现有处理器
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_formatter = logging.Formatter(format_str)
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
        
        # 文件处理器（如果配置了）
        log_file = log_config.get('file')
        if log_file:
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(level)
            file_formatter = logging.Formatter(format_str)
            file_handler.setFormatter(file_formatter)
            root_logger.addHandler(file_handler)
    
    def get_nats_config(self) -> Dict[str, Any]:
        """获取NATS配置"""
        return self.config.get('nats', {})
    
    def get_telegram_config(self) -> Dict[str, Any]:
        """获取Telegram配置"""
        return self.config.get('telegram', {})
    
    def get_filters_config(self) -> Dict[str, Any]:
        """获取过滤配置"""
        return self.config.get('filters', {})
    
    def get_rate_limit_config(self) -> Dict[str, Any]:
        """获取限流配置"""
        return self.config.get('rate_limit', {})
    
    def get_error_handling_config(self) -> Dict[str, Any]:
        """获取错误处理配置"""
        return self.config.get('error_handling', {})

class RateLimiter:
    """限流器"""
    
    def __init__(self, max_messages_per_minute: int = 10, cooldown_seconds: int = 3):
        self.max_messages_per_minute = max_messages_per_minute
        self.cooldown_seconds = cooldown_seconds
        self.message_times = deque()
        self.last_message_time = 0
    
    async def wait_if_needed(self):
        """如果需要，等待以遵守限流规则"""
        current_time = time.time()
        
        # 检查冷却时间
        time_since_last = current_time - self.last_message_time
        if time_since_last < self.cooldown_seconds:
            wait_time = self.cooldown_seconds - time_since_last
            logger.debug(f"冷却等待 {wait_time:.1f} 秒")
            await asyncio.sleep(wait_time)
            current_time = time.time()
        
        # 检查每分钟限制
        one_minute_ago = current_time - 60
        
        # 移除一分钟前的记录
        while self.message_times and self.message_times[0] < one_minute_ago:
            self.message_times.popleft()
        
        # 如果达到限制，等待
        if len(self.message_times) >= self.max_messages_per_minute:
            wait_time = self.message_times[0] + 60 - current_time
            if wait_time > 0:
                logger.warning(f"达到限流限制，等待 {wait_time:.1f} 秒")
                await asyncio.sleep(wait_time)
                current_time = time.time()
        
        # 记录当前消息时间
        self.message_times.append(current_time)
        self.last_message_time = current_time

class MessageFormatter:
    """消息格式化器"""
    
    def __init__(self, format_config: Dict[str, Any]):
        self.config = format_config
    
    def format_notification(self, notification_data: Dict[str, Any]) -> str:
        """格式化通知消息"""
        try:
            # 添加调试信息
            logger.debug(f"开始格式化通知消息，数据结构: {json.dumps(notification_data, ensure_ascii=False, indent=2)[:500]}...")
            
            # 提取数据
            original_msg = notification_data.get('data', {}).get('original_message', {})
            analysis_results = notification_data.get('data', {}).get('analysis_results', [])
            summary = notification_data.get('data', {}).get('summary', {})
            
            logger.debug(f"提取到的数据 - original_msg: {bool(original_msg)}, analysis_results: {len(analysis_results)}, summary: {bool(summary)}")
            
            # 获取原始消息数据
            original_data = original_msg.get('data', {})
            logger.debug(f"原始消息数据: {bool(original_data)}, keys: {list(original_data.keys()) if original_data else []}")
            
            # 获取消息来源
            source = original_msg.get('source', 'unknown')
            
            # 获取情绪分析结果
            sentiment_result = self._get_sentiment_result(analysis_results)
            if not sentiment_result:
                logger.debug("未找到情绪分析结果")
                return None
            
            logger.debug(f"情绪分析结果: {sentiment_result}")
            
            # 构建消息
            message_parts = []
            
            # 分析结果和评分
            sentiment = sentiment_result.get('sentiment', '未知')
            score = sentiment_result.get('score', 0.0)
            reason = sentiment_result.get('reason', '无')
            
            # 情绪图标
            emoji = self._get_sentiment_emoji(sentiment, score)
            
            # 主要分析结果
            message_parts.append(f"{emoji} <b>分析结果:</b> {sentiment}")
            
            if self.config.get('include_score', True):
                message_parts.append(f"📊 <b>评分:</b> {score:.2f}")
            
            if self.config.get('include_reason', True) and reason != '无':
                message_parts.append(f"💡 <b>理由:</b> {reason}")
            
            # 来源信息 - 根据不同来源显示不同信息
            if self.config.get('include_source', True):
                if source == 'twitter':
                    # Twitter消息
                    list_url = original_data.get('list_url', '')
                    username = original_data.get('username', '未知用户')
                    
                    # 从列表URL中提取列表名称，如果没有则显示"未知列表"
                    list_name = '未知列表'
                    if list_url:
                        # 尝试从URL中提取列表ID或名称
                        if '/lists/' in list_url:
                            list_id = list_url.split('/lists/')[-1].split('?')[0]
                            list_name = f"列表 {list_id}"
                        else:
                            list_name = '未知列表'
                    
                    message_parts.append(f"🐦 <b>来源:</b> Twitter - {list_name}")
                    message_parts.append(f"👤 <b>用户:</b> {username} (@{username})")
                    
                    # 添加Twitter链接（如果有）
                    tweet_url = original_data.get('tweet_url')
                    if tweet_url:
                        message_parts.append(f"🔗 <a href=\"{tweet_url}\">查看推文</a>")
                else:
                    # Telegram消息
                    chat_title = original_data.get('chat_title', '未知群组')
                    message_parts.append(f"📱 <b>来源:</b> Telegram - {chat_title}")
            
            # 原文引用
            raw_text = original_data.get('raw_text') or original_data.get('text', '')
            if raw_text:
                # 限制文本长度
                max_length = self.config.get('max_text_length', 500)
                if len(raw_text) > max_length:
                    raw_text = raw_text[:max_length] + '...'
                
                message_parts.append(f"\n<pre>{self._escape_html(raw_text)}</pre>")
            
            # @原作者 - 仅对Telegram消息显示
            if source == 'telegram' and self.config.get('include_author', True):
                username_tg = original_data.get('username')
                first_name = original_data.get('first_name')
                
                if username_tg:
                    message_parts.append(f"\n👤 @{username_tg}")
                elif first_name:
                    message_parts.append(f"\n👤 {first_name}")
            
            # 时间戳
            timestamp = datetime.now().strftime('%H:%M:%S')
            message_parts.append(f"\n⏰ {timestamp}")
            
            result = '\n'.join(message_parts)
            logger.debug(f"格式化完成，消息长度: {len(result)}")
            return result
            
        except Exception as e:
            logger.error(f"格式化消息失败: {e}", exc_info=True)
            return None
    
    def _get_sentiment_result(self, analysis_results: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """获取情绪分析结果"""
        for result in analysis_results:
            if result.get('agent_type') == 'sentiment_analysis':
                return result.get('result', {})
        return None
    
    def _get_sentiment_emoji(self, sentiment: str, score: float) -> str:
        """根据情绪和评分获取表情符号"""
        if sentiment == '利多':
            if abs(score) > 0.8:
                return '🚀'  # 强烈利多
            elif abs(score) > 0.5:
                return '📈'  # 利多
            else:
                return '🟢'  # 弱利多
        elif sentiment == '利空':
            if abs(score) > 0.8:
                return '💥'  # 强烈利空
            elif abs(score) > 0.5:
                return '📉'  # 利空
            else:
                return '🔴'  # 弱利空
        else:
            return '⚪'  # 中性
    
    def _escape_html(self, text: str) -> str:
        """转义HTML特殊字符"""
        return (text.replace('&', '&amp;')
                   .replace('<', '&lt;')
                   .replace('>', '&gt;'))
    
    def _extract_symbols(self, original_data: Dict[str, Any], source: str) -> List[str]:
        """从原始消息数据中提取数字货币符号"""
        try:
            symbols = []
            
            if source == 'twitter':
                # Twitter消息的符号提取
                crypto_symbols = original_data.get('crypto_symbols', [])
                extracted_data = original_data.get('extracted_data', {})
                extracted_symbols = extracted_data.get('symbols', [])
                
                # 合并两个来源的符号
                all_symbols = crypto_symbols + extracted_symbols
                symbols = all_symbols
            else:
                # Telegram消息的符号提取
                extracted_data = original_data.get('extracted_data', {})
                symbols = extracted_data.get('symbols', [])
            
            # 去重并转换为大写，限制数量避免消息过长
            unique_symbols = []
            seen = set()
            for symbol in symbols:
                if isinstance(symbol, dict):
                    # 如果是字典格式（CoinGecko API返回），提取symbol字段
                    symbol_str = symbol.get('symbol', '').upper()
                else:
                    # 如果是字符串格式
                    symbol_str = str(symbol).upper()
                
                if symbol_str and symbol_str not in seen and len(unique_symbols) < 10:  # 最多显示10个符号
                    unique_symbols.append(symbol_str)
                    seen.add(symbol_str)
            
            return unique_symbols
            
        except Exception as e:
            logger.debug(f"提取符号失败: {e}")
            return []

class MessageFilter:
    """消息过滤器"""
    
    def __init__(self, filter_config: Dict[str, Any]):
        self.config = filter_config
    
    def should_send(self, notification_data: Dict[str, Any]) -> bool:
        """判断是否应该发送消息"""
        try:
            analysis_results = notification_data.get('data', {}).get('analysis_results', [])
            
            # 获取情绪分析结果
            sentiment_result = self._get_sentiment_result(analysis_results)
            if not sentiment_result:
                logger.debug("没有情绪分析结果，跳过")
                return False
            
            sentiment = sentiment_result.get('sentiment', '中性')
            score = sentiment_result.get('score', 0.0)
            
            # 评分阈值过滤（使用绝对值）
            min_threshold = self.config.get('min_score_threshold', 0.0)
            if abs(score) < min_threshold:
                logger.debug(f"评分绝对值 {abs(score):.2f} 低于阈值 {min_threshold}，跳过")
                return False
            
            # 情绪过滤
            sentiment_filter = self.config.get('sentiment_filter', [])
            if sentiment_filter and sentiment not in sentiment_filter:
                logger.debug(f"情绪 {sentiment} 不在过滤列表中，跳过")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"过滤判断失败: {e}")
            return False
    
    def _get_sentiment_result(self, analysis_results: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """获取情绪分析结果"""
        for result in analysis_results:
            if result.get('agent_type') == 'sentiment_analysis':
                return result.get('result', {})
        return None

class TelegramNotifier:
    """Telegram通知器"""
    
    def __init__(self, config: Config):
        self.config = config
        self.telegram_config = config.get_telegram_config()
        self.rate_limiter = None
        self.message_formatter = None
        self.message_filter = None
        self.bot = None
        self.target_groups = []
        
        self._initialize_components()
    
    def _initialize_components(self):
        """初始化组件"""
        # 初始化Bot
        bot_token = self.telegram_config.get('bot_token')
        if not bot_token or bot_token == 'YOUR_BOT_TOKEN_HERE':
            raise ValueError("请在配置文件中设置有效的 Telegram Bot Token")
        
        self.bot = Bot(token=bot_token)
        
        # 初始化目标群组
        groups = self.telegram_config.get('target_groups', [])
        self.target_groups = [g for g in groups if g.get('enabled', True)]
        
        if not self.target_groups:
            raise ValueError("没有配置启用的目标群组")
        
        # 初始化限流器
        rate_config = self.config.get_rate_limit_config()
        if rate_config.get('enabled', True):
            self.rate_limiter = RateLimiter(
                max_messages_per_minute=rate_config.get('max_messages_per_minute', 10),
                cooldown_seconds=rate_config.get('cooldown_seconds', 3)
            )
        
        # 初始化消息格式化器
        format_config = self.telegram_config.get('message_format', {})
        self.message_formatter = MessageFormatter(format_config)
        
        # 初始化消息过滤器
        filter_config = self.config.get_filters_config()
        self.message_filter = MessageFilter(filter_config)
        
        logger.info(f"Telegram通知器初始化完成，目标群组: {len(self.target_groups)} 个")
    
    async def send_notification(self, notification_data: Dict[str, Any]):
        """发送通知消息"""
        try:
            # 过滤检查
            if not self.message_filter.should_send(notification_data):
                logger.debug("消息被过滤器拦截，不发送")
                return
            
            # 格式化消息
            message_text = self.message_formatter.format_notification(notification_data)
            if not message_text:
                logger.warning("消息格式化失败，跳过发送")
                return
            
            # 发送到所有目标群组
            for group in self.target_groups:
                await self._send_to_group(group, message_text)
            
        except Exception as e:
            logger.error(f"发送通知失败: {e}")
    
    async def _send_to_group(self, group: Dict[str, Any], message_text: str):
        """发送消息到指定群组"""
        chat_id = group.get('chat_id')
        group_name = group.get('name', str(chat_id))
        
        error_config = self.config.get_error_handling_config()
        retry_attempts = error_config.get('retry_attempts', 3)
        retry_delay = error_config.get('retry_delay', 5)
        
        for attempt in range(retry_attempts + 1):
            try:
                # 限流等待
                if self.rate_limiter:
                    await self.rate_limiter.wait_if_needed()
                
                # 发送消息
                await self.bot.send_message(
                    chat_id=chat_id,
                    text=message_text,
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True
                )
                
                logger.info(f"✅ 消息已发送到 {group_name} ({chat_id})")
                return
                
            except RetryAfter as e:
                # Telegram限流
                wait_time = e.retry_after
                logger.warning(f"Telegram限流，等待 {wait_time} 秒后重试")
                await asyncio.sleep(wait_time)
                
            except TimedOut:
                # 超时错误
                if attempt < retry_attempts:
                    logger.warning(f"发送超时，{retry_delay} 秒后重试 ({attempt + 1}/{retry_attempts})")
                    await asyncio.sleep(retry_delay)
                else:
                    logger.error(f"❌ 发送到 {group_name} 超时，已达最大重试次数")
                    
            except TelegramError as e:
                # 其他Telegram错误
                if "chat not found" in str(e).lower():
                    logger.error(f"❌ 群组 {group_name} ({chat_id}) 不存在或Bot未加入")
                    return
                elif "not enough rights" in str(e).lower():
                    logger.error(f"❌ Bot在群组 {group_name} 中没有发送消息权限")
                    return
                else:
                    if attempt < retry_attempts:
                        logger.warning(f"Telegram错误: {e}，{retry_delay} 秒后重试 ({attempt + 1}/{retry_attempts})")
                        await asyncio.sleep(retry_delay)
                    else:
                        logger.error(f"❌ 发送到 {group_name} 失败: {e}")
                        
            except Exception as e:
                # 其他未知错误
                if attempt < retry_attempts:
                    logger.warning(f"未知错误: {e}，{retry_delay} 秒后重试 ({attempt + 1}/{retry_attempts})")
                    await asyncio.sleep(retry_delay)
                else:
                    logger.error(f"❌ 发送到 {group_name} 失败: {e}")

class NotificationBot:
    """通知机器人主类"""
    
    def __init__(self, config_file: str = "config.yml"):
        self.config = Config(config_file)
        self.nats_client = None
        self.telegram_notifier = None
        self.running = False
        self.message_count = 0
    
    async def initialize(self):
        """初始化"""
        # 初始化NATS连接
        nats_config = self.config.get_nats_config()
        
        if not nats_config.get('enabled', False):
            raise ValueError("NATS未启用，请检查配置文件")
        
        try:
            self.nats_client = await nats.connect(
                servers=nats_config.get('servers', ['nats://localhost:4222'])
            )
            logger.info("NATS连接成功")
        except Exception as e:
            logger.error(f"NATS连接失败: {e}")
            raise
        
        # 初始化Telegram通知器
        try:
            self.telegram_notifier = TelegramNotifier(self.config)
            logger.info("Telegram通知器初始化成功")
        except Exception as e:
            logger.error(f"Telegram通知器初始化失败: {e}")
            raise
    
    async def start(self):
        """启动通知机器人"""
        nats_config = self.config.get_nats_config()
        subject = nats_config.get('subject', 'messages.notification')
        
        logger.info(f"开始监听NATS subject: {subject}")
        
        # 订阅通知消息
        await self.nats_client.subscribe(subject, cb=self._message_handler)
        
        self.running = True
        logger.info("🤖 通知机器人已启动，等待消息...")
        logger.info("如果长时间没有收到消息，请检查:")
        logger.info("1. analyze_agent是否正在运行")
        logger.info("2. NATS subject配置是否正确")
        logger.info("3. NATS服务器连接是否正常")
        
        try:
            # 保持运行
            while self.running:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("收到停止信号")
        finally:
            self.running = False
            if self.nats_client:
                await self.nats_client.close()
    
    async def _message_handler(self, msg):
        """处理接收到的通知消息"""
        try:
            self.message_count += 1
            logger.info(f"📨 收到通知消息 #{self.message_count} [subject: {msg.subject}], 大小: {len(msg.data)} bytes")
            
            # 解析消息
            notification_data = json.loads(msg.data.decode())
            
            # 验证消息类型
            if notification_data.get('type') != 'messages.notification':
                logger.warning(f"跳过非通知消息: type={notification_data.get('type')}")
                return
            
            if notification_data.get('source') != 'analyze_agent':
                logger.warning(f"跳过非analyze_agent消息: source={notification_data.get('source')}")
                return
            
            logger.info(f"处理通知消息: 来自 {notification_data.get('sender')}")
            
            # 发送Telegram通知
            await self.telegram_notifier.send_notification(notification_data)
            
        except Exception as e:
            logger.error(f"处理通知消息失败: {e}", exc_info=True)

async def main():
    """主函数"""
    try:
        # 创建通知机器人
        bot = NotificationBot()
        
        # 初始化
        await bot.initialize()
        
        # 启动
        await bot.start()
        
    except Exception as e:
        logger.error(f"程序启动失败: {e}")
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
