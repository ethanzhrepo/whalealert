#!/bin/bash

# WhaleBot 一键安装脚本
# 用于安装整个项目的所有组件

set -e  # 遇到错误时退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 显示帮助信息
show_help() {
    echo "WhaleBot 一键安装脚本"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  --help, -h          显示此帮助信息"
    echo "  --skip-nats         跳过NATS服务器安装检查"
    echo "  --skip-tests        跳过所有测试"
    echo "  --component <name>  只安装指定组件 (telegramstream|analyze_agent|notification)"
    echo ""
    echo "示例:"
    echo "  $0                           # 完整安装所有组件"
    echo "  $0 --skip-tests              # 安装但跳过测试"
    echo "  $0 --component analyze_agent # 只安装分析智能体"
    echo ""
}

# 检查NATS服务器
check_nats() {
    log_info "检查NATS服务器..."
    
    if command -v nats-server >/dev/null 2>&1; then
        log_success "NATS服务器已安装"
    elif docker ps >/dev/null 2>&1 && docker images | grep -q nats; then
        log_success "发现NATS Docker镜像"
    else
        log_warning "未发现NATS服务器"
        echo ""
        echo "请选择NATS安装方式："
        echo "1. 使用Docker (推荐)"
        echo "2. 本地安装"
        echo "3. 跳过 (手动安装)"
        read -p "请选择 [1-3]: " choice
        
        case $choice in
            1)
                log_info "启动NATS Docker容器..."
                docker run -d -p 4222:4222 --name whalebot-nats nats:latest
                log_success "NATS Docker容器已启动"
                ;;
            2)
                log_info "请访问 https://docs.nats.io/running-a-nats-service/introduction/installation"
                log_info "按任意键继续..."
                read -n 1
                ;;
            3)
                log_warning "跳过NATS安装，请确保手动安装并启动"
                ;;
            *)
                log_error "无效选择"
                exit 1
                ;;
        esac
    fi
}

# 安装TelegramStream
install_telegramstream() {
    log_info "安装TelegramStream组件..."
    
    cd telegramstream
    if [ -f "setup.sh" ]; then
        chmod +x setup.sh
        ./setup.sh
        log_success "TelegramStream安装完成"
    else
        log_error "未找到TelegramStream安装脚本"
        exit 1
    fi
    cd ..
}

# 安装Analyze Agent
install_analyze_agent() {
    log_info "安装Analyze Agent组件..."
    
    cd analyze_agent
    if [ -f "setup.sh" ]; then
        chmod +x setup.sh
        if [ "$SKIP_TESTS" = true ]; then
            ./setup.sh --skip-dedup-test
        else
            ./setup.sh
        fi
        log_success "Analyze Agent安装完成"
    else
        log_error "未找到Analyze Agent安装脚本"
        exit 1
    fi
    cd ..
}

# 安装Notification Bot
install_notification() {
    log_info "安装Notification Bot组件..."
    
    cd notification
    if [ -f "setup.sh" ]; then
        chmod +x setup.sh
        ./setup.sh
        log_success "Notification Bot安装完成"
    else
        log_error "未找到Notification Bot安装脚本"
        exit 1
    fi
    cd ..
}

# 创建配置文件
setup_configs() {
    log_info "设置配置文件..."
    
    # TelegramStream配置
    if [ ! -f "telegramstream/config.yml" ] && [ -f "telegramstream/config.yml.example" ]; then
        cp telegramstream/config.yml.example telegramstream/config.yml
        log_info "已创建TelegramStream配置文件"
    fi
    
    # Analyze Agent配置
    if [ ! -f "analyze_agent/config.yml" ] && [ -f "analyze_agent/config.yml.example" ]; then
        cp analyze_agent/config.yml.example analyze_agent/config.yml
        log_info "已创建Analyze Agent配置文件"
    fi
    
    # Notification配置
    if [ ! -f "notification/config.yml" ] && [ -f "notification/config.yml.example" ]; then
        cp notification/config.yml.example notification/config.yml
        log_info "已创建Notification配置文件"
    fi
    
    log_success "配置文件设置完成"
}

# 显示后续步骤
show_next_steps() {
    echo ""
    log_success "WhaleBot 安装完成！"
    echo ""
    echo "后续配置步骤："
    echo ""
    echo "1. 配置TelegramStream:"
    echo "   cd telegramstream"
    echo "   # 编辑 config.yml，填入Telegram API凭据"
    echo "   python main.py config  # 选择要监控的频道"
    echo ""
    echo "2. 配置Analyze Agent:"
    echo "   cd analyze_agent"
    echo "   # 编辑 config.yml，配置LLM提供商"
    echo "   # 如使用OpenAI: 设置api_key"
    echo "   # 如使用Ollama: 确保服务运行在localhost:11434"
    echo ""
    echo "3. 配置Notification Bot:"
    echo "   cd notification"
    echo "   # 编辑 config.yml，设置Bot token和目标群组"
    echo ""
    echo "启动服务："
    echo "1. 启动TelegramStream: cd telegramstream && python main.py start"
    echo "2. 启动Analyze Agent: cd analyze_agent && python main.py"
    echo "3. 启动Notification Bot: cd notification && ./run.sh"
    echo ""
    echo "详细文档："
    echo "- 项目总览: README.md (English) / README_cn.md (中文)"
    echo "- TelegramStream: telegramstream/README.md"
    echo "- Analyze Agent: analyze_agent/README.md"
    echo "- Notification Bot: notification/README.md"
    echo ""
}

# 主函数
main() {
    echo "========================================"
    echo "    WhaleBot 一键安装脚本"
    echo "========================================"
    echo ""
    
    # 解析命令行参数
    SKIP_NATS=false
    SKIP_TESTS=false
    COMPONENT=""
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --help|-h)
                show_help
                exit 0
                ;;
            --skip-nats)
                SKIP_NATS=true
                shift
                ;;
            --skip-tests)
                SKIP_TESTS=true
                shift
                ;;
            --component)
                COMPONENT="$2"
                shift 2
                ;;
            *)
                log_error "未知参数: $1"
                echo "使用 --help 查看帮助信息"
                exit 1
                ;;
        esac
    done
    
    # 检查NATS服务器
    if [ "$SKIP_NATS" = false ]; then
        check_nats
    fi
    
    # 根据组件参数决定安装内容
    if [ -n "$COMPONENT" ]; then
        case $COMPONENT in
            telegramstream)
                install_telegramstream
                ;;
            analyze_agent)
                install_analyze_agent
                ;;
            notification)
                install_notification
                ;;
            *)
                log_error "未知组件: $COMPONENT"
                log_info "可用组件: telegramstream, analyze_agent, notification"
                exit 1
                ;;
        esac
    else
        # 安装所有组件
        install_telegramstream
        install_analyze_agent
        install_notification
    fi
    
    # 设置配置文件
    setup_configs
    
    # 显示后续步骤
    show_next_steps
}

# 处理中断信号
trap 'log_error "安装被中断"; exit 1' INT TERM

# 运行主函数
main "$@" 