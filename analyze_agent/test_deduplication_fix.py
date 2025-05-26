#!/usr/bin/env python3
"""
测试消息去重功能修复
"""

import asyncio
import json
import logging
import time
import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from deduplication import MessageDeduplicator, get_deduplicator

# 设置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_basic_functionality():
    """测试基本功能"""
    print("\n=== 测试基本功能 ===")
    
    # 创建去重器
    deduplicator = MessageDeduplicator(
        model_name="BAAI/bge-m3",
        similarity_threshold=0.85,
        time_window_hours=2,
        max_cache_size=100,
        cache_file="test_cache_basic.pkl"
    )
    
    try:
        await deduplicator.initialize()
        print("✓ 去重器初始化成功")
        
        # 测试消息
        test_message = {
            "type": "telegram.message",
            "timestamp": int(time.time() * 1000),
            "source": "telegram",
            "data": {
                "message_id": "test_001",
                "chat_id": "-1001234567890",
                "text": "Bitcoin price is going up!",
                "extracted_data": {
                    "raw_text": "Bitcoin price is going up!"
                }
            }
        }
        
        # 第一次检查（应该不重复）
        is_duplicate, similar_record, similarity_score = await deduplicator.check_duplicate(test_message)
        print(f"第一次检查: 重复={is_duplicate}, 相似度={similarity_score:.3f}")
        
        # 添加消息
        success = await deduplicator.add_message(test_message)
        print(f"添加消息: 成功={success}")
        
        # 第二次检查（应该重复）
        is_duplicate, similar_record, similarity_score = await deduplicator.check_duplicate(test_message)
        print(f"第二次检查: 重复={is_duplicate}, 相似度={similarity_score:.3f}")
        
        # 显示统计信息
        stats = deduplicator.get_stats()
        print(f"统计信息: {stats}")
        
        await deduplicator.cleanup()
        print("✓ 基本功能测试完成")
        
    except Exception as e:
        print(f"✗ 基本功能测试失败: {e}")
        import traceback
        traceback.print_exc()

async def test_edge_cases():
    """测试边界情况"""
    print("\n=== 测试边界情况 ===")
    
    deduplicator = MessageDeduplicator(
        model_name="BAAI/bge-m3",
        similarity_threshold=0.85,
        time_window_hours=2,
        max_cache_size=100,
        cache_file="test_cache_edge.pkl"
    )
    
    try:
        await deduplicator.initialize()
        
        # 测试空文本
        empty_message = {
            "type": "telegram.message",
            "timestamp": int(time.time() * 1000),
            "source": "telegram",
            "data": {
                "message_id": "empty_001",
                "chat_id": "-1001234567890",
                "text": "",
                "extracted_data": {
                    "raw_text": ""
                }
            }
        }
        
        is_duplicate, _, _ = await deduplicator.check_duplicate(empty_message)
        print(f"空文本检查: 重复={is_duplicate}")
        
        # 测试短文本
        short_message = {
            "type": "telegram.message",
            "timestamp": int(time.time() * 1000),
            "source": "telegram",
            "data": {
                "message_id": "short_001",
                "chat_id": "-1001234567890",
                "text": "Hi",
                "extracted_data": {
                    "raw_text": "Hi"
                }
            }
        }
        
        is_duplicate, _, _ = await deduplicator.check_duplicate(short_message)
        print(f"短文本检查: 重复={is_duplicate}")
        
        # 测试缺失字段
        incomplete_message = {
            "type": "telegram.message",
            "timestamp": int(time.time() * 1000),
            "source": "telegram",
            "data": {
                "message_id": "incomplete_001"
                # 缺少text和extracted_data
            }
        }
        
        is_duplicate, _, _ = await deduplicator.check_duplicate(incomplete_message)
        print(f"不完整消息检查: 重复={is_duplicate}")
        
        await deduplicator.cleanup()
        print("✓ 边界情况测试完成")
        
    except Exception as e:
        print(f"✗ 边界情况测试失败: {e}")
        import traceback
        traceback.print_exc()

