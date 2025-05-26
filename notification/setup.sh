#!/bin/bash
#
# Notification Bot 安装脚本
#

set -e

echo "🚀 开始安装 Notification Bot..."

# 检查Python版本
python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "Python版本: $python_version"

# 使用Python自身来检查版本，更可靠
python3 -c "
import sys
if sys.version_info < (3, 8):
    print('❌ 错误: 需要Python 3.8或更高版本')
    print(f'   当前版本: {sys.version_info.major}.{sys.version_info.minor}')
    exit(1)
else:
    print(f'✅ Python版本检查通过: {sys.version_info.major}.{sys.version_info.minor}')
"

# 创建虚拟环境（可选）
if [ "$1" = "--venv" ]; then
    echo "📦 创建虚拟环境..."
    python3 -m venv venv
    source venv/bin/activate
    echo "✅ 虚拟环境已创建并激活"
fi

# 升级pip
echo "📦 升级pip..."
python3 -m pip install --upgrade pip

# 安装依赖
echo "📦 安装Python依赖..."
python3 -m pip install -r requirements.txt

# 检查配置文件
echo "🔧 检查配置文件..."
if [ ! -f "config.yml" ]; then
    echo "❌ 错误: config.yml 不存在"
    echo "请复制 config.yml.example 并修改配置"
    exit 1
fi

# 检查Bot Token
bot_token=$(python3 -c "import yaml; config=yaml.safe_load(open('config.yml')); print(config.get('telegram', {}).get('bot_token', ''))")
if [ "$bot_token" = "YOUR_BOT_TOKEN_HERE" ] || [ -z "$bot_token" ]; then
    echo "⚠️  警告: 请在 config.yml 中设置有效的 Telegram Bot Token"
    echo "   1. 联系 @BotFather 创建Bot"
    echo "   2. 获取Bot Token"
    echo "   3. 在 config.yml 中设置 telegram.bot_token"
fi

# 检查群组配置
echo "🔧 检查群组配置..."
enabled_groups=$(python3 -c "
import yaml
config = yaml.safe_load(open('config.yml'))
groups = config.get('telegram', {}).get('target_groups', [])
enabled = [g for g in groups if g.get('enabled', True)]
print(len(enabled))
")

if [ "$enabled_groups" -eq 0 ]; then
    echo "⚠️  警告: 没有配置启用的目标群组"
    echo "   请在 config.yml 中配置 telegram.target_groups"
fi

# 创建日志目录
echo "📁 创建日志目录..."
mkdir -p logs

# 设置执行权限
echo "🔧 设置执行权限..."
chmod +x run.sh
chmod +x main.py

echo ""
echo "✅ Notification Bot 安装完成！"
echo ""
echo "📋 下一步:"
echo "   1. 配置 Telegram Bot Token (如果还没有)"
echo "   2. 配置目标群组ID"
echo "   3. 运行: ./run.sh"
echo ""
echo "📖 更多信息请查看 README.md"
