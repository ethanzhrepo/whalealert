#!/usr/bin/env python3
"""
Analyze Agent - 多Agent消息分析系统
监听NATS消息队列，使用多个AI Agent对Telegram消息进行分析和加工
"""

import asyncio
import json
import logging
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

import yaml
import nats
from pydantic import BaseModel, Field

# LangChain imports
from langchain.schema import BaseMessage, HumanMessage
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

# 导入去重模块
from deduplication import get_deduplicator, cleanup_deduplicator, ensure_model_available

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
        
        logging.basicConfig(level=level, format=format_str, force=True)
    
    def get_nats_config(self) -> Dict[str, Any]:
        """获取NATS配置"""
        return self.config.get('nats', {})
    
    def get_llm_config(self) -> Dict[str, Any]:
        """获取LLM配置"""
        return self.config.get('llm', {})
    
    def get_agents_config(self) -> Dict[str, Any]:
        """获取Agent配置"""
        return self.config.get('agents', {})
    
    def get_deduplication_config(self) -> Dict[str, Any]:
        """获取去重配置"""
        return self.config.get('deduplication', {})

class SentimentAnalysisResult(BaseModel):
    """情绪分析结果模型"""
    情绪: str = Field(description="利多/利空/中性")
    理由: str = Field(description="判断理由")
    情绪评分: float = Field(description="情绪评分，范围-1.0到1.0")

class LLMManager:
    """LLM管理器，支持多种LLM提供商"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.provider = config.get('provider', 'ollama')
        self.llm = self._initialize_llm()
    
    def _initialize_llm(self):
        """初始化LLM实例"""
        if self.provider == 'ollama':
            ollama_config = self.config.get('ollama', {})
            return ChatOllama(
                base_url=ollama_config.get('base_url', 'http://localhost:11434'),
                model=ollama_config.get('model', 'llama3.1:8b'),
                temperature=ollama_config.get('temperature', 0.1),
                timeout=ollama_config.get('timeout', 30)
            )
        
        elif self.provider == 'openai':
            openai_config = self.config.get('openai', {})
            return ChatOpenAI(
                api_key=openai_config.get('api_key'),
                model=openai_config.get('model', 'gpt-4o-mini'),
                temperature=openai_config.get('temperature', 0.1),
                max_tokens=openai_config.get('max_tokens', 1000),
                timeout=openai_config.get('timeout', 30)
            )
        
        elif self.provider == 'anthropic':
            anthropic_config = self.config.get('anthropic', {})
            return ChatAnthropic(
                api_key=anthropic_config.get('api_key'),
                model=anthropic_config.get('model', 'claude-3-haiku-20240307'),
                temperature=anthropic_config.get('temperature', 0.1),
                max_tokens=anthropic_config.get('max_tokens', 1000),
                timeout=anthropic_config.get('timeout', 30)
            )
        
        else:
            raise ValueError(f"不支持的LLM提供商: {self.provider}")
    
    async def generate_response(self, prompt: str) -> str:
        """生成LLM响应"""
        try:
            messages = [HumanMessage(content=prompt)]
            response = await self.llm.ainvoke(messages)
            return response.content
        except Exception as e:
            logger.error(f"LLM调用失败: {e}")
            raise

class BaseAgent(ABC):
    """Agent基类"""
    
    def __init__(self, name: str, llm_manager: LLMManager):
        self.name = name
        self.llm_manager = llm_manager
        logger.info(f"初始化Agent: {name}")
    
    @abstractmethod
    async def process(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理消息的抽象方法"""
        pass
    
    def _extract_raw_text(self, message_data: Dict[str, Any]) -> str:
        """从消息数据中提取raw_text"""
        try:
            # 优先使用extracted_data中的raw_text
            raw_text = message_data.get('data', {}).get('extracted_data', {}).get('raw_text', '')
            if raw_text and raw_text.strip():
                return raw_text.strip()
            
            # 降级到普通text字段
            text = message_data.get('data', {}).get('text', '')
            if text and text.strip():
                return text.strip()
            
            # 再降级到raw_text字段（直接在data下）
            raw_text_direct = message_data.get('data', {}).get('raw_text', '')
            if raw_text_direct and raw_text_direct.strip():
                return raw_text_direct.strip()
            
            return ''
        except Exception as e:
            logger.warning(f"提取raw_text失败: {e}")
            # 最后的降级方案
            return message_data.get('data', {}).get('text', '')

