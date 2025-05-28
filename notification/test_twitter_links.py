#!/usr/bin/env python3
"""
测试Twitter消息链接显示功能
"""

import json
import sys
from pathlib import Path

# 添加当前目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from main import MessageFormatter

def test_twitter_message_with_link():
    """测试包含链接的Twitter消息格式化"""
    print("🧪 测试Twitter消息链接显示...")
    
    # 模拟格式化配置
    format_config = {
        'include_score': True,
        'include_reason': True,
        'include_source': True,
        'include_author': True,
        'max_text_length': 500
    }
    
    formatter = MessageFormatter(format_config)
    
    # 模拟包含Twitter链接的通知数据
    notification_data = {
        'data': {
            'original_message': {
                'source': 'twitter',
                'data': {
                    'message_id': '1234567890',
                    'list_url': 'https://x.com/i/lists/123456789',
                    'username': 'testuser',
                    'text': 'BTC价格上涨！这是一个很好的买入机会 🚀',
                    'raw_text': 'BTC价格上涨！这是一个很好的买入机会 🚀',
                    'tweet_url': 'https://x.com/testuser/status/1234567890',
                    'extracted_data': {
                        'symbols': ['BTC'],
                        'sentiment': 'positive'
                    }
                }
            },
            'analysis_results': [
                {
                    'agent_type': 'sentiment_analysis',
                    'result': {
                        'sentiment': '利多',
                        'score': 0.8,
                        'reason': '提到价格上涨和买入机会，表现出积极的情绪'
                    }
                }
            ],
            'summary': {
                'total_agents': 1,
                'success_count': 1
            }
        }
    }
    
    # 格式化消息
    formatted_message = formatter.format_notification(notification_data)
    
    if formatted_message:
        print("✅ Twitter消息格式化成功")
        print("📝 格式化结果:")
        print(formatted_message)
        print()
        
        # 检查是否包含链接
        if '🔗' in formatted_message and 'https://x.com/testuser/status/1234567890' in formatted_message:
            print("✅ Twitter原文链接已正确包含")
        else:
            print("❌ Twitter原文链接缺失")
            return False
        
        # 检查链接格式
        if '<a href="https://x.com/testuser/status/1234567890">查看推文</a>' in formatted_message:
            print("✅ 链接格式正确")
        else:
            print("❌ 链接格式不正确")
            return False
        
        return True
    else:
        print("❌ Twitter消息格式化失败")
        return False

def test_twitter_message_without_link():
    """测试不包含链接的Twitter消息格式化"""
    print("🧪 测试无链接Twitter消息...")
    
    format_config = {
        'include_score': True,
        'include_reason': True,
        'include_source': True,
        'include_author': True,
        'max_text_length': 500
    }
    
    formatter = MessageFormatter(format_config)
    
    # 模拟不包含链接的Twitter消息
    notification_data = {
        'data': {
            'original_message': {
                'source': 'twitter',
                'data': {
                    'message_id': '1234567890',
                    'list_url': 'https://x.com/i/lists/123456789',
                    'username': 'testuser',
                    'text': 'ETH价格下跌了',
                    'raw_text': 'ETH价格下跌了',
                    # 注意：这里没有 tweet_url
                    'extracted_data': {
                        'symbols': ['ETH'],
                        'sentiment': 'negative'
                    }
                }
            },
            'analysis_results': [
                {
                    'agent_type': 'sentiment_analysis',
                    'result': {
                        'sentiment': '利空',
                        'score': -0.6,
                        'reason': '提到价格下跌，表现出消极情绪'
                    }
                }
            ]
        }
    }
    
    formatted_message = formatter.format_notification(notification_data)
    
    if formatted_message:
        print("✅ 无链接Twitter消息格式化成功")
        print("📝 格式化结果:")
        print(formatted_message)
        print()
        
        # 检查不应该包含链接
        if '🔗' not in formatted_message:
            print("✅ 正确处理无链接情况")
            return True
        else:
            print("❌ 不应该包含链接")
            return False
    else:
        print("❌ 无链接Twitter消息格式化失败")
        return False

def test_telegram_message():
    """测试Telegram消息格式化（应该不包含链接）"""
    print("🧪 测试Telegram消息...")
    
    format_config = {
        'include_score': True,
        'include_reason': True,
        'include_source': True,
        'include_author': True,
        'max_text_length': 500
    }
    
    formatter = MessageFormatter(format_config)
    
    # 模拟Telegram消息
    notification_data = {
        'data': {
            'original_message': {
                'source': 'telegram',
                'data': {
                    'message_id': 987654321,
                    'chat_title': '币圈讨论群',
                    'username': 'telegramuser',
                    'text': 'DOGE要moon了！',
                    'raw_text': 'DOGE要moon了！',
                    'extracted_data': {
                        'symbols': ['DOGE'],
                        'sentiment': 'positive'
                    }
                }
            },
            'analysis_results': [
                {
                    'agent_type': 'sentiment_analysis',
                    'result': {
                        'sentiment': '利多',
                        'score': 0.7,
                        'reason': '使用了"moon"等利多词汇'
                    }
                }
            ]
        }
    }
    
    formatted_message = formatter.format_notification(notification_data)
    
    if formatted_message:
        print("✅ Telegram消息格式化成功")
        print("📝 格式化结果:")
        print(formatted_message)
        print()
        
        # Telegram消息不应该有Twitter链接
        if '查看推文' not in formatted_message:
            print("✅ Telegram消息正确处理（无Twitter链接）")
            return True
        else:
            print("❌ Telegram消息不应该包含Twitter链接")
            return False
    else:
        print("❌ Telegram消息格式化失败")
        return False

def main():
    """主测试函数"""
    print("=" * 60)
    print("    Twitter链接显示功能测试")
    print("=" * 60)
    
    tests = [
        ("Twitter消息（有链接）", test_twitter_message_with_link),
        ("Twitter消息（无链接）", test_twitter_message_without_link),
        ("Telegram消息", test_telegram_message),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 40)
        
        try:
            result = test_func()
            if result:
                passed += 1
                print(f"✅ {test_name} 测试通过")
            else:
                print(f"❌ {test_name} 测试失败")
        except Exception as e:
            print(f"❌ {test_name} 测试异常: {e}")
    
    print("\n" + "=" * 60)
    print(f"测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！Twitter链接显示功能正常工作")
        print("\n📝 功能说明:")
        print("- Twitter消息会显示原文链接")
        print("- 链接格式: 🔗 查看推文")
        print("- 如果消息没有链接信息，则不显示链接")
        print("- Telegram消息不会显示Twitter链接")
        return True
    else:
        print("⚠️  部分测试失败，请检查代码")
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 测试过程中发生异常: {e}")
        sys.exit(1) 