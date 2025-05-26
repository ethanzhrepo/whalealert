#!/usr/bin/env python3
"""
测试 Analyze Agent 功能
"""

import asyncio
import json
import sys
from main import Config, LLMManager, SentimentAnalysisAgent

async def test_config_loading():
    """测试配置加载"""
    print("=== 测试配置加载 ===")
    
    try:
        config = Config()
        print("✅ 配置文件加载成功")
        
        nats_config = config.get_nats_config()
        print(f"NATS配置: {nats_config}")
        
        llm_config = config.get_llm_config()
        print(f"LLM提供商: {llm_config.get('provider', 'unknown')}")
        
        agents_config = config.get_agents_config()
        print(f"启用的Agent: {list(agents_config.keys())}")
        
    except Exception as e:
        print(f"❌ 配置加载失败: {e}")
        return False
    
    return True

async def test_llm_connection():
    """测试LLM连接"""
    print("\n=== 测试LLM连接 ===")
    
    try:
        config = Config()
        llm_manager = LLMManager(config.get_llm_config())
        print(f"✅ LLM管理器初始化成功，提供商: {llm_manager.provider}")
        
        # 测试简单调用
        test_prompt = "请回答：1+1等于几？只需要回答数字。"
        response = await llm_manager.generate_response(test_prompt)
        print(f"LLM测试响应: {response[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ LLM连接失败: {e}")
        return False

async def test_sentiment_analysis():
    """测试情绪分析Agent"""
    print("\n=== 测试情绪分析Agent ===")
    
    try:
        config = Config()
        llm_manager = LLMManager(config.get_llm_config())
        agent = SentimentAnalysisAgent(llm_manager)
        
        # 测试消息
        test_messages = [
            {
                "name": "利多消息",
                "data": {
                    "message_id": 12345,
                    "chat_id": -1001234567890,
                    "text": "BTC突破新高！市场情绪高涨，预计将继续上涨！",
                    "extracted_data": {
                        "raw_text": "BTC突破新高！市场情绪高涨，预计将继续上涨！"
                    }
                }
            },
            {
                "name": "利空消息",
                "data": {
                    "message_id": 12346,
                    "chat_id": -1001234567890,
                    "text": "加密货币市场崩盘，投资者恐慌抛售，BTC暴跌20%",
                    "extracted_data": {
                        "raw_text": "加密货币市场崩盘，投资者恐慌抛售，BTC暴跌20%"
                    }
                }
            },
            {
                "name": "中性消息",
                "data": {
                    "message_id": 12347,
                    "chat_id": -1001234567890,
                    "text": "今日BTC价格在支撑位附近震荡，成交量平稳",
                    "extracted_data": {
                        "raw_text": "今日BTC价格在支撑位附近震荡，成交量平稳"
                    }
                }
            }
        ]
        
        for test_msg in test_messages:
            print(f"\n测试 {test_msg['name']}:")
            print(f"原文: {test_msg['data']['text']}")
            
            result = await agent.process(test_msg)
            
            if result:
                sentiment = result.get('data', {}).get('sentiment', '未知')
                reason = result.get('data', {}).get('reason', '无理由')
                score = result.get('data', {}).get('score', 0.0)
                
                print(f"  情绪: {sentiment}")
                print(f"  理由: {reason}")
                print(f"  评分: {score}")
                print(f"  结果类型: {result.get('type', 'unknown')}")
            else:
                print("  ❌ 分析失败")
        
        return True
        
    except Exception as e:
        print(f"❌ 情绪分析测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_message_format():
    """测试消息格式"""
    print("\n=== 测试消息格式 ===")
    
    # 模拟telegramstream发送的消息格式
    sample_message = {
        "type": "telegram.message",
        "timestamp": 1748142870135,
        "source": "telegram",
        "sender": "telegramstream",
        "data": {
            "message_id": 12345,
            "chat_id": -1001234567890,
            "chat_title": "Crypto Signals",
            "chat_type": "channel",
            "user_id": 123456789,
            "username": "crypto_trader",
            "text": "🚀 BTC突破10万美元！牛市来了！",
            "extracted_data": {
                "raw_text": "BTC突破10万美元！牛市来了！",
                "symbols": ["BTC"],
                "crypto_currencies": [
                    {
                        "id": "bitcoin",
                        "symbol": "btc",
                        "name": "Bitcoin",
                        "current_price": 100000
                    }
                ],
                "sentiment": "positive"
            }
        }
    }
    
    print("样例消息格式:")
    print(json.dumps(sample_message, ensure_ascii=False, indent=2))
    
    return True

async def main():
    """主测试函数"""
    print("开始测试 Analyze Agent 功能...\n")
    
    # 测试配置加载
    if not await test_config_loading():
        print("❌ 配置测试失败，停止后续测试")
        return 1
    
    # 测试消息格式
    await test_message_format()
    
    # 测试LLM连接
    if not await test_llm_connection():
        print("❌ LLM连接测试失败，跳过情绪分析测试")
        return 1
    
    # 测试情绪分析
    if not await test_sentiment_analysis():
        print("❌ 情绪分析测试失败")
        return 1
    
    print("\n✅ 所有测试通过！")
    return 0

if __name__ == '__main__':
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n测试被用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"\n测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1) 