class SentimentAnalysisAgent(BaseAgent):
    """情绪分析Agent"""
    
    def __init__(self, llm_manager: LLMManager):
        super().__init__("情绪分析Agent", llm_manager)
    
    async def process(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理情绪分析"""
        start_time = time.time()
        
        raw_text = self._extract_raw_text(message_data)
        
        if not raw_text or len(raw_text.strip()) < 10:
            logger.debug("文本内容太短，跳过情绪分析")
            return self._create_neutral_result("文本内容太短", start_time)
        
        try:
            # 输出正在分析的文本信息
            logger.info(f"🤖 {self.name} 开始分析...")
            logger.info(f"📊 分析文本长度: {len(raw_text)} 字符")
            if len(raw_text) <= 200:
                logger.info(f"📊 分析文本: {raw_text}")
            else:
                logger.info(f"📊 分析文本: {raw_text[:200]}... [已截断]")
            
            # 构建提示词
            prompt = self._build_prompt(raw_text)
            
            # 调用LLM
            logger.info(f"🔄 调用 {self.llm_manager.provider} LLM 进行情绪分析...")
            response = await self.llm_manager.generate_response(prompt)
            
            # 解析响应
            result = self._parse_response(response)
            
            processing_time = int((time.time() - start_time) * 1000)
            
            # 输出分析结果
            logger.info(f"✅ 情绪分析完成!")
            logger.info(f"📈 分析结果: {result.情绪} (评分: {result.情绪评分:.2f})")
            logger.info(f"💭 分析理由: {result.理由}")
            logger.info(f"⏱️  处理耗时: {processing_time}ms")
            
            return self._format_result(result, message_data, processing_time)
            
        except Exception as e:
            logger.error(f"❌ 情绪分析失败: {e}")
            return self._create_error_result(str(e), message_data, start_time)
    
    def _build_prompt(self, text: str) -> str:
        """构建情绪分析提示词"""
        return f"""你是一位资深加密货币分析师，请分析以下币圈新闻所传达的市场情绪。

新闻内容：
{text}

请直接输出如下格式的 JSON，不要包含任何解释、思考过程或其他文字：

{{
  "情绪": "利多 / 利空 / 中性（三选一）",
  "理由": "一句话解释为什么你判断为这种情绪",
  "情绪评分": 数值（范围从 -1.0 到 1.0，越接近 1 表示越利多，越接近 -1 表示越利空）
}}

只返回JSON，不要任何其他内容："""
    
    def _parse_response(self, response: str) -> SentimentAnalysisResult:
        """解析LLM响应"""
        try:
            # 清理响应内容
            response = response.strip()
            
            # 移除思考标签（如 <think>...</think>）
            import re
            # 移除 <think>...</think> 标签及其内容
            response = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL)
            
            # 移除其他可能的思考标签
            response = re.sub(r'<thinking>.*?</thinking>', '', response, flags=re.DOTALL)
            response = re.sub(r'<thought>.*?</thought>', '', response, flags=re.DOTALL)
            
            # 清理多余的空白字符
            response = response.strip()
            
            # 尝试提取JSON部分
            if response.startswith('```json'):
                response = response[7:]
            if response.endswith('```'):
                response = response[:-3]
            
            # 使用正则表达式提取JSON对象
            json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
            json_matches = re.findall(json_pattern, response, re.DOTALL)
            
            if json_matches:
                # 使用第一个匹配的JSON对象
                response = json_matches[0].strip()
            else:
                # 如果没有找到完整的JSON，尝试逐行解析
                lines = response.split('\n')
                json_lines = []
                in_json = False
                brace_count = 0
                
                for line in lines:
                    line = line.strip()
                    if not in_json and line.startswith('{'):
                        in_json = True
                        json_lines.append(line)
                        brace_count += line.count('{') - line.count('}')
                    elif in_json:
                        json_lines.append(line)
                        brace_count += line.count('{') - line.count('}')
                        if brace_count <= 0:
                            break
                
                if json_lines:
                    response = '\n'.join(json_lines)
            
            # 再次清理
            response = response.strip()
            
            logger.debug(f"清理后的响应: {response[:200]}...")
            
            # 解析JSON
            data = json.loads(response)
            
            # 验证和标准化数据
            sentiment = data.get('情绪', '中性')
            if sentiment not in ['利多', '利空', '中性']:
                sentiment = '中性'
            
            reason = data.get('理由', '无法确定')
            score = float(data.get('情绪评分', 0.0))
            score = max(-1.0, min(1.0, score))  # 限制在[-1, 1]范围内
            
            return SentimentAnalysisResult(
                情绪=sentiment,
                理由=reason,
                情绪评分=score
            )
            
        except Exception as e:
            logger.warning(f"解析LLM响应失败: {e}, 原始响应: {response[:200]}...")
            return SentimentAnalysisResult(
                情绪="中性",
                理由="解析失败",
                情绪评分=0.0
            )
    
    def _format_result(self, result: SentimentAnalysisResult, original_message: Dict[str, Any], processing_time: int) -> Dict[str, Any]:
        """格式化分析结果"""
        return {
            'type': 'analysis.sentiment',
            'timestamp': int(time.time() * 1000),
            'source': 'analyze_agent',
            'sender': 'sentiment_analysis_agent',
            'agent_name': self.name,
            'original_message_id': original_message.get('data', {}).get('message_id'),
            'original_chat_id': original_message.get('data', {}).get('chat_id'),
            'data': {
                'sentiment': result.情绪,
                'reason': result.理由,
                'score': result.情绪评分,
                'analysis_time': datetime.now().isoformat(),
                'llm_provider': self.llm_manager.provider,
                'processing_time': processing_time
            }
        }
    
    def _create_neutral_result(self, reason: str, start_time: float) -> Dict[str, Any]:
        """创建中性结果"""
        return {
            'type': 'analysis.sentiment',
            'timestamp': int(time.time() * 1000),
            'source': 'analyze_agent',
            'sender': 'sentiment_analysis_agent',
            'agent_name': self.name,
            'data': {
                'sentiment': '中性',
                'reason': reason,
                'score': 0.0,
                'analysis_time': datetime.now().isoformat(),
                'llm_provider': self.llm_manager.provider,
                'processing_time': int((time.time() - start_time) * 1000)
            }
        }
    
    def _create_error_result(self, error: str, original_message: Dict[str, Any], start_time: float) -> Dict[str, Any]:
        """创建错误结果"""
        return {
            'type': 'analysis.error',
            'timestamp': int(time.time() * 1000),
            'source': 'analyze_agent',
            'sender': 'sentiment_analysis_agent',
            'agent_name': self.name,
            'original_message_id': original_message.get('data', {}).get('message_id'),
            'data': {
                'error': error,
                'analysis_time': datetime.now().isoformat(),
                'processing_time': int((time.time() - start_time) * 1000)
            }
        }

class AgentManager:
    """Agent管理器"""
    
    def __init__(self, config: Config, llm_manager: LLMManager):
        self.config = config
        self.llm_manager = llm_manager
        self.agents: List[BaseAgent] = []
        self._initialize_agents()
    
    def _initialize_agents(self):
        """初始化所有启用的Agent"""
        agents_config = self.config.get_agents_config()
        
        # 情绪分析Agent
        if agents_config.get('sentiment_analysis', {}).get('enabled', False):
            self.agents.append(SentimentAnalysisAgent(self.llm_manager))
        
        # 未来可以在这里添加更多Agent
        # if agents_config.get('price_analysis', {}).get('enabled', False):
        #     self.agents.append(PriceAnalysisAgent(self.llm_manager))
        
        logger.info(f"已初始化 {len(self.agents)} 个Agent")
    
    async def process_message(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """使用所有Agent处理消息，返回格式化的结果"""
        start_time = time.time()
        results = []
        successful_count = 0
        failed_count = 0
        
        for agent in self.agents:
            try:
                result = await agent.process(message_data)
                if result:
                    # 格式化Agent结果
                    agent_result = {
                        'agent_name': agent.name,
                        'agent_type': self._get_agent_type(agent),
                        'result': result.get('data', {}),
                        'processing_time_ms': result.get('data', {}).get('processing_time', 0),
                        'llm_provider': result.get('data', {}).get('llm_provider', ''),
                        'analysis_time': result.get('data', {}).get('analysis_time', datetime.now().isoformat())
                    }
                    results.append(agent_result)
                    
                    if result.get('type') != 'analysis.error':
                        successful_count += 1
                    else:
                        failed_count += 1
                else:
                    failed_count += 1
            except Exception as e:
                logger.error(f"Agent {agent.name} 处理失败: {e}")
                failed_count += 1
        
        end_time = time.time()
        total_processing_time = int((end_time - start_time) * 1000)
        
        # 计算综合情绪和评分
        overall_sentiment, overall_score = self._calculate_overall_sentiment(results)
        
        # 构建汇总信息
        summary = {
            'total_agents': len(self.agents),
            'successful_analyses': successful_count,
            'failed_analyses': failed_count,
            'overall_sentiment': overall_sentiment,
            'overall_score': overall_score,
            'processing_start_time': datetime.fromtimestamp(start_time).isoformat() + 'Z',
            'processing_end_time': datetime.fromtimestamp(end_time).isoformat() + 'Z',
            'total_processing_time_ms': total_processing_time
        }
        
        return {
            'analysis_results': results,
            'summary': summary
        }
    
    def _get_agent_type(self, agent: BaseAgent) -> str:
        """获取Agent类型标识符"""
        if isinstance(agent, SentimentAnalysisAgent):
            return 'sentiment_analysis'
        # 未来可以添加更多Agent类型
        return 'unknown'
    
    def _calculate_overall_sentiment(self, results: List[Dict[str, Any]]) -> tuple[str, float]:
        """计算综合情绪和评分"""
        if not results:
            return '中性', 0.0
        
        # 目前只有情绪分析Agent，直接使用其结果
        sentiment_results = [r for r in results if r.get('agent_type') == 'sentiment_analysis']
        
        if not sentiment_results:
            return '中性', 0.0
        
        # 如果只有一个情绪分析结果，直接使用
        if len(sentiment_results) == 1:
            result_data = sentiment_results[0].get('result', {})
            return result_data.get('sentiment', '中性'), result_data.get('score', 0.0)
        
        # 如果有多个情绪分析结果，计算平均值
        total_score = sum(r.get('result', {}).get('score', 0.0) for r in sentiment_results)
        avg_score = total_score / len(sentiment_results)
        
        # 根据平均评分确定综合情绪
        if avg_score > 0.3:
            overall_sentiment = '利多'
        elif avg_score < -0.3:
            overall_sentiment = '利空'
        else:
            overall_sentiment = '中性'
        
        return overall_sentiment, avg_score

class AnalyzeAgent:
    """主分析系统"""
    
    def __init__(self, config_file: str = "config.yml"):
        self.config = Config(config_file)
        self.llm_manager = LLMManager(self.config.get_llm_config())
        self.agent_manager = AgentManager(self.config, self.llm_manager)
        self.nats_client = None
        self.running = False
        self.deduplicator = None
    
    async def initialize(self):
        """初始化NATS连接和去重器"""
        # 检测和初始化去重器
        dedup_config = self.config.get_deduplication_config()
        if dedup_config.get('enabled', False):
            logger.info("检测消息去重配置...")
            
            # 获取模型名称
            model_name = dedup_config.get('model_name', 'BAAI/bge-m3')
            logger.info(f"去重模型: {model_name}")
            
            # 检查并确保模型可用
            logger.info("检查去重模型可用性...")
            model_available = await ensure_model_available(model_name)
            
            if not model_available:
                logger.error(f"去重模型不可用: {model_name}")
                logger.error("请检查网络连接或模型路径，或在配置中禁用去重功能")
                raise RuntimeError(f"去重模型不可用: {model_name}")
            
            # 初始化去重器（此时模型已确保可用）
            logger.info("初始化消息去重器...")
            self.deduplicator = await get_deduplicator(dedup_config)
            logger.info("消息去重器初始化完成")
        else:
            logger.info("消息去重功能已禁用")
        
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
    
    async def start_monitoring(self):
        """开始监控消息"""
        nats_config = self.config.get_nats_config()
        subjects = nats_config.get('subject', [])
        
        if not subjects:
            raise ValueError("未配置监控的subject")
        
        logger.info(f"开始监控NATS subjects: {subjects}")
        
        # 订阅所有配置的subject
        for subject in subjects:
            await self.nats_client.subscribe(subject, cb=self._message_handler)
            logger.info(f"已订阅subject: {subject}")
        
        self.running = True
        logger.info("消息监控已启动，等待消息...")
        logger.info("如果长时间没有收到消息，请检查:")
        logger.info("1. telegramstream是否正在运行")
        logger.info("2. telegramstream的NATS subject配置是否正确")
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
            # 清理去重器
            if self.deduplicator:
                await cleanup_deduplicator()
    
    async def _message_handler(self, msg):
        """处理接收到的消息"""
        try:
            # 添加调试信息
            logger.info(f"收到NATS消息 [subject: {msg.subject}], 大小: {len(msg.data)} bytes")
            
            # 解析消息
            message_data = json.loads(msg.data.decode())
            
            logger.info(f"解析消息成功: type={message_data.get('type')}, source={message_data.get('source')}")
            
            # 处理telegram和twitter消息
            source = message_data.get('source')
            if source not in ['telegram', 'twitter']:
                logger.info(f"跳过不支持的消息源: source={source}")
                return
            
            # 提取并输出原文和来源信息
            data = message_data.get('data', {})
            text = data.get('text', '') or data.get('raw_text', '')
            username = data.get('username', '') or data.get('user_id', '')
            chat_title = data.get('chat_title', '') if source == 'telegram' else ''
            list_url = data.get('list_url', '') if source == 'twitter' else ''
            message_id = data.get('message_id', '')
            
            # 调试：显示所有可能的文本字段
            logger.debug(f"🔍 调试文本字段:")
            logger.debug(f"   data.text: '{data.get('text', '')}'")
            logger.debug(f"   data.raw_text: '{data.get('raw_text', '')}'")
            logger.debug(f"   data.extracted_data.raw_text: '{data.get('extracted_data', {}).get('raw_text', '')}'")
            
            # 输出消息来源和原文信息
            logger.info("=" * 80)
            logger.info(f"📨 消息来源: {source.upper()}")
            logger.info(f"🆔 消息ID: {message_id}")
            if source == 'telegram':
                logger.info(f"👤 用户: {username}")
                if chat_title:
                    logger.info(f"💬 群组: {chat_title}")
            elif source == 'twitter':
                logger.info(f"👤 用户: @{username}")
                if list_url:
                    logger.info(f"📋 列表: {list_url}")
            
            # 输出原文内容
            if text:
                logger.info(f"📝 原文内容:")
                # 如果文本太长，截断显示
                if len(text) > 500:
                    logger.info(f"   {text[:500]}...")
                    logger.info(f"   [文本长度: {len(text)} 字符，已截断显示]")
                else:
                    logger.info(f"   {text}")
            else:
                logger.info("📝 原文内容: [无文本内容]")
            
            logger.info("=" * 80)
            
            logger.info(f"开始处理{source}消息: {message_data.get('type')}")
            
            # 消息去重检查
            if self.deduplicator:
                is_duplicate, similar_record, similarity_score = await self.deduplicator.check_duplicate(message_data)
                
                if is_duplicate:
                    logger.info(f"检测到重复消息，跳过处理: 相似度={similarity_score:.3f}")
                    
                    # 记录去重统计信息
                    stats = self.deduplicator.get_stats()
                    logger.info(f"去重统计: 总消息={stats['total_messages']}, 重复={stats['duplicates_found']}, 缓存大小={stats['cache_size']}")
                    
                    # 发送去重通知
                    await self._send_duplicate_notification(message_data, similar_record, similarity_score)
                    return
                
                # 添加消息到去重缓存
                await self.deduplicator.add_message(message_data)
            
            # 使用Agent处理消息
            analysis_result = await self.agent_manager.process_message(message_data)
            
            logger.info(f"Agent处理完成，生成 {len(analysis_result['analysis_results'])} 个结果")
            
            # 输出分析结果
            for result in analysis_result['analysis_results']:
                result_json = json.dumps(result, ensure_ascii=False, separators=(',', ':'))
                print(f"[{datetime.now().isoformat()}] {result_json}")
            
            # 发送通知消息到 messages.notification subject
            await self._send_notification(message_data, analysis_result)
                
        except Exception as e:
            logger.error(f"处理消息失败: {e}", exc_info=True)
    
    async def _send_duplicate_notification(self, message_data: Dict[str, Any], similar_record, similarity_score: float):
        """发送重复消息通知"""
        try:
            nats_config = self.config.get_nats_config()
            notification_subject = nats_config.get('notification_subject', 'messages.notification')
            
            # 确保similarity_score是Python原生float类型，避免numpy类型序列化问题
            similarity_score_float = float(similarity_score) if similarity_score is not None else 0.0
            
            # 构建重复消息通知
            notification_message = {
                'type': 'messages.duplicate',
                'timestamp': int(time.time() * 1000),
                'source': 'analyze_agent',
                'sender': 'deduplication_agent',
                'data': {
                    'message': message_data,
                    'duplicate_info': {
                        'is_duplicate': True,
                        'similarity_score': similarity_score_float,
                        'original_message_id': similar_record.message_id if similar_record else None,
                        'original_timestamp': float(similar_record.timestamp) if similar_record else None,
                        'detection_time': datetime.now().isoformat()
                    },
                    'stats': self._sanitize_stats(self.deduplicator.get_stats() if self.deduplicator else {})
                }
            }
            
            # 发送到NATS
            notification_json = json.dumps(notification_message, ensure_ascii=False, separators=(',', ':'))
            await self.nats_client.publish(notification_subject, notification_json.encode())
            
            logger.debug(f"重复消息通知已发送到 {notification_subject}")
            
        except Exception as e:
            logger.error(f"发送重复消息通知失败: {e}")
    
    def _sanitize_stats(self, stats: Dict[str, Any]) -> Dict[str, Any]:
        """清理统计数据中的numpy类型，确保JSON序列化兼容"""
        import numpy as np
        
        sanitized = {}
        for key, value in stats.items():
            if isinstance(value, (np.integer, np.floating)):
                sanitized[key] = value.item()  # 转换为Python原生类型
            elif isinstance(value, np.ndarray):
                sanitized[key] = value.tolist()  # 转换为Python列表
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_stats(value)  # 递归处理嵌套字典
            elif isinstance(value, list):
                sanitized[key] = [self._sanitize_value(item) for item in value]
            else:
                sanitized[key] = value
        return sanitized
    
    def _sanitize_value(self, value):
        """清理单个值中的numpy类型"""
        import numpy as np
        
        if isinstance(value, (np.integer, np.floating)):
            return value.item()
        elif isinstance(value, np.ndarray):
            return value.tolist()
        elif isinstance(value, dict):
            return self._sanitize_stats(value)
        elif isinstance(value, list):
            return [self._sanitize_value(item) for item in value]
        else:
            return value
    
    async def _send_notification(self, original_message: Dict[str, Any], analysis_result: Dict[str, Any]):
        """发送通知消息到 messages.notification subject"""
        try:
            nats_config = self.config.get_nats_config()
            notification_subject = nats_config.get('notification_subject', 'messages.notification')
            
            # 添加去重统计信息到通知中
            notification_data = {
                'original_message': original_message,
                'analysis_results': analysis_result['analysis_results'],
                'summary': analysis_result['summary']
            }
            
            # 如果启用了去重，添加去重统计信息
            if self.deduplicator:
                notification_data['deduplication_stats'] = self._sanitize_stats(self.deduplicator.get_stats())
            
            # 构建通知消息
            notification_message = {
                'type': 'messages.notification',
                'timestamp': int(time.time() * 1000),
                'source': 'analyze_agent',
                'sender': 'analyze_agent',
                'data': notification_data
            }
            
            # 发送到NATS
            notification_json = json.dumps(notification_message, ensure_ascii=False, separators=(',', ':'))
            await self.nats_client.publish(notification_subject, notification_json.encode())
            
            logger.info(f"通知消息已发送到 {notification_subject}")
            logger.debug(f"通知消息内容: {notification_json[:200]}...")
            
        except Exception as e:
            logger.error(f"发送通知消息失败: {e}")

async def main():
    """主函数"""
    try:
        # 创建分析系统
        analyzer = AnalyzeAgent()
        
        # 初始化
        await analyzer.initialize()
        
        # 开始监控
        await analyzer.start_monitoring()
        
    except Exception as e:
        logger.error(f"系统启动失败: {e}")
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
