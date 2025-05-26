#!/bin/bash

echo "=== Telegram 消息监控程序安装脚本 ==="
echo ""

# 检查 conda 是否安装
if ! command -v conda &> /dev/null; then
    echo "❌ 未找到 conda 命令"
    echo "请先安装 Anaconda 或 Miniconda"
    echo "下载地址: https://www.anaconda.com/products/distribution"
    exit 1
else
    echo "✅ conda 已安装"
fi

# 检查 Python 版本
python_version=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" = "$required_version" ]; then
    echo "✅ Python 版本检查通过: $python_version"
else
    echo "⚠️  当前 Python 版本: $python_version (将使用 conda 创建 Python 3.9 环境)"
fi

# 检查是否已存在 telegram 环境
if conda env list | grep -q "^telegram "; then
    echo "⚠️  conda 环境 'telegram' 已存在"
    read -p "是否删除现有环境并重新创建？(y/n): " recreate_env
    if [ "$recreate_env" = "y" ] || [ "$recreate_env" = "Y" ]; then
        echo "正在删除现有环境..."
        conda env remove -n telegram -y
    else
        echo "使用现有环境..."
        conda activate telegram
    fi
fi

# 创建 conda 环境
if ! conda env list | grep -q "^telegram "; then
    echo "正在创建 conda 环境 'telegram'..."
    conda create -n telegram python=3.9 -y
    if [ $? -eq 0 ]; then
        echo "✅ conda 环境 'telegram' 创建成功"
    else
        echo "❌ conda 环境创建失败"
        exit 1
    fi
fi

# 激活环境
echo "正在激活 conda 环境..."
source $(conda info --base)/etc/profile.d/conda.sh
conda activate telegram

if [ $? -eq 0 ]; then
    echo "✅ conda 环境 'telegram' 已激活"
else
    echo "❌ 环境激活失败"
    exit 1
fi

# 安装依赖
echo "正在安装 Python 依赖包..."
pip install -r requirements.txt

if [ $? -eq 0 ]; then
    echo "✅ 依赖包安装完成"
else
    echo "❌ 依赖包安装失败"
    exit 1
fi

# 配置文件设置
if [ ! -f "config.yml" ]; then
    echo ""
    echo "📝 配置 Telegram API"
    echo "请访问 https://my.telegram.org 获取 API 凭据"
    echo ""
    
    read -p "请输入您的 API ID: " api_id
    read -p "请输入您的 API Hash: " api_hash
    read -p "请输入您的手机号 (包含国家代码，如 +8613812345678): " phone
    
    # 创建配置文件
    cat > config.yml << EOF
telegram:
  api_id: '$api_id'
  api_hash: '$api_hash'
  phone: '$phone'
  session: 'telegram_monitor'

monitoring:
  groups: []
  channels: []

nats:
  enabled: false
  servers: 
    - 'nats://localhost:4222'
  subject: 'telegram.messages'

advanced:
  filters:
    min_message_length: 0
    ignore_bots: false
    keywords: []
  extraction:
    extract_urls: true
    extract_addresses: true
    extract_symbols: true
    sentiment_analysis: true
EOF
    
    echo "✅ 配置文件已创建"
else
    echo "⚠️  配置文件 config.yml 已存在，跳过创建"
fi

echo ""
echo "🎉 安装完成！"
echo ""
echo "下一步："
echo "1. 配置监控群组/频道: python main.py config"
echo "2. 启动监控: python main.py start"
echo ""
echo "注意：下次使用前请激活 conda 环境："
echo "conda activate telegram" 