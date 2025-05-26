#!/usr/bin/env python3
"""
消息去重和合并模块
使用语义向量进行中英文混合文本的近重复检测
"""

import asyncio
import json
import logging
import time
import hashlib
import os
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from pathlib import Path
import pickle

import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

@dataclass
class MessageRecord:
    """消息记录"""
    message_id: str
    chat_id: str
    text: str
    vector: np.ndarray
    timestamp: float
    original_message: Dict[str, Any]

class MessageDeduplicator:
    """消息去重器"""
    
    def __init__(self, 
                 model_name: str = "BAAI/bge-m3",
                 similarity_threshold: float = 0.85,
                 time_window_hours: int = 2,
                 max_cache_size: int = 10000,
                 cache_file: str = "message_cache.pkl"):
        """
        初始化去重器
        
        Args:
            model_name: 句向量模型名称
            similarity_threshold: 相似度阈值
            time_window_hours: 时间窗口（小时）
            max_cache_size: 最大缓存大小
            cache_file: 缓存文件路径
        """
        self.model_name = model_name
        self.similarity_threshold = similarity_threshold
        self.time_window_hours = time_window_hours
        self.max_cache_size = max_cache_size
        self.cache_file = cache_file
        
        # 消息记录
        self.message_records: List[MessageRecord] = []
        self.message_index_map: Dict[str, int] = {}  # message_id -> index
        
        # FAISS索引
        self.faiss_index = None
        self.vector_dimension = None
        
        # 模型
        self.model = None
        self.model_loading = False
        
        # 统计信息
        self.stats = {
            'total_messages': 0,
            'duplicates_found': 0,
            'cache_hits': 0,
            'cache_misses': 0
        }
        
        logger.info(f"初始化消息去重器: model={model_name}, threshold={similarity_threshold}, window={time_window_hours}h")
    
    async def initialize(self):
        """异步初始化"""
        await self._load_model()
        self._load_cache()
        logger.info("消息去重器初始化完成")
    
    async def _load_model(self):
        """异步加载模型"""
        if self.model is not None:
            return
        
        if self.model_loading:
            # 等待其他协程加载完成
            while self.model_loading:
                await asyncio.sleep(0.1)
            return
        
        self.model_loading = True
        try:
            logger.info(f"开始加载句向量模型: {self.model_name}")
            start_time = time.time()
            
            # 在线程池中加载模型以避免阻塞
            loop = asyncio.get_event_loop()
            self.model = await loop.run_in_executor(
                None, 
                lambda: SentenceTransformer(self.model_name)
            )
            
            # 获取向量维度
            test_vector = self.model.encode(["test"], normalize_embeddings=True)
            self.vector_dimension = test_vector.shape[1]
            
            # 初始化FAISS索引
            self.faiss_index = faiss.IndexFlatIP(self.vector_dimension)  # 内积索引（归一化后等价于余弦相似度）
            
            load_time = time.time() - start_time
            logger.info(f"模型加载完成: 维度={self.vector_dimension}, 耗时={load_time:.2f}s")
            
        except Exception as e:
            logger.error(f"模型加载失败: {e}")
            raise
        finally:
            self.model_loading = False
    
    def _load_cache(self):
        """加载缓存文件"""
        cache_path = Path(self.cache_file)
        if not cache_path.exists():
            logger.info("缓存文件不存在，从空缓存开始")
            return
        
        try:
            with open(cache_path, 'rb') as f:
                cache_data = pickle.load(f)
            
            self.message_records = cache_data.get('message_records', [])
            self.stats = cache_data.get('stats', self.stats)
            
            # 重建索引
            if self.message_records and self.faiss_index is not None:
                try:
                    vectors = np.array([record.vector for record in self.message_records])
                    self.faiss_index.add(vectors.astype(np.float32))
                    logger.debug(f"从缓存重建FAISS索引完成，包含 {len(self.message_records)} 个向量")
                    
                    # 重建映射
                    self.message_index_map = {
                        record.message_id: i for i, record in enumerate(self.message_records)
                    }
                except Exception as e:
                    logger.error(f"从缓存重建FAISS索引失败: {e}")
                    # 清空有问题的缓存数据
                    self.message_records = []
                    self.message_index_map = {}
                    if self.vector_dimension:
                        self.faiss_index = faiss.IndexFlatIP(self.vector_dimension)
            
            logger.info(f"缓存加载完成: {len(self.message_records)} 条记录")
            
        except Exception as e:
            logger.error(f"缓存加载失败: {e}")
            self.message_records = []
            self.stats = {
                'total_messages': 0,
                'duplicates_found': 0,
                'cache_hits': 0,
                'cache_misses': 0
            }
    
    def _save_cache(self):
        """保存缓存文件"""
        try:
            cache_data = {
                'message_records': self.message_records,
                'stats': self.stats
            }
            
            with open(self.cache_file, 'wb') as f:
                pickle.dump(cache_data, f)
            
            logger.debug(f"缓存已保存: {len(self.message_records)} 条记录")
            
        except Exception as e:
            logger.error(f"缓存保存失败: {e}")
    
    def _extract_text(self, message_data: Dict[str, Any]) -> str:
        """从消息数据中提取文本"""
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
            logger.warning(f"提取文本失败: {e}")
            # 最后的降级方案
            return message_data.get('data', {}).get('text', '')
    
    def _generate_message_id(self, message_data: Dict[str, Any]) -> str:
        """生成消息ID"""
        # 优先使用原始message_id
        original_id = message_data.get('data', {}).get('message_id')
        if original_id:
            return str(original_id)
        
        # 使用文本内容生成哈希ID
        text = self._extract_text(message_data)
        timestamp = message_data.get('timestamp', int(time.time() * 1000))
        content = f"{text}_{timestamp}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _cleanup_old_records(self):
        """清理过期记录"""
        current_time = time.time()
        cutoff_time = current_time - (self.time_window_hours * 3600)
        
        # 找出需要保留的记录
        valid_indices = []
        valid_records = []
        
        for i, record in enumerate(self.message_records):
            if record.timestamp >= cutoff_time:
                valid_indices.append(i)
                valid_records.append(record)
        
        if len(valid_records) < len(self.message_records):
            removed_count = len(self.message_records) - len(valid_records)
            logger.info(f"清理过期记录: 移除 {removed_count} 条，保留 {len(valid_records)} 条")
            
            # 更新记录列表
            self.message_records = valid_records
            
            # 重建FAISS索引
            if self.faiss_index is not None:
                self.faiss_index.reset()
                
                if valid_records:
                    try:
                        vectors = np.array([record.vector for record in valid_records])
                        self.faiss_index.add(vectors.astype(np.float32))
                        logger.debug(f"FAISS索引重建完成，包含 {len(valid_records)} 个向量")
                    except Exception as e:
                        logger.error(f"重建FAISS索引失败: {e}")
                        # 重新初始化空索引
                        if self.vector_dimension:
                            self.faiss_index = faiss.IndexFlatIP(self.vector_dimension)
                
                # 重建映射
                self.message_index_map = {
                    record.message_id: i for i, record in enumerate(valid_records)
                }
            else:
                self.message_index_map.clear()
    
    async def check_duplicate(self, message_data: Dict[str, Any]) -> Tuple[bool, Optional[MessageRecord], float]:
        """
        检查消息是否重复
        
        Returns:
            (is_duplicate, similar_record, similarity_score)
        """
        start_time = time.time()
        
        # 模型应该在初始化时已经加载，这里只做安全检查
        if self.model is None:
            logger.warning("模型未加载，尝试重新加载...")
            await self._load_model()
        
        # 提取文本
        text = self._extract_text(message_data)
        if not text or len(text.strip()) < 10:
            logger.debug("文本内容太短，跳过去重检查")
            return False, None, 0.0
        
        # 生成消息ID
        message_id = self._generate_message_id(message_data)
        chat_id = str(message_data.get('data', {}).get('chat_id', ''))
        
        # 清理过期记录
        self._cleanup_old_records()
        
        # 检查是否已存在相同ID的消息
        if message_id in self.message_index_map:
            existing_record = self.message_records[self.message_index_map[message_id]]
            logger.info(f"发现完全相同的消息: {message_id}")
            self.stats['cache_hits'] += 1
            return True, existing_record, 1.0
        
        # 生成向量
        try:
            vector = self.model.encode([text], normalize_embeddings=True)[0]
        except Exception as e:
            logger.error(f"向量化失败: {e}")
            return False, None, 0.0
        
        # 如果没有历史记录，直接返回不重复
        if not self.message_records:
            self.stats['cache_misses'] += 1
            processing_time = (time.time() - start_time) * 1000
            logger.debug(f"首条消息，无需去重检查，耗时: {processing_time:.1f}ms")
            return False, None, 0.0
        
        # 使用FAISS搜索最相似的向量
        try:
            # 检查FAISS索引状态
            if self.faiss_index is None:
                logger.error("FAISS索引未初始化")
                return False, None, 0.0
            
            # 检查索引中的向量数量
            if self.faiss_index.ntotal == 0:
                logger.debug("FAISS索引为空，无法进行相似度搜索")
                return False, None, 0.0
            
            # 检查向量维度
            if vector.shape[0] != self.vector_dimension:
                logger.error(f"向量维度不匹配: 期望{self.vector_dimension}, 实际{vector.shape[0]}")
                return False, None, 0.0
            
            k = min(10, len(self.message_records), self.faiss_index.ntotal)
            if k <= 0:
                logger.debug("没有可搜索的向量")
                return False, None, 0.0
            
            similarities, indices = self.faiss_index.search(
                vector.reshape(1, -1).astype(np.float32), 
                k=k
            )
            
            # 检查搜索结果
            if similarities.shape[0] == 0 or indices.shape[0] == 0:
                logger.debug("FAISS搜索返回空结果")
                return False, None, 0.0
            
            if similarities.shape[1] == 0 or indices.shape[1] == 0:
                logger.debug("FAISS搜索未找到任何相似向量")
                return False, None, 0.0
            
            max_similarity = 0.0
            most_similar_record = None
            
            for similarity, idx in zip(similarities[0], indices[0]):
                if idx == -1:  # FAISS返回-1表示无效索引
                    continue
                
                # 检查索引是否在有效范围内
                if idx >= len(self.message_records):
                    logger.warning(f"FAISS返回的索引超出范围: {idx} >= {len(self.message_records)}")
                    continue
                
                record = self.message_records[idx]
                
                # 检查时间窗口
                current_time = time.time()
                if current_time - record.timestamp > self.time_window_hours * 3600:
                    continue
                
                if similarity > max_similarity:
                    max_similarity = similarity
                    most_similar_record = record
            
            processing_time = (time.time() - start_time) * 1000
            
            # 判断是否重复
            is_duplicate = max_similarity >= self.similarity_threshold
            
            if is_duplicate:
                self.stats['duplicates_found'] += 1
                logger.info(f"发现重复消息: 相似度={max_similarity:.3f}, 原消息ID={most_similar_record.message_id}, 耗时: {processing_time:.1f}ms")
                logger.debug(f"原文本: {most_similar_record.text[:100]}...")
                logger.debug(f"新文本: {text[:100]}...")
            else:
                self.stats['cache_misses'] += 1
                logger.debug(f"消息不重复: 最高相似度={max_similarity:.3f}, 耗时: {processing_time:.1f}ms")
            
            return is_duplicate, most_similar_record, max_similarity
            
        except Exception as e:
            logger.error(f"相似度搜索失败: {e}")
            return False, None, 0.0
    
    async def add_message(self, message_data: Dict[str, Any]) -> bool:
        """
        添加消息到缓存
        
        Returns:
            是否成功添加
        """
        try:
            # 模型应该在初始化时已经加载，这里只做安全检查
            if self.model is None:
                logger.warning("模型未加载，尝试重新加载...")
                await self._load_model()
            
            # 提取信息
            text = self._extract_text(message_data)
            if not text or len(text.strip()) < 10:
                return False
            
            message_id = self._generate_message_id(message_data)
            chat_id = str(message_data.get('data', {}).get('chat_id', ''))
            
            # 检查是否已存在
            if message_id in self.message_index_map:
                logger.debug(f"消息已存在，跳过添加: {message_id}")
                return False
            
            # 生成向量
            vector = self.model.encode([text], normalize_embeddings=True)[0]
            
            # 创建记录
            record = MessageRecord(
                message_id=message_id,
                chat_id=chat_id,
                text=text,
                vector=vector,
                timestamp=time.time(),
                original_message=message_data
            )
            
            # 添加到缓存
            self.message_records.append(record)
            self.message_index_map[message_id] = len(self.message_records) - 1
            
            # 添加到FAISS索引
            if self.faiss_index is not None:
                try:
                    # 检查向量维度
                    if vector.shape[0] != self.vector_dimension:
                        logger.error(f"向量维度不匹配: 期望{self.vector_dimension}, 实际{vector.shape[0]}")
                        return False
                    
                    self.faiss_index.add(vector.reshape(1, -1).astype(np.float32))
                    logger.debug(f"向量已添加到FAISS索引，当前索引大小: {self.faiss_index.ntotal}")
                except Exception as e:
                    logger.error(f"添加向量到FAISS索引失败: {e}")
                    return False
            
            self.stats['total_messages'] += 1
            
            # 检查缓存大小限制
            if len(self.message_records) > self.max_cache_size:
                self._cleanup_old_records()
            
            # 定期保存缓存
            if self.stats['total_messages'] % 100 == 0:
                self._save_cache()
            
            logger.debug(f"消息已添加到缓存: {message_id}, 缓存大小: {len(self.message_records)}")
            return True
            
        except Exception as e:
            logger.error(f"添加消息失败: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        current_time = time.time()
        cutoff_time = current_time - (self.time_window_hours * 3600)
        
        # 计算时间窗口内的消息数量
        active_messages = sum(1 for record in self.message_records if record.timestamp >= cutoff_time)
        
        return {
            **self.stats,
            'cache_size': len(self.message_records),
            'active_messages_in_window': active_messages,
            'time_window_hours': self.time_window_hours,
            'similarity_threshold': self.similarity_threshold,
            'model_name': self.model_name,
            'vector_dimension': self.vector_dimension
        }
    
    def save_cache_now(self):
        """立即保存缓存"""
        self._save_cache()
    
    async def cleanup(self):
        """清理资源"""
        self._save_cache()
        logger.info("消息去重器已清理")

# 全局去重器实例
_global_deduplicator: Optional[MessageDeduplicator] = None

async def get_deduplicator(config: Dict[str, Any] = None) -> MessageDeduplicator:
    """获取全局去重器实例"""
    global _global_deduplicator
    
    if _global_deduplicator is None:
        # 默认配置
        default_config = {
            'model_name': 'BAAI/bge-m3',
            'similarity_threshold': 0.85,
            'time_window_hours': 2,
            'max_cache_size': 10000,
            'cache_file': 'message_cache.pkl'
        }
        
        if config:
            # 过滤掉不属于MessageDeduplicator构造函数的参数
            filtered_config = {k: v for k, v in config.items() 
                             if k in ['model_name', 'similarity_threshold', 'time_window_hours', 
                                    'max_cache_size', 'cache_file']}
            default_config.update(filtered_config)
        
        _global_deduplicator = MessageDeduplicator(**default_config)
        await _global_deduplicator.initialize()
    
    return _global_deduplicator

async def cleanup_deduplicator():
    """清理全局去重器"""
    global _global_deduplicator
    if _global_deduplicator:
        await _global_deduplicator.cleanup()
        _global_deduplicator = None

def check_model_exists(model_name: str) -> bool:
    """
    检查模型是否存在（本地路径或已缓存的HuggingFace模型）
    
    Args:
        model_name: 模型名称或路径
        
    Returns:
        bool: 模型是否存在
    """
    try:
        # 检查是否为本地路径
        if os.path.exists(model_name):
            # 检查是否为有效的模型目录
            model_path = Path(model_name)
            if model_path.is_dir():
                # 检查必要的模型文件
                required_files = ['config.json', 'pytorch_model.bin']
                has_required = any((model_path / f).exists() for f in required_files)
                if has_required:
                    logger.info(f"找到本地模型: {model_name}")
                    return True
        
        # 检查HuggingFace缓存
        try:
            from transformers import AutoConfig
            # 尝试加载配置，如果成功说明模型已缓存
            config = AutoConfig.from_pretrained(model_name, local_files_only=True)
            logger.info(f"找到缓存的HuggingFace模型: {model_name}")
            return True
        except Exception:
            # 模型未缓存
            pass
        
        logger.info(f"模型不存在或未缓存: {model_name}")
        return False
        
    except Exception as e:
        logger.warning(f"检查模型存在性时出错: {e}")
        return False

async def download_model(model_name: str) -> bool:
    """
    下载模型（如果不存在）
    
    Args:
        model_name: 模型名称
        
    Returns:
        bool: 下载是否成功
    """
    try:
        logger.info(f"开始下载模型: {model_name}")
        logger.info("这可能需要几分钟时间，请耐心等待...")
        
        # 在线程池中下载模型以避免阻塞
        loop = asyncio.get_event_loop()
        
        def _download_model():
            try:
                # 使用SentenceTransformer下载模型
                model = SentenceTransformer(model_name)
                return True
            except Exception as e:
                logger.error(f"模型下载失败: {e}")
                return False
        
        success = await loop.run_in_executor(None, _download_model)
        
        if success:
            logger.info(f"模型下载完成: {model_name}")
        else:
            logger.error(f"模型下载失败: {model_name}")
        
        return success
        
    except Exception as e:
        logger.error(f"下载模型时出错: {e}")
        return False

async def ensure_model_available(model_name: str) -> bool:
    """
    确保模型可用（检查存在性，如不存在则下载）
    
    Args:
        model_name: 模型名称或路径
        
    Returns:
        bool: 模型是否可用
    """
    try:
        # 首先检查模型是否存在
        if check_model_exists(model_name):
            return True
        
        # 判断是否为本地路径
        is_local_path = (
            os.path.isabs(model_name) or  # 绝对路径
            model_name.startswith('./') or  # 相对路径 ./
            model_name.startswith('../') or  # 相对路径 ../
            os.path.exists(model_name)  # 存在的路径
        )
        
        # 如果是本地路径但不存在，直接返回False
        if is_local_path:
            logger.error(f"本地模型路径不存在: {model_name}")
            return False
        
        # 尝试下载HuggingFace模型
        logger.info(f"模型不存在，尝试下载: {model_name}")
        return await download_model(model_name)
        
    except Exception as e:
        logger.error(f"确保模型可用时出错: {e}")
        return False 