#!/usr/bin/env python3
"""
Telegram 监控程序诊断工具
"""

import yaml
import asyncio
from pathlib import Path
from telethon import TelegramClient
from main import TelegramConfig

async def diagnose():
    """诊断配置和连接状态"""
    print("=== Telegram 监控程序诊断 ===\n")
    
    # 1. 检查配置文件
    config_file = Path("config.yml")
    if not config_file.exists():
        print("❌ config.yml 文件不存在")
        return
    
    print("✅ config.yml 文件存在")
    
    # 2. 读取配置
    try:
        config = TelegramConfig()
        telegram_config = config.get_telegram_config()
        monitoring_config = config.get_monitoring_config()
        
        print(f"✅ 配置文件读取成功")
        print(f"   API ID: {'设置' if telegram_config.get('api_id') else '未设置'}")
        print(f"   API Hash: {'设置' if telegram_config.get('api_hash') else '未设置'}")
        print(f"   手机号: {'设置' if telegram_config.get('phone') else '未设置'}")
        
        groups = monitoring_config.get('groups', [])
        channels = monitoring_config.get('channels', [])
        print(f"   监控群组: {len(groups)} 个")
        print(f"   监控频道: {len(channels)} 个")
        
        if groups:
            print("   群组列表:")
            for group in groups:
                print(f"     - {group['title']} (ID: {group['id']})")
        
        if channels:
            print("   频道列表:")
            for channel in channels:
                print(f"     - {channel['title']} (ID: {channel['id']})")
        
        # 检查 ID 格式
        print("\n=== ID 格式检查 ===")
        all_chats = groups + channels
        for chat in all_chats:
            chat_id = chat['id']
            if isinstance(chat_id, str):
                chat_id = int(chat_id)
            
            if chat_id < 0:
                if str(abs(chat_id)).startswith('100'):
                    print(f"✅ {chat['title']}: ID {chat_id} 格式正确 (带 -100 前缀)")
                else:
                    print(f"⚠️  {chat['title']}: ID {chat_id} 格式异常")
            else:
                print(f"ℹ️  {chat['title']}: ID {chat_id} 是正数格式")
        
    except Exception as e:
        print(f"❌ 配置文件读取失败: {e}")
        return
    
    # 3. 测试 Telegram 连接
    print("\n=== 测试 Telegram 连接 ===")
    
    if not all([telegram_config.get('api_id'), telegram_config.get('api_hash')]):
        print("❌ Telegram API 配置不完整")
        return
    
    try:
        client = TelegramClient(
            telegram_config.get('session', 'telegram_monitor'),
            int(telegram_config['api_id']),
            telegram_config['api_hash']
        )
        
        await client.start(phone=telegram_config.get('phone'))
        print("✅ Telegram 连接成功")
        
        # 4. 检查监控目标的可访问性
        print("\n=== 检查监控目标 ===")
        
        all_chats = groups + channels
        if not all_chats:
            print("⚠️  没有配置任何监控目标")
        else:
            accessible_count = 0
            for chat in all_chats:
                try:
                    entity = await client.get_entity(chat['id'])
                    print(f"✅ {chat['title']} - 可访问")
                    accessible_count += 1
                except Exception as e:
                    print(f"❌ {chat['title']} - 无法访问: {e}")
            
            print(f"\n可访问的聊天: {accessible_count}/{len(all_chats)}")
        
        await client.disconnect()
        
    except Exception as e:
        print(f"❌ Telegram 连接失败: {e}")
        return
    
    print("\n=== 诊断完成 ===")
    print("如果所有检查都通过，但仍然没有消息输出，请:")
    print("1. 确认监控的群组/频道有新消息")
    print("2. 检查是否有权限访问这些群组/频道")
    print("3. 尝试发送测试消息到监控的群组")

if __name__ == '__main__':
    asyncio.run(diagnose()) 