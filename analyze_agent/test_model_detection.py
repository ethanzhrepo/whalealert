#!/usr/bin/env python3
"""
模型检测功能测试脚本
"""

import asyncio
import logging
from deduplication import check_model_exists, ensure_model_available

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_model_detection():
    """测试模型检测功能"""
    print("开始测试模型检测功能...")
    
    # 测试用例
    test_cases = [
        {
            'name': 'BGE-M3模型（默认）',
            'model_name': 'BAAI/bge-m3',
            'description': '测试默认的BGE-M3模型'
        },
        {
            'name': '不存在的模型',
            'model_name': 'non-existent-model/test',
            'description': '测试不存在的模型处理'
        },
        {
            'name': '本地路径（不存在）',
            'model_name': './non-existent-local-model',
            'description': '测试不存在的本地路径'
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- 测试 {i}: {test_case['name']} ---")
        print(f"描述: {test_case['description']}")
        print(f"模型: {test_case['model_name']}")
        
        # 检查模型是否存在
        exists = check_model_exists(test_case['model_name'])
        print(f"模型存在: {'是' if exists else '否'}")
        
        # 如果是默认模型，测试确保可用功能
        if test_case['model_name'] == 'BAAI/bge-m3':
            print("测试模型确保可用功能...")
            try:
                available = await ensure_model_available(test_case['model_name'])
                print(f"模型可用: {'是' if available else '否'}")
                if available:
                    print("✓ BGE-M3模型测试通过")
                else:
                    print("✗ BGE-M3模型测试失败")
            except Exception as e:
                print(f"✗ 测试失败: {e}")
        else:
            print("跳过下载测试（非默认模型）")

async def test_config_integration():
    """测试配置集成"""
    print("\n开始测试配置集成...")
    
    # 模拟配置
    test_configs = [
        {
            'name': '默认配置',
            'config': {
                'enabled': True,
                'model_name': 'BAAI/bge-m3'
            }
        },
        {
            'name': '自定义模型',
            'config': {
                'enabled': True,
                'model_name': 'sentence-transformers/all-MiniLM-L6-v2'
            }
        },
        {
            'name': '禁用去重',
            'config': {
                'enabled': False,
                'model_name': 'BAAI/bge-m3'
            }
        }
    ]
    
    for i, test_config in enumerate(test_configs, 1):
        print(f"\n--- 配置测试 {i}: {test_config['name']} ---")
        config = test_config['config']
        
        if config.get('enabled', False):
            model_name = config.get('model_name', 'BAAI/bge-m3')
            print(f"检查模型: {model_name}")
            
            exists = check_model_exists(model_name)
            print(f"模型存在: {'是' if exists else '否'}")
            
            if not exists:
                print("模型不存在，需要下载")
            else:
                print("模型已存在，可直接使用")
        else:
            print("去重功能已禁用，跳过模型检查")

async def main():
    """主函数"""
    try:
        await test_model_detection()
        await test_config_integration()
        print("\n🎉 模型检测功能测试完成！")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main()) 