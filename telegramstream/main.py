#!/usr/bin/env python3
"""
Telegram 消息监控程序
支持配置群组/频道选择和多线程消息监控
"""

import asyncio
import json
import sys
import time
import re
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

import yaml
from telethon import TelegramClient, events
from telethon.tl.types import Channel, Chat
from prompt_toolkit.application import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import Layout
from prompt_toolkit.layout.containers import HSplit, VSplit
from prompt_toolkit.widgets import CheckboxList, Frame, Button
import emoji

# 导入符号匹配工具
from symbol_util import find_crypto_symbols

try:
    import nats
    NATS_AVAILABLE = True
except ImportError:
    NATS_AVAILABLE = False

# 配置日志
logging.basicConfig(
    level=logging.INFO,  # 恢复到 INFO 级别
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 抑制 Telethon 的调试日志
telethon_logger = logging.getLogger('telethon')
telethon_logger.setLevel(logging.WARNING)

class TelegramConfig:
    """Telegram 配置管理"""
    
    def __init__(self, config_file: str = "config.yml"):
        self.config_file = config_file
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        config_path = Path(self.config_file)
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        return {
            'telegram': {
                'api_id': '',
                'api_hash': '',
                'phone': '',
                'session': 'telegram_monitor'
            },
            'monitoring': {
                'groups': [],
                'channels': []
            },
            'nats': {
                'enabled': False,
                'servers': ['nats://localhost:4222'],
                'subject': 'telegram.messages'
            }
        }
    
    def save_config(self):
        """保存配置文件"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            yaml.dump(self.config, f, default_flow_style=False, allow_unicode=True)
    
    def get_telegram_config(self) -> Dict[str, str]:
        """获取 Telegram 配置"""
        return self.config.get('telegram', {})
    
    def get_monitoring_config(self) -> Dict[str, List]:
        """获取监控配置"""
        return self.config.get('monitoring', {'groups': [], 'channels': []})
    
    def get_nats_config(self) -> Dict[str, Any]:
        """获取 NATS 配置"""
        return self.config.get('nats', {})
    
    def update_monitoring_config(self, selected_chats: List[Dict[str, Any]]):
        """更新监控配置"""
        groups = []
        channels = []
        
        for chat in selected_chats:
            chat_info = {
                'id': chat['id'],
                'title': chat['title'],
                'type': chat['type']
            }
            if chat['type'] in ['group', 'supergroup']:
                groups.append(chat_info)
            elif chat['type'] == 'channel':
                channels.append(chat_info)
        
        self.config['monitoring'] = {
            'groups': groups,
            'channels': channels
        }

class MessageExtractor:
    """消息内容提取器"""
    
    # 正则表达式模式
    ETHEREUM_ADDRESS = re.compile(r'0x[a-fA-F0-9]{40}')
    SOLANA_ADDRESS = re.compile(r'[1-9A-HJ-NP-Za-km-z]{32,44}')
    BITCOIN_ADDRESS = re.compile(r'(bc1|[13])[a-zA-HJ-NP-Z0-9]{25,39}')
    SYMBOL_PATTERN = re.compile(r'\b[A-Z]{2,10}\b')
    URL_PATTERN = re.compile(r'https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:\w*))?)?')
    PRICE_PATTERN = re.compile(r'\$?(\d+(?:\.\d+)?)\s*(?:USD|USDT|USDC|\$)', re.IGNORECASE)
    
    # 关键词分类
    BULLISH_KEYWORDS = {'pump', 'moon', 'bullish', 'buy', 'long', 'rocket', 'up', 'rise', 'gain'}
    BEARISH_KEYWORDS = {'dump', 'bear', 'bearish', 'sell', 'short', 'crash', 'down', 'fall', 'loss'}
    NEUTRAL_KEYWORDS = {'analysis', 'chart', 'support', 'resistance', 'volume', 'trading'}
    
    async def extract_data(self, text: str) -> Dict[str, Any]:
        """提取消息中的结构化数据"""
        if not text:
            return {}
        
        # 移除表情符号获取纯文本
        raw_text = emoji.demojize(text)
        
        # 提取地址
        addresses = {
            'ethereum': list(set(self.ETHEREUM_ADDRESS.findall(text))),
            'solana': list(set(addr for addr in self.SOLANA_ADDRESS.findall(text) 
                               if self._is_valid_solana_address(addr))),
            'bitcoin': list(set(self.BITCOIN_ADDRESS.findall(text)))
        }
        
        # 使用CoinGecko API匹配数字货币符号和名称
        try:
            crypto_matches = await find_crypto_symbols(text)
            # 提取简单的符号列表（保持向后兼容）
            symbols = [match.get('symbol', '').upper() for match in crypto_matches]
            # 同时保存完整的数字货币信息
            crypto_data = crypto_matches
        except Exception as e:
            logger.error(f"CoinGecko符号匹配失败: {e}")
            # 降级到简单正则表达式匹配，使用清理后的文本
            cleaned_text = self._clean_text_for_matching(text)
            symbols = list(set(self.SYMBOL_PATTERN.findall(cleaned_text.upper())))
            crypto_data = []
        
        # 如果CoinGecko没有匹配到，尝试简单正则表达式作为备选
        if not symbols:
            cleaned_text = self._clean_text_for_matching(text)
            fallback_symbols = list(set(self.SYMBOL_PATTERN.findall(cleaned_text.upper())))
            symbols = fallback_symbols
        
        # 提取 URL
        urls = []
        for url in self.URL_PATTERN.findall(text):
            urls.append({
                'url': url,
                'domain': self._extract_domain(url),
                'type': self._classify_url(url)
            })
        
        # 提取价格
        prices = []
        for match in self.PRICE_PATTERN.finditer(text):
            prices.append({
                'price': float(match.group(1)),
                'currency': 'USD'
            })
        
        # 关键词分析
        text_lower = text.lower()
        keywords = []
        sentiment = 'neutral'
        
        bullish_count = sum(1 for kw in self.BULLISH_KEYWORDS if kw in text_lower)
        bearish_count = sum(1 for kw in self.BEARISH_KEYWORDS if kw in text_lower)
        
        if bullish_count > bearish_count:
            sentiment = 'positive'
        elif bearish_count > bullish_count:
            sentiment = 'negative'
        
        # 提取匹配的关键词
        all_keywords = self.BULLISH_KEYWORDS | self.BEARISH_KEYWORDS | self.NEUTRAL_KEYWORDS
        keywords = [kw for kw in all_keywords if kw in text_lower]
        
        return {
            'addresses': addresses,
            'symbols': symbols,
            'crypto_currencies': crypto_data,  # 新增：完整的数字货币信息
            'urls': urls,
            'prices': prices,
            'keywords': keywords,
            'sentiment': sentiment,
            'raw_text': raw_text
        }
    
    def _is_valid_solana_address(self, addr: str) -> bool:
        """验证 Solana 地址格式"""
        return 32 <= len(addr) <= 44 and addr.isalnum()
    
    def _extract_domain(self, url: str) -> str:
        """提取域名"""
        try:
            from urllib.parse import urlparse
            return urlparse(url).netloc
        except:
            return ''
    
    def _classify_url(self, url: str) -> str:
        """分类 URL 类型"""
        domain = self._extract_domain(url).lower()
        
        if any(dex in domain for dex in ['dexscreener', 'dextools', 'birdeye']):
            return 'dex_tracker'
        elif any(explorer in domain for explorer in ['etherscan', 'solscan', 'blockchain']):
            return 'blockchain_explorer'
        elif any(exchange in domain for exchange in ['binance', 'coinbase', 'okx']):
            return 'exchange'
        elif any(social in domain for social in ['twitter', 'telegram', 'discord']):
            return 'social_media'
        else:
            return 'unknown'
    
    def _clean_text_for_matching(self, text: str) -> str:
        """
        清理文本，移除URL和邮箱地址，避免误匹配
        
        Args:
            text: 原始文本
            
        Returns:
            清理后的文本
        """
        # URL 匹配模式（更全面的匹配）
        url_patterns = [
            r'https?://[^\s]+',  # http/https URLs
            r'www\.[^\s]+',      # www URLs
            r'[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(?:/[^\s]*)?',  # 域名格式
        ]
        
        # 邮箱匹配模式
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        
        # 文件扩展名模式（避免匹配.html, .com等）
        file_extension_pattern = r'\b\w+\.[a-zA-Z]{2,4}\b'
        
        cleaned_text = text
        
        # 移除URL
        for pattern in url_patterns:
            cleaned_text = re.sub(pattern, ' ', cleaned_text, flags=re.IGNORECASE)
        
        # 移除邮箱地址
        cleaned_text = re.sub(email_pattern, ' ', cleaned_text)
        
        # 移除文件扩展名（如 .html, .com 等）
        cleaned_text = re.sub(file_extension_pattern, ' ', cleaned_text)
        
        # 移除多余的空格
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
        
        return cleaned_text

class TelegramConfigUI:
    """Telegram 配置交互界面"""
    
    def __init__(self, client: TelegramClient):
        self.client = client
        self.chats = []
        self.selected_chats = []
        self.checkbox_list = None
        self.app = None
        self.confirm_exit = False  # 确认退出状态
    
    async def get_chats(self) -> List[Dict[str, Any]]:
        """获取所有群组和频道"""
        chats = []
        
        async for dialog in self.client.iter_dialogs():
            entity = dialog.entity
            
            if isinstance(entity, (Channel, Chat)):
                # 判断聊天类型
                if isinstance(entity, Channel):
                    if entity.broadcast:
                        chat_type = 'channel'  # 频道
                    else:
                        chat_type = 'supergroup'  # 超级群组
                else:  # isinstance(entity, Chat)
                    chat_type = 'group'  # 普通群组
                
                chats.append({
                    'id': entity.id,
                    'title': dialog.title,
                    'type': chat_type,
                    'username': getattr(entity, 'username', None)
                })
        
        return sorted(chats, key=lambda x: x['title'])
    
    def create_ui(self) -> Application:
        """创建用户界面"""
        # 获取已配置的群组/频道
        config = TelegramConfig()
        existing_config = config.get_monitoring_config()
        existing_chat_ids = set()
        
        # 收集已配置的群组/频道ID
        for group in existing_config.get('groups', []):
            existing_chat_ids.add(group['id'])
        for channel in existing_config.get('channels', []):
            existing_chat_ids.add(channel['id'])
        
        # 创建复选框列表，预选已配置的项目
        checkbox_values = []
        default_values = []
        
        for chat in self.chats:
            checkbox_values.append((chat, f"{chat['title']} ({chat['type']})"))
            # 如果这个聊天已经在配置中，则默认选中
            if chat['id'] in existing_chat_ids:
                default_values.append(chat)
        
        self.checkbox_list = CheckboxList(values=checkbox_values, default_values=default_values)
        
        # 创建按钮（添加快捷键说明）
        save_button = Button(text='保存配置 (F8)', handler=self._save_config)
        cancel_button = Button(text='取消 (ESC)', handler=self._cancel)
        
        # 创建动态标题控制
        def get_title():
            if self.confirm_exit:
                return '确认退出？再次按 ESC 退出，按任意键取消'
            selected_count = len(self.checkbox_list.current_values)
            return f'选择要监控的群组/频道 (已选: {selected_count}) (空格:选择 Tab:切换 F8:保存 ESC:退出)'
        
        # 创建布局
        checkbox_frame = Frame(
            body=self.checkbox_list,
            title=get_title,
            height=min(len(self.chats) + 3, 20)
        )
        
        buttons_container = VSplit([
            save_button,
            cancel_button
        ], padding=1)
        
        root_container = HSplit([
            checkbox_frame,
            buttons_container
        ])
        
        layout = Layout(root_container, focused_element=self.checkbox_list)
        
        # 创建键盘绑定
        kb = KeyBindings()
        
        @kb.add('tab')
        def _(event):
            """Tab 键：切换焦点"""
            event.app.layout.focus_next()
        
        @kb.add('s-tab')  # Shift+Tab
        def _(event):
            """Shift+Tab 键：反向切换焦点"""
            event.app.layout.focus_previous()
        
        @kb.add('escape')
        def _(event):
            """ESC 键：询问是否退出"""
            if not self.confirm_exit:
                # 第一次按 ESC，显示确认提示
                self.confirm_exit = True
                # 触发重绘
                event.app.invalidate()
            else:
                # 第二次按 ESC，确认退出
                print("\n退出配置（未保存）")
                event.app.exit(result='cancel')
        
        @kb.add('space')
        def _(event):
            """空格键：选择/取消选择，并更新显示"""
            # 让CheckboxList处理空格键
            event.app.layout.current_control.toggle_current()
            # 触发重绘以更新标题中的计数
            event.app.invalidate()
        
        @kb.add('<any>')
        def _(event):
            """任意键：取消退出确认"""
            if self.confirm_exit and event.key_sequence[0].key not in ['escape', 'f8', 'tab', 's-tab', 'space']:
                self.confirm_exit = False
                # 触发重绘
                event.app.invalidate()
        
        @kb.add('f8')
        def _(event):
            """F8 键：保存并退出"""
            self._save_config()
        
        @kb.add('c-c')
        @kb.add('c-d')
        def _(event):
            """Ctrl+C/Ctrl+D：强制退出"""
            event.app.exit()
        
        return Application(
            layout=layout,
            key_bindings=kb,
            full_screen=True
        )
    
    def _save_config(self):
        """保存配置"""
        self.selected_chats = [chat for chat in self.checkbox_list.current_values]
        group_count = len([chat for chat in self.selected_chats if chat['type'] in ['group', 'supergroup']])
        channel_count = len([chat for chat in self.selected_chats if chat['type'] == 'channel'])
        print(f"\n已选择 {len(self.selected_chats)} 个聊天:")
        print(f"  - 群组: {group_count} 个")
        print(f"  - 频道: {channel_count} 个")
        self.app.exit(result='save')
    
    def _cancel(self):
        """取消配置"""
        print("\n退出配置（未保存）")
        self.app.exit(result='cancel')
    
    async def run_config(self) -> Optional[List[Dict[str, Any]]]:
        """运行配置界面"""
        print("正在获取群组和频道列表...")
        self.chats = await self.get_chats()
        
        if not self.chats:
            print("未找到任何群组或频道")
            return None
        
        self.app = self.create_ui()
        result = await self.app.run_async()
        
        if result == 'save':
            return self.selected_chats
        return None

class TelegramMonitor:
    """Telegram 消息监控器"""
    
    def __init__(self, config: TelegramConfig):
        self.config = config
        self.client = None
        self.extractor = MessageExtractor()
        self.nats_client = None
        self.running = False
        
    async def initialize(self):
        """初始化客户端"""
        telegram_config = self.config.get_telegram_config()
        
        if not all([telegram_config.get('api_id'), telegram_config.get('api_hash')]):
            raise ValueError("请在 config.yml 中配置 Telegram API 信息")
        
        self.client = TelegramClient(
            telegram_config.get('session', 'telegram_monitor'),
            int(telegram_config['api_id']),
            telegram_config['api_hash']
        )
        
        # 抑制客户端连接期间的日志输出
        old_level = logging.getLogger().level
        logging.getLogger().setLevel(logging.ERROR)
        
        try:
            await self.client.start(phone=telegram_config.get('phone'))
        finally:
            # 恢复日志级别
            logging.getLogger().setLevel(old_level)
        
        # 初始化 NATS 连接
        nats_config = self.config.get_nats_config()
        if NATS_AVAILABLE and nats_config.get('enabled'):
            try:
                self.nats_client = await nats.connect(servers=nats_config.get('servers', ['nats://localhost:4222']))
                logger.info("NATS 连接成功")
            except Exception as e:
                logger.warning(f"NATS 连接失败: {e}")
                self.nats_client = None
    
    async def start_monitoring(self):
        """启动监控"""
        monitoring_config = self.config.get_monitoring_config()
        all_chats = monitoring_config.get('groups', []) + monitoring_config.get('channels', [])
        
        if not all_chats:
            logger.error("没有配置监控的群组或频道")
            return
        
        logger.info(f"开始监控 {len(all_chats)} 个群组/频道, NATS 状态: {NATS_AVAILABLE}" )
        logger.info("监控的聊天列表:")
        for chat in all_chats:
            logger.info(f"  - {chat['title']} (ID: {chat['id']}, 类型: {chat['type']})")
        
        # 注册事件处理器
        @self.client.on(events.NewMessage)
        async def handle_new_message(event):
            logger.debug(f"收到新消息事件，来自聊天 ID: {event.chat_id}")
            await self._handle_message(event, 'telegram.message')
        
        @self.client.on(events.MessageEdited)
        async def handle_edited_message(event):
            logger.debug(f"收到编辑消息事件，来自聊天 ID: {event.chat_id}")
            # await self._handle_message(event, 'telegram.edit')
            # await self._handle_message(event, 'telegram.message')
        
        @self.client.on(events.MessageDeleted)
        async def handle_deleted_message(event):
            logger.debug(f"收到删除消息事件，来自聊天 ID: {event.chat_id}")
            await self._handle_delete(event)
        
        self.running = True
        logger.info("监控已启动，按 Ctrl+C 停止")
        logger.info("等待消息...")
        
        try:
            await self.client.run_until_disconnected()
        except KeyboardInterrupt:
            logger.info("收到停止信号")
        finally:
            self.running = False
            if self.nats_client:
                await self.nats_client.close()
    
    async def _handle_message(self, event, message_type: str):
        """处理消息事件"""
        try:
            # 检查是否是监控的群组/频道
            chat_id = event.chat_id
            monitoring_config = self.config.get_monitoring_config()
            all_chats = monitoring_config.get('groups', []) + monitoring_config.get('channels', [])
            
            logger.debug(f"处理消息: 聊天ID {chat_id}, 类型 {message_type}")
            
            # 修复 ID 匹配问题：处理 Telegram 的 ID 格式差异
            def normalize_chat_id(id_value):
                """标准化聊天 ID，处理 -100 前缀"""
                if isinstance(id_value, str):
                    id_value = int(id_value)
                
                # 如果是负数且以 -100 开头，提取实际 ID
                if id_value < 0 and str(abs(id_value)).startswith('100'):
                    return abs(id_value) - 1000000000000  # 移除 -100 前缀
                return abs(id_value)  # 统一使用正数比较
            
            normalized_event_id = normalize_chat_id(chat_id)
            
            monitored_chat = None
            for chat in all_chats:
                config_id = normalize_chat_id(chat['id'])
                if config_id == normalized_event_id:
                    monitored_chat = chat
                    break
            
            if not monitored_chat:
                logger.debug(f"聊天 ID {chat_id} (标准化: {normalized_event_id}) 不在监控列表中，跳过")
                logger.debug(f"监控列表 ID: {[normalize_chat_id(chat['id']) for chat in all_chats]}")
                return
            
            logger.info(f"处理来自 '{monitored_chat['title']}' 的消息")
            
            # 获取消息信息
            message = event.message
            sender = await message.get_sender()
            
            # 提取结构化数据
            text = message.message or ''
            extracted_data = await self.extractor.extract_data(text)
            
            logger.debug(f"消息文本: {text[:100]}...")  # 只显示前100个字符
            
            # 构建消息数据
            message_data = {
                'type': message_type,
                'timestamp': int(time.time() * 1000),
                'source': 'telegram',
                'sender': 'telegramstream',
                'data': {
                    'message_id': message.id,
                    'chat_id': chat_id,
                    'chat_title': monitored_chat['title'],
                    'chat_type': monitored_chat['type'],
                    'user_id': sender.id if sender else None,
                    'username': getattr(sender, 'username', None),
                    'first_name': getattr(sender, 'first_name', None),
                    'is_bot': getattr(sender, 'bot', False),
                    'date': int(message.date.timestamp() * 1000),
                    'text': text,
                    'raw_text': extracted_data.get('raw_text', text),
                    'reply_to_message_id': message.reply_to_msg_id,
                    'forward_from_chat_id': getattr(message.forward, 'chat_id', None) if message.forward else None,
                    'entities': self._extract_entities(message),
                    'media': self._extract_media(message),
                    'extracted_data': extracted_data
                }
            }
            
            # 如果是编辑消息，添加编辑信息
            if message_type == 'telegram.edit':
                message_data['data']['edit_date'] = int(message.edit_date.timestamp() * 1000) if message.edit_date else None
            
            await self._send_message(message_data)
            
        except Exception as e:
            logger.error(f"处理消息时出错: {e}", exc_info=True)
    
    async def _handle_delete(self, event):
        """处理删除事件"""
        try:
            # 检查是否是监控的聊天
            chat_id = event.chat_id
            monitoring_config = self.config.get_monitoring_config()
            all_chats = monitoring_config.get('groups', []) + monitoring_config.get('channels', [])
            
            # 使用相同的 ID 标准化逻辑
            def normalize_chat_id(id_value):
                """标准化聊天 ID，处理 -100 前缀"""
                if isinstance(id_value, str):
                    id_value = int(id_value)
                
                # 如果是负数且以 -100 开头，提取实际 ID
                if id_value < 0 and str(abs(id_value)).startswith('100'):
                    return abs(id_value) - 1000000000000  # 移除 -100 前缀
                return abs(id_value)  # 统一使用正数比较
            
            normalized_event_id = normalize_chat_id(chat_id)
            
            monitored_chat = None
            for chat in all_chats:
                config_id = normalize_chat_id(chat['id'])
                if config_id == normalized_event_id:
                    monitored_chat = chat
                    break
            
            if not monitored_chat:
                logger.debug(f"删除事件：聊天 ID {chat_id} 不在监控列表中，跳过")
                return
            
            # 构建删除消息数据
            message_data = {
                'type': 'telegram.delete',
                'timestamp': int(time.time() * 1000),
                'source': 'telegram',
                'sender': 'telegramstream',
                'data': {
                    'message_ids': event.deleted_ids,
                    'chat_id': chat_id,
                    'chat_title': monitored_chat['title'],
                    'deleted_at': int(time.time() * 1000)  # 统一为毫秒时间戳
                }
            }
            
            await self._send_message(message_data)
            
        except Exception as e:
            logger.error(f"处理删除事件时出错: {e}")
    
    def _extract_entities(self, message) -> List[Dict[str, Any]]:
        """提取消息实体"""
        entities = []
        if hasattr(message, 'entities') and message.entities:
            for entity in message.entities:
                entity_data = {
                    'type': entity.__class__.__name__.lower(),
                    'offset': entity.offset,
                    'length': entity.length
                }
                
                # 添加特定类型的额外信息
                if hasattr(entity, 'url'):
                    entity_data['url'] = entity.url
                elif hasattr(entity, 'user_id'):
                    entity_data['user_id'] = entity.user_id
                
                entities.append(entity_data)
        
        return entities
    
    def _extract_media(self, message) -> Optional[Dict[str, Any]]:
        """提取媒体信息"""
        if not message.media:
            return None
        
        media_data = {
            'type': message.media.__class__.__name__.lower()
        }
        
        # 根据媒体类型添加信息
        if hasattr(message.media, 'photo'):
            media_data.update({
                'file_id': str(message.media.photo.id),
                'caption': getattr(message, 'message', '')
            })
        elif hasattr(message.media, 'document'):
            doc = message.media.document
            media_data.update({
                'file_id': str(doc.id),
                'file_size': doc.size,
                'mime_type': doc.mime_type,
                'caption': getattr(message, 'message', '')
            })
        
        return media_data
    
    async def _send_message(self, message_data: Dict[str, Any]):
        """发送消息到队列或控制台"""
        message_json = json.dumps(message_data, ensure_ascii=False, separators=(',', ':'))
        
        # 发送到 NATS
        if self.nats_client:
            try:
                nats_config = self.config.get_nats_config()
                subject = nats_config.get('subject', 'telegram.messages')
                await self.nats_client.publish(subject, message_json.encode())
                logger.debug(f"消息已发送到 NATS: {subject}")
            except Exception as e:
                logger.error(f"发送到 NATS 失败: {e}")
        
        # 控制台输出
        print(f"[{datetime.now().isoformat()}] {message_json}")

async def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法:")
        print("  python main.py config  - 配置监控的群组/频道")
        print("  python main.py start   - 启动监控")
        return
    
    command = sys.argv[1]
    config = TelegramConfig()
    
    if command == 'config':
        # 配置模式
        telegram_config = config.get_telegram_config()
        
        if not all([telegram_config.get('api_id'), telegram_config.get('api_hash')]):
            print("请先在 config.yml 中配置 Telegram API 信息:")
            print("telegram:")
            print("  api_id: 'your_api_id'")
            print("  api_hash: 'your_api_hash'")
            print("  phone: 'your_phone_number'")
            return
        
        # 初始化客户端
        client = TelegramClient(
            telegram_config.get('session', 'telegram_monitor'),
            int(telegram_config['api_id']),
            telegram_config['api_hash']
        )
        
        # 抑制客户端连接期间的日志输出
        old_level = logging.getLogger().level
        logging.getLogger().setLevel(logging.ERROR)
        
        try:
            await client.start(phone=telegram_config.get('phone'))
        finally:
            # 恢复日志级别
            logging.getLogger().setLevel(old_level)
        
        # 运行配置界面
        ui = TelegramConfigUI(client)
        selected_chats = await ui.run_config()
        
        if selected_chats:
            config.update_monitoring_config(selected_chats)
            config.save_config()
            print(f"已保存 {len(selected_chats)} 个群组/频道的配置")
        else:
            print("已取消配置")
        
        await client.disconnect()
    
    elif command == 'start':
        # 监控模式
        monitor = TelegramMonitor(config)
        
        # 验证配置
        monitoring_config = config.get_monitoring_config()
        all_chats = monitoring_config.get('groups', []) + monitoring_config.get('channels', [])
        
        logger.info(f"从配置文件读取到 {len(all_chats)} 个监控目标")
        if not all_chats:
            print("❌ 没有配置任何监控的群组或频道")
            print("请先运行: python main.py config")
            return
        
        await monitor.initialize()
        await monitor.start_monitoring()
    
    else:
        print(f"未知命令: {command}")

if __name__ == '__main__':
    asyncio.run(main())
