#!/usr/bin/env python3
"""
简化的 DeepSeek 集成测试脚本
只测试基本的 LLM 功能，不依赖去重模块
"""

import asyncio
import sys
import yaml
from pathlib import Path

def test_deepseek_import():
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

def test_config_loading():
    """测试配置文件加载"""
    print("\n🧪 测试配置文件加载...")
    
    try:
        config_path = Path("config.yml")
        if not config_path.exists():
            print("⚠️  config.yml 文件不存在，跳过配置测试")
            return True
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        llm_config = config.get('llm', {})
        deepseek_config = llm_config.get('deepseek', {})
        
        print("✅ 配置文件加载成功")
        print(f"   LLM提供商: {llm_config.get('provider', 'unknown')}")
        print(f"   DeepSeek模型: {deepseek_config.get('model', 'unknown')}")
        print(f"   API密钥: {'已设置' if deepseek_config.get('api_key') and deepseek_config.get('api_key') != 'your-deepseek-api-key' else '未设置'}")
        
        return True
    except Exception as e:
        print(f"❌ 配置文件加载失败: {e}")
        return False

def test_deepseek_initialization():
    """测试DeepSeek初始化"""
    print("\n🧪 测试DeepSeek初始化...")
    
    try:
        from langchain_deepseek import ChatDeepSeek
        
        # 使用测试配置
        test_config = {
            'api_key': 'test-api-key',
            'model': 'deepseek-chat',
            'temperature': 0.1,
            'max_tokens': 1000,
            'timeout': 30
        }
        
        llm = ChatDeepSeek(**test_config)
        print("✅ DeepSeek LLM初始化成功")
        print(f"   模型: {test_config['model']}")
        print(f"   温度: {test_config['temperature']}")
        
        return True
    except Exception as e:
        print(f"❌ DeepSeek LLM初始化失败: {e}")
        return False

async def test_deepseek_api_call():
    """测试DeepSeek API调用（如果配置了真实API密钥）"""
    print("\n🧪 测试DeepSeek API调用...")
    
    try:
        # 尝试从配置文件读取API密钥
        config_path = Path("config.yml")
        if not config_path.exists():
            print("⚠️  config.yml 文件不存在，跳过API调用测试")
            return True
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        llm_config = config.get('llm', {})
        deepseek_config = llm_config.get('deepseek', {})
        api_key = deepseek_config.get('api_key')
        
        if not api_key or api_key == 'your-deepseek-api-key':
            print("⚠️  未在config.yml中设置有效的DeepSeek API密钥，跳过API调用测试")
            print("   如需测试API调用，请在config.yml中设置:")
            print("   llm:")
            print("     deepseek:")
            print("       api_key: 'sk-your-actual-api-key'")
            return True
        
        from langchain_deepseek import ChatDeepSeek
        from langchain.schema import HumanMessage
        
        llm = ChatDeepSeek(
            api_key=api_key,
            model=deepseek_config.get('model', 'deepseek-chat'),
            temperature=0.1,
            max_tokens=100,
            timeout=30
        )
        
        # 测试简单的API调用
        test_prompt = "请用一句话介绍DeepSeek。"
        print(f"   测试提示: {test_prompt}")
        
        messages = [HumanMessage(content=test_prompt)]
        response = await llm.ainvoke(messages)
        
        print(f"✅ DeepSeek API调用成功")
        print(f"   响应: {response.content[:100]}{'...' if len(response.content) > 100 else ''}")
        return True
        
    except Exception as e:
        print(f"❌ DeepSeek API调用失败: {e}")
        print("   请检查config.yml中的API密钥是否正确，或网络连接是否正常")
        return False

async def main():
    """主测试函数"""
    print("=" * 50)
    print("    DeepSeek 简化集成测试")
    print("=" * 50)
    
    tests = [
        ("导入测试", test_deepseek_import),
        ("配置加载测试", test_config_loading),
        ("初始化测试", test_deepseek_initialization),
        ("API调用测试", test_deepseek_api_call),
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
        print("\n📝 使用说明:")
        print("1. 确保在 config.yml 中设置了正确的 DeepSeek API 密钥")
        print("2. 将 llm.provider 设置为 'deepseek'")
        print("3. 运行 python main.py 启动分析系统")
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