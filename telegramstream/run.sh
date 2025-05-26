#!/bin/bash

# Telegram 监控程序启动脚本

# 检查 conda 是否安装
if ! command -v conda &> /dev/null; then
    echo "❌ 未找到 conda 命令，请先运行 ./setup.sh 安装环境"
    exit 1
fi

# 检查 telegram 环境是否存在
if ! conda env list | grep -q "^telegram "; then
    echo "❌ conda 环境 'telegram' 不存在"
    echo "请先运行 ./setup.sh 创建环境"
    exit 1
fi

# 激活环境
echo "激活 conda 环境 'telegram'..."
source $(conda info --base)/etc/profile.d/conda.sh
conda activate telegram

if [ $? -ne 0 ]; then
    echo "❌ 环境激活失败"
    exit 1
fi

# 检查参数
if [ $# -eq 0 ]; then
    echo "Telegram 消息监控程序"
    echo ""
    echo "用法:"
    echo "  ./run.sh config  - 配置监控的群组/频道"
    echo "  ./run.sh start   - 启动监控"
    echo "  ./run.sh help    - 显示帮助信息"
    echo ""
    echo "首次使用请运行: ./run.sh config"
    exit 0
fi

case "$1" in
    "config")
        echo "启动配置界面..."
        python main.py config
        ;;
    "start")
        echo "启动消息监控..."
        python main.py start
        ;;
    "help")
        echo "Telegram 消息监控程序"
        echo ""
        echo "功能："
        echo "  - 监控指定的 Telegram 群组和频道"
        echo "  - 自动提取消息中的区块链地址、代币符号、价格等信息"
        echo "  - 支持情感分析和关键词过滤"
        echo "  - 可将消息发送到 NATS 消息队列"
        echo ""
        echo "配置文件: config.yml"
        echo "消息格式: 查看 message.md"
        echo ""
        echo "使用步骤："
        echo "  1. ./run.sh config  # 选择要监控的群组/频道"
        echo "  2. ./run.sh start   # 启动监控"
        ;;
    *)
        echo "未知命令: $1"
        echo "使用 './run.sh help' 查看帮助"
        exit 1
        ;;
esac 