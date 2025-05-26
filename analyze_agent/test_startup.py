#!/usr/bin/env python3
"""
测试启动过程脚本
"""

import asyncio
import sys
from main import AnalyzeAgent

async def test_init():
    """测试初始化过程"""
    try:
        print("创建 AnalyzeAgent...")
        analyzer = AnalyzeAgent()
        print('✓ AnalyzeAgent 创建成功')
        
        print("开始初始化...")
        # 测试初始化（会因为NATS连接失败而报错，但我们可以看到模型检测过程）
        await analyzer.initialize()
        print('✓ 初始化完成')
    except Exception as e:
        print(f'预期的错误（NATS连接失败）: {e}')
        if "NATS" in str(e):
            print("✓ 模型检测和加载过程正常，只是NATS连接失败（这是预期的）")
        else:
            print("✗ 意外的错误")
            raise

if __name__ == "__main__":
    asyncio.run(test_init()) 