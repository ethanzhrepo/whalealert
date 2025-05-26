#!/usr/bin/env python3
"""
消息去重功能测试脚本
"""

import asyncio
import json
import time
from datetime import datetime
from deduplication import MessageDeduplicator

async def test_deduplication():
    """测试消息去重功能"""
    print("开始测试消息去重功能...")
    
    # 创建去重器（使用较小的配置用于测试）
    deduplicator = MessageDeduplicator(
        model_name="BAAI/bge-m3",
        similarity_threshold=0.85,
        time_window_hours=2,
        max_cache_size=100,
        cache_file="test_cache.pkl"
    )
    
    # 初始化
    await deduplicator.initialize()
    
    # 测试消息
    test_messages = [
        {
            "type": "telegram.message",
            "timestamp": int(time.time() * 1000),
            "source": "telegram",
            "data": {
                "message_id": "1001",
                "chat_id": "-1001234567890",
                "text": "Binance 将上线新币 DOGE/USDT Trading Pair",
                "extracted_data": {
                    "raw_text": "Binance 将上线新币 DOGE/USDT Trading Pair"
                }
            }
        },
        {
            "type": "telegram.message", 
            "timestamp": int(time.time() * 1000) + 1000,
            "source": "telegram",
            "data": {
                "message_id": "1002",
                "chat_id": "-1001234567890", 
                "text": "Binance announces new DOGE/USDT trading pair launch",
                "extracted_data": {
                    "raw_text": "Binance announces new DOGE/USDT trading pair launch"
                }
            }
        },
        {
            "type": "telegram.message",
            "timestamp": int(time.time() * 1000) + 2000,
            "source": "telegram", 
            "data": {
                "message_id": "1003",
                "chat_id": "-1001234567890",
                "text": "Bitcoin price reaches new all-time high",
                "extracted_data": {
                    "raw_text": "Bitcoin price reaches new all-time high"
                }
            }
        },
        {
            "type": "telegram.message",
            "timestamp": int(time.time() * 1000) + 3000,
            "source": "telegram",
            "data": {
                "message_id": "1004", 
                "chat_id": "-1001234567890",
                "text": "Binance 将上线新币 DOGE/USDT Trading Pair",  # 完全相同的消息
                "extracted_data": {
                    "raw_text": "Binance 将上线新币 DOGE/USDT Trading Pair"
                }
            }
        },
        {
            "type": "telegram.message",
            "timestamp": int(time.time() * 1000) + 4000,
            "source": "telegram",
            "data": {
                "message_id": "1005",
                "chat_id": "-1001234567890",
                "text": "币安即将推出 DOGE/USDT 交易对",  # 语义相似的消息
                "extracted_data": {
                    "raw_text": "币安即将推出 DOGE/USDT 交易对"
                }
            }
        }
    ]
    
    print(f"\n测试 {len(test_messages)} 条消息...")
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n--- 测试消息 {i} ---")
        print(f"文本: {message['data']['extracted_data']['raw_text']}")
        
        # 检查是否重复
        is_duplicate, similar_record, similarity_score = await deduplicator.check_duplicate(message)
        
        if is_duplicate:
            print(f"✓ 检测到重复消息!")
            print(f"  相似度: {similarity_score:.3f}")
            if similar_record:
                print(f"  原消息ID: {similar_record.message_id}")
                print(f"  原文本: {similar_record.text[:50]}...")
        else:
            print(f"✗ 消息不重复 (最高相似度: {similarity_score:.3f})")
            
            # 添加到缓存
            success = await deduplicator.add_message(message)
            if success:
                print(f"  已添加到缓存")
            else:
                print(f"  添加到缓存失败")
    
    # 显示统计信息
    print(f"\n--- 去重统计 ---")
    stats = deduplicator.get_stats()
    for key, value in stats.items():
        print(f"{key}: {value}")
    
    # 清理
    await deduplicator.cleanup()
    print(f"\n测试完成!")

async def test_similarity_threshold():
    """测试不同相似度阈值的效果"""
    print("\n开始测试相似度阈值...")
    
    # 测试消息对
    message1 = {
        "type": "telegram.message",
        "timestamp": int(time.time() * 1000),
        "source": "telegram",
        "data": {
            "message_id": "2001",
            "chat_id": "-1001234567890",
            "text": "Binance 将上线新币 DOGE/USDT Trading Pair",
            "extracted_data": {
                "raw_text": "Binance 将上线新币 DOGE/USDT Trading Pair"
            }
        }
    }
    
    message2 = {
        "type": "telegram.message", 
        "timestamp": int(time.time() * 1000) + 1000,
        "source": "telegram",
        "data": {
            "message_id": "2002",
            "chat_id": "-1001234567890",
            "text": "币安即将推出 DOGE/USDT 交易对",
            "extracted_data": {
                "raw_text": "币安即将推出 DOGE/USDT 交易对"
            }
        }
    }
    
    # 测试不同阈值
    thresholds = [0.7, 0.8, 0.85, 0.9, 0.95]
    
    for threshold in thresholds:
        print(f"\n--- 阈值: {threshold} ---")
        
        deduplicator = MessageDeduplicator(
            model_name="BAAI/bge-m3",
            similarity_threshold=threshold,
            time_window_hours=2,
            max_cache_size=100,
            cache_file=f"test_cache_{threshold}.pkl"
        )
        
        await deduplicator.initialize()
        
        # 添加第一条消息
        await deduplicator.add_message(message1)
        
        # 检查第二条消息
        is_duplicate, similar_record, similarity_score = await deduplicator.check_duplicate(message2)
        
        print(f"相似度: {similarity_score:.3f}")
        print(f"是否重复: {'是' if is_duplicate else '否'}")
        
        await deduplicator.cleanup()

async def main():
    """主函数"""
    try:
        await test_deduplication()
        await test_similarity_threshold()
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main()) 