async def test_faiss_consistency():
    """测试FAISS索引一致性"""
    print("\n=== 测试FAISS索引一致性 ===")
    
    deduplicator = MessageDeduplicator(
        model_name="BAAI/bge-m3",
        similarity_threshold=0.85,
        time_window_hours=2,
        max_cache_size=10,  # 小缓存以触发清理
        cache_file="test_cache_faiss.pkl"
    )
    
    try:
        await deduplicator.initialize()
        
        # 添加多条消息
        messages = []
        for i in range(15):  # 超过max_cache_size
            message = {
                "type": "telegram.message",
                "timestamp": int(time.time() * 1000) + i * 1000,
                "source": "telegram",
                "data": {
                    "message_id": f"test_{i:03d}",
                    "chat_id": "-1001234567890",
                    "text": f"This is test message number {i} about cryptocurrency trading",
                    "extracted_data": {
                        "raw_text": f"This is test message number {i} about cryptocurrency trading"
                    }
                }
            }
            messages.append(message)
            
            # 添加消息
            success = await deduplicator.add_message(message)
            print(f"添加消息 {i}: 成功={success}")
            
            # 检查FAISS索引状态
            if deduplicator.faiss_index:
                print(f"  FAISS索引大小: {deduplicator.faiss_index.ntotal}")
                print(f"  消息记录数量: {len(deduplicator.message_records)}")
        
        # 测试搜索功能
        test_message = {
            "type": "telegram.message",
            "timestamp": int(time.time() * 1000) + 20000,
            "source": "telegram",
            "data": {
                "message_id": "search_test",
                "chat_id": "-1001234567890",
                "text": "This is test message number 5 about cryptocurrency trading",  # 应该与第5条相似
                "extracted_data": {
                    "raw_text": "This is test message number 5 about cryptocurrency trading"
                }
            }
        }
        
        is_duplicate, similar_record, similarity_score = await deduplicator.check_duplicate(test_message)
        print(f"相似性搜索: 重复={is_duplicate}, 相似度={similarity_score:.3f}")
        if similar_record:
            print(f"  相似消息ID: {similar_record.message_id}")
        
        await deduplicator.cleanup()
        print("✓ FAISS索引一致性测试完成")
        
    except Exception as e:
        print(f"✗ FAISS索引一致性测试失败: {e}")
        import traceback
        traceback.print_exc()

async def test_cache_persistence():
    """测试缓存持久化"""
    print("\n=== 测试缓存持久化 ===")
    
    cache_file = "test_cache_persistence.pkl"
    
    # 第一阶段：创建并保存缓存
    try:
        deduplicator1 = MessageDeduplicator(
            model_name="BAAI/bge-m3",
            similarity_threshold=0.85,
            time_window_hours=2,
            max_cache_size=100,
            cache_file=cache_file
        )
        
        await deduplicator1.initialize()
        
        # 添加一些消息
        for i in range(5):
            message = {
                "type": "telegram.message",
                "timestamp": int(time.time() * 1000) + i * 1000,
                "source": "telegram",
                "data": {
                    "message_id": f"persist_{i:03d}",
                    "chat_id": "-1001234567890",
                    "text": f"Persistent message {i} about blockchain technology",
                    "extracted_data": {
                        "raw_text": f"Persistent message {i} about blockchain technology"
                    }
                }
            }
            await deduplicator1.add_message(message)
        
        deduplicator1.save_cache_now()
        await deduplicator1.cleanup()
        print("✓ 第一阶段：缓存已保存")
        
    except Exception as e:
        print(f"✗ 第一阶段失败: {e}")
        return
    
    # 第二阶段：加载缓存并验证
    try:
        deduplicator2 = MessageDeduplicator(
            model_name="BAAI/bge-m3",
            similarity_threshold=0.85,
            time_window_hours=2,
            max_cache_size=100,
            cache_file=cache_file
        )
        
        await deduplicator2.initialize()
        
        print(f"加载的消息数量: {len(deduplicator2.message_records)}")
        print(f"FAISS索引大小: {deduplicator2.faiss_index.ntotal if deduplicator2.faiss_index else 0}")
        
        # 测试重复检测
        test_message = {
            "type": "telegram.message",
            "timestamp": int(time.time() * 1000) + 10000,
            "source": "telegram",
            "data": {
                "message_id": "persist_000",  # 相同ID
                "chat_id": "-1001234567890",
                "text": "Persistent message 0 about blockchain technology",
                "extracted_data": {
                    "raw_text": "Persistent message 0 about blockchain technology"
                }
            }
        }
        
        is_duplicate, similar_record, similarity_score = await deduplicator2.check_duplicate(test_message)
        print(f"重复检测: 重复={is_duplicate}, 相似度={similarity_score:.3f}")
        
        await deduplicator2.cleanup()
        print("✓ 第二阶段：缓存加载验证完成")
        
    except Exception as e:
        print(f"✗ 第二阶段失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 清理测试文件
    try:
        if os.path.exists(cache_file):
            os.remove(cache_file)
    except:
        pass

async def main():
    """主测试函数"""
    print("开始消息去重功能修复测试...")
    
    # 清理旧的测试缓存文件
    test_files = [
        "test_cache_basic.pkl",
        "test_cache_edge.pkl", 
        "test_cache_faiss.pkl",
        "test_cache_persistence.pkl"
    ]
    
    for file in test_files:
        try:
            if os.path.exists(file):
                os.remove(file)
        except:
            pass
    
    try:
        await test_basic_functionality()
        await test_edge_cases()
        await test_faiss_consistency()
        await test_cache_persistence()
        
        print("\n=== 测试总结 ===")
        print("✓ 所有测试完成")
        
    except Exception as e:
        print(f"\n✗ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
    
    # 清理测试文件
    for file in test_files:
        try:
            if os.path.exists(file):
                os.remove(file)
        except:
            pass

if __name__ == "__main__":
    asyncio.run(main()) 