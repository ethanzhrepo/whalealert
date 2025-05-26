#!/usr/bin/env python3
"""
测试 symbol_util.py 的功能
"""

import asyncio
import sys
from symbol_util import find_crypto_symbols, get_symbol_cache_info

async def test_symbol_matching():
    """测试符号匹配功能"""
    print("=== 测试数字货币符号匹配 ===\n")
    
    # 测试用例
    test_cases = [
        "BTC is going to the moon! 🚀",
        "ETHEREUM looks bullish today",
        "Thinking about buying some Bitcoin and Solana",
        "DOGE pump incoming 💎👌",
        "Check out this new altcoin: PEPE",
        "USD price action on ETH/USDT",
        "Nothing interesting here",
        "Mixed signals: BTC down, ETH up, MATIC sideways"
    ]
    
    for i, text in enumerate(test_cases, 1):
        print(f"测试 {i}: {text}")
        
        try:
            matches = await find_crypto_symbols(text)
            if matches:
                print(f"  找到 {len(matches)} 个匹配:")
                for match in matches:
                    symbol = match.get('symbol', 'N/A')
                    name = match.get('name', 'N/A')
                    price = match.get('current_price', 'N/A')
                    rank = match.get('market_cap_rank', 'N/A')
                    print(f"    - {symbol.upper()} ({name}) - 价格: ${price} - 排名: #{rank}")
            else:
                print("  没有找到匹配的数字货币")
        except Exception as e:
            print(f"  错误: {e}")
        
        print()

async def test_cache_info():
    """测试缓存信息"""
    print("=== 测试缓存信息 ===\n")
    
    cache_info = get_symbol_cache_info()
    print(f"缓存的数字货币数量: {cache_info['cached_symbols_count']}")
    print(f"上次获取时间: {cache_info['last_fetch_time']}")
    print(f"距离下次刷新: {cache_info['time_until_next_refresh']:.0f} 秒")
    print(f"aiohttp 可用性: {cache_info['aiohttp_available']}")

async def main():
    """主测试函数"""
    print("开始测试 symbol_util.py 功能...\n")
    
    # 测试缓存信息
    await test_cache_info()
    print()
    
    # 测试符号匹配
    await test_symbol_matching()
    
    # 再次检查缓存信息
    print("=== 测试后的缓存信息 ===\n")
    await test_cache_info()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n测试被用户中断")
    except Exception as e:
        print(f"\n测试失败: {e}")
        sys.exit(1) 