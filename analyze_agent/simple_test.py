#!/usr/bin/env python3
"""
简化测试 - 只测试配置加载
"""

import yaml
import json
from pathlib import Path

def test_config_loading():
    """测试配置文件加载"""
    print("=== 测试配置文件加载 ===")
    
    try:
        config_path = Path("config.yml")
        if not config_path.exists():
            print("❌ 配置文件不存在")
            return False
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        print("✅ 配置文件加载成功")
        print(f"NATS启用: {config.get('nats', {}).get('enabled', False)}")
        print(f"LLM提供商: {config.get('llm', {}).get('provider', 'unknown')}")
        print(f"监控subjects: {config.get('nats', {}).get('subject', [])}")
        
        # 检查必要的配置项
        if not config.get('nats', {}).get('enabled'):
            print("⚠️  NATS未启用")
        
        if not config.get('nats', {}).get('subject'):
            print("⚠️  未配置监控subject")
        
        if not config.get('agents', {}).get('sentiment_analysis', {}).get('enabled'):
            print("⚠️  情绪分析Agent未启用")
        
        return True
        
    except Exception as e:
        print(f"❌ 配置加载失败: {e}")
        return False

def test_message_format():
    """测试消息格式"""
    print("\n=== 测试消息格式 ===")
    
    # 模拟telegramstream发送的消息
    sample_message = {
        "type": "telegram.message",
        "timestamp": 1748142870135,
        "source": "telegram",
        "sender": "telegramstream",
        "data": {
            "message_id": 12345,
            "chat_id": -1001234567890,
            "chat_title": "Crypto Signals",
            "text": "🚀 BTC突破10万美元！牛市来了！",
            "extracted_data": {
                "raw_text": "BTC突破10万美元！牛市来了！",
                "symbols": ["BTC"],
                "sentiment": "positive"
            }
        }
    }
    
    print("样例输入消息:")
    print(json.dumps(sample_message, ensure_ascii=False, indent=2))
    
    # 模拟分析结果
    analysis_result = {
        "type": "analysis.sentiment",
        "timestamp": 1748142870135,
        "source": "analyze_agent",
        "sender": "sentiment_analysis_agent",
        "agent_name": "情绪分析Agent",
        "original_message_id": 12345,
        "data": {
            "sentiment": "利多",
            "reason": "消息提到BTC突破新高，市场情绪积极",
            "score": 0.8,
            "analysis_time": "2024-12-23T10:30:00.000Z"
        }
    }
    
    print("\n样例输出消息:")
    print(json.dumps(analysis_result, ensure_ascii=False, indent=2))
    
    return True

def test_raw_text_extraction():
    """测试raw_text提取"""
    print("\n=== 测试raw_text提取 ===")
    
    test_messages = [
        {
            "name": "标准消息",
            "data": {
                "text": "原始文本",
                "extracted_data": {
                    "raw_text": "处理后的文本"
                }
            }
        },
        {
            "name": "缺少extracted_data",
            "data": {
                "text": "只有原始文本"
            }
        },
        {
            "name": "空消息",
            "data": {}
        }
    ]
    
    for test_msg in test_messages:
        print(f"\n测试 {test_msg['name']}:")
        
        # 模拟提取逻辑
        try:
            raw_text = test_msg.get('data', {}).get('extracted_data', {}).get('raw_text', '')
            if not raw_text:
                raw_text = test_msg.get('data', {}).get('text', '')
            
            print(f"  提取结果: '{raw_text}'")
            
            if len(raw_text.strip()) < 10:
                print("  ⚠️  文本太短，会跳过分析")
            else:
                print("  ✅ 文本长度足够，可以进行分析")
                
        except Exception as e:
            print(f"  ❌ 提取失败: {e}")
    
    return True

def main():
    """主测试函数"""
    print("开始简化测试...\n")
    
    success_count = 0
    total_tests = 3
    
    if test_config_loading():
        success_count += 1
    
    if test_message_format():
        success_count += 1
    
    if test_raw_text_extraction():
        success_count += 1
    
    print(f"\n测试完成: {success_count}/{total_tests} 通过")
    
    if success_count == total_tests:
        print("✅ 所有基础测试通过！")
        print("\n下一步:")
        print("1. 安装LLM依赖: pip install langchain-ollama")
        print("2. 启动Ollama服务: ollama serve")
        print("3. 下载模型: ollama pull llama3.1:8b")
        print("4. 启动NATS服务器")
        print("5. 运行完整测试: python test_agent.py")
        return 0
    else:
        print("❌ 部分测试失败")
        return 1

if __name__ == '__main__':
    import sys
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as e:
        print(f"\n测试失败: {e}")
        sys.exit(1) 