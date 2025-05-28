#!/usr/bin/env python3
"""
DeepSeek集成测试脚本
测试DeepSeek LLM提供商的集成是否正常工作
"""

import asyncio
import os
import sys
from pathlib import Path

# 添加当前目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from main import LLMManager, Config

def test_deepseek_config():
    """测试DeepSeek配置"""
    print("🧪 测试DeepSeek配置...")
    
    # 模拟DeepSeek配置
    config = {
        'provider': 'deepseek',
        'deepseek': {
            'api_key': 'test-api-key',
            'model': 'deepseek-chat',
            'temperature': 0.1,
            'max_tokens': 1000,
            'timeout': 30
        }
    }
    
    try:
        llm_manager = LLMManager(config)
        print("✅ DeepSeek LLMManager初始化成功")
        print(f"   提供商: {llm_manager.provider}")
        print(f"   LLM类型: {type(llm_manager.llm).__name__}")
        return True
    except Exception as e:
        print(f"❌ DeepSeek LLMManager初始化失败: {e}")
        return False

async def test_deepseek_call():
    """测试DeepSeek API调用（需要在配置文件中设置API密钥）"""
    print("\n🧪 测试DeepSeek API调用...")
    
    # 尝试从配置文件读取API密钥
    try:
        config_obj = Config()
        llm_config = config_obj.get_llm_config()
        deepseek_config = llm_config.get('deepseek', {})
        api_key = deepseek_config.get('api_key')
        
        if not api_key or api_key == 'your-deepseek-api-key':
            print("⚠️  未在config.yml中设置有效的DeepSeek API密钥，跳过API调用测试")
            print("   如需测试API调用，请在config.yml中设置:")
            print("   llm:")
            print("     deepseek:")
            print("       api_key: 'your-actual-api-key'")
            return True
        
        config = {
            'provider': 'deepseek',
            'deepseek': {
                'api_key': api_key,
                'model': 'deepseek-chat',
                'temperature': 0.1,
                'max_tokens': 100,
                'timeout': 30
            }
        }
        
        llm_manager = LLMManager(config)
        
        # 测试简单的API调用
        test_prompt = "请用一句话介绍DeepSeek。"
        print(f"   测试提示: {test_prompt}")
        
        response = await llm_manager.generate_response(test_prompt)
        print(f"✅ DeepSeek API调用成功")
        print(f"   响应: {response[:100]}{'...' if len(response) > 100 else ''}")
        return True
        
    except Exception as e:
        print(f"❌ DeepSeek API调用失败: {e}")
        print("   请检查config.yml中的API密钥是否正确，或网络连接是否正常")
        return False

def test_deepseek_models():
    """测试不同的DeepSeek模型配置"""
    print("\n🧪 测试DeepSeek模型配置...")
    
    models = ['deepseek-chat', 'deepseek-reasoner']
    
    for model in models:
        config = {
            'provider': 'deepseek',
            'deepseek': {
                'api_key': 'test-api-key',
                'model': model,
                'temperature': 0.1,
                'max_tokens': 1000,
                'timeout': 30
            }
        }
        
        try:
            llm_manager = LLMManager(config)
            print(f"✅ 模型 {model} 配置成功")
        except Exception as e:
            print(f"❌ 模型 {model} 配置失败: {e}")
            return False
    
    return True

def test_import_deepseek():
    """测试DeepSeek包导入"""
    print("🧪 测试DeepSeek包导入...")
    
    try:
        from langchain_deepseek import ChatDeepSeek
        print("✅ langchain_deepseek导入成功")
        print(f"   ChatDeepSeek类: {ChatDeepSeek}")
        return True
    except ImportError as e:
        print(f"❌ langchain_deepseek导入失败: {e}")
        print("   请运行: pip install langchain-deepseek")
        return False

async def main():
    """主测试函数"""
    print("=" * 50)
    print("    DeepSeek集成测试")
    print("=" * 50)
    
    tests = [
        ("导入测试", test_import_deepseek),
        ("配置测试", test_deepseek_config),
        ("模型测试", test_deepseek_models),
        ("API调用测试", test_deepseek_call),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 30)
        
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            
            if result:
                passed += 1
                print(f"✅ {test_name} 通过")
            else:
                print(f"❌ {test_name} 失败")
                
        except Exception as e:
            print(f"❌ {test_name} 异常: {e}")
    
    print("\n" + "=" * 50)
    print(f"测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！DeepSeek集成正常工作")
        return True
    else:
        print("⚠️  部分测试失败，请检查配置和依赖")
        return False

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 测试过程中发生异常: {e}")
        sys.exit(1) 