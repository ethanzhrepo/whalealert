#!/bin/bash
# Notification Bot 启动脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 显示帮助信息
show_help() {
    echo "Notification Bot 启动脚本"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  --help              显示此帮助信息"
    echo "  --check-config      检查配置文件"
    echo "  --test-bot          测试Bot连接"
    echo "  --check-deps        检查依赖"
    echo "  --debug             启用调试模式"
    echo ""
    echo "示例:"
    echo "  $0                  正常启动"
    echo "  $0 --debug          调试模式启动"
    echo "  $0 --check-config   检查配置"
}

# 检查依赖
check_dependencies() {
    echo -e "${BLUE}🔍 检查依赖...${NC}"
    
    # 检查Python
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}❌ Python3 未安装${NC}"
        exit 1
    fi
    
    # 检查必需的Python包
    python3 -c "
import sys
required_packages = ['yaml', 'nats', 'telegram']
missing_packages = []

for package in required_packages:
    try:
        __import__(package)
    except ImportError:
        missing_packages.append(package)

if missing_packages:
    print(f'❌ 缺少Python包: {missing_packages}')
    print('请运行: pip install -r requirements.txt')
    sys.exit(1)
else:
    print('✅ 所有依赖已安装')
"
}

# 检查配置文件
check_config() {
    echo -e "${BLUE}🔧 检查配置文件...${NC}"
    
    if [ ! -f "config.yml" ]; then
        echo -e "${RED}❌ 配置文件 config.yml 不存在${NC}"
        exit 1
    fi
    
    # 使用Python检查配置
    python3 -c "
import yaml
import sys

try:
    with open('config.yml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # 检查NATS配置
    nats_config = config.get('nats', {})
    if not nats_config.get('enabled'):
        print('⚠️  NATS未启用')
    
    # 检查Telegram配置
    telegram_config = config.get('telegram', {})
    bot_token = telegram_config.get('bot_token', '')
    
    if not bot_token or bot_token == 'YOUR_BOT_TOKEN_HERE':
        print('❌ 请设置有效的Telegram Bot Token')
        sys.exit(1)
    
    # 检查目标群组
    target_groups = telegram_config.get('target_groups', [])
    enabled_groups = [g for g in target_groups if g.get('enabled', True)]
    
    if not enabled_groups:
        print('❌ 没有配置启用的目标群组')
        sys.exit(1)
    
    print(f'✅ 配置检查通过')
    print(f'   - Bot Token: 已设置')
    print(f'   - 目标群组: {len(enabled_groups)} 个')
    
except Exception as e:
    print(f'❌ 配置文件错误: {e}')
    sys.exit(1)
"
}

# 测试Bot连接
test_bot() {
    echo -e "${BLUE}🤖 测试Bot连接...${NC}"
    
    python3 -c "
import asyncio
import yaml
from telegram import Bot
from telegram.error import TelegramError

async def test_bot_connection():
    try:
        with open('config.yml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        bot_token = config.get('telegram', {}).get('bot_token', '')
        if not bot_token or bot_token == 'YOUR_BOT_TOKEN_HERE':
            print('❌ Bot Token未设置')
            return False
        
        bot = Bot(token=bot_token)
        me = await bot.get_me()
        
        print(f'✅ Bot连接成功')
        print(f'   - Bot名称: {me.first_name}')
        print(f'   - 用户名: @{me.username}')
        print(f'   - Bot ID: {me.id}')
        
        return True
        
    except TelegramError as e:
        print(f'❌ Bot连接失败: {e}')
        return False
    except Exception as e:
        print(f'❌ 测试失败: {e}')
        return False

if not asyncio.run(test_bot_connection()):
    exit(1)
"
}

# 检查NATS连接
check_nats() {
    echo -e "${BLUE}📡 检查NATS连接...${NC}"
    
    python3 -c "
import asyncio
import yaml
import nats

async def test_nats_connection():
    try:
        with open('config.yml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        nats_config = config.get('nats', {})
        servers = nats_config.get('servers', ['nats://localhost:4222'])
        
        nc = await nats.connect(servers=servers)
        await nc.close()
        
        print(f'✅ NATS连接成功')
        print(f'   - 服务器: {servers}')
        
        return True
        
    except Exception as e:
        print(f'❌ NATS连接失败: {e}')
        print('   请确保NATS服务器正在运行')
        return False

if not asyncio.run(test_nats_connection()):
    exit(1)
"
}

# 主函数
main() {
    local debug_mode=false
    
    # 解析命令行参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            --help)
                show_help
                exit 0
                ;;
            --check-config)
                check_config
                exit 0
                ;;
            --test-bot)
                test_bot
                exit 0
                ;;
            --check-deps)
                check_dependencies
                exit 0
                ;;
            --debug)
                debug_mode=true
                shift
                ;;
            *)
                echo -e "${RED}未知选项: $1${NC}"
                show_help
                exit 1
                ;;
        esac
    done
    
    echo -e "${GREEN}🤖 启动 Notification Bot...${NC}"
    echo ""
    
    # 检查依赖
    check_dependencies
    
    # 检查配置
    check_config
    
    # 检查NATS连接
    check_nats
    
    # 测试Bot连接
    test_bot
    
    echo ""
    echo -e "${GREEN}✅ 所有检查通过，启动程序...${NC}"
    echo ""
    
    # 设置环境变量
    if [ "$debug_mode" = true ]; then
        export PYTHONPATH="${PYTHONPATH}:."
        export LOG_LEVEL="DEBUG"
        echo -e "${YELLOW}🐛 调试模式已启用${NC}"
    fi
    
    # 启动程序
    if [ "$debug_mode" = true ]; then
        python3 -u main.py
    else
        python3 main.py
    fi
}

# 运行主函数
main "$@"
