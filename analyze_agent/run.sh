#!/bin/bash

# Analyze Agent 运行脚本
# 用于启动分析系统

set -e  # 遇到错误时退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# 配置变量
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="$SCRIPT_DIR/config.yml"

# Python命令变量
PYTHON_CMD=""

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

log_step() {
    echo -e "${PURPLE}[STEP]${NC} $1"
}

# 检查命令是否存在
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# 检测Python命令
detect_python() {
    if command_exists python3; then
        PYTHON_CMD="python3"
    elif command_exists python; then
        # 检查是否为Python 3
        if python -c "import sys; exit(0 if sys.version_info[0] == 3 else 1)" 2>/dev/null; then
            PYTHON_CMD="python"
        else
            log_error "找到的python命令是Python 2，需要Python 3"
            exit 1
        fi
    else
        log_error "未找到Python，请先安装Python 3.8+"
        exit 1
    fi
}

# 检查配置文件
check_config() {
    log_step "检查配置文件..."
    
    if [ ! -f "$CONFIG_FILE" ]; then
        log_error "配置文件不存在: $CONFIG_FILE"
        log_info "请先运行: ./setup.sh"
        exit 1
    fi
    
    # 检查配置文件内容
    if ! $PYTHON_CMD -c "
import yaml
with open('$CONFIG_FILE', 'r') as f:
    config = yaml.safe_load(f)
    
# 检查必要配置
if not config.get('nats', {}).get('enabled'):
    print('ERROR: NATS未启用')
    exit(1)
    
if not config.get('nats', {}).get('subject'):
    print('ERROR: 未配置监控subject')
    exit(1)
    
if not config.get('agents', {}).get('sentiment_analysis', {}).get('enabled'):
    print('ERROR: 情绪分析Agent未启用')
    exit(1)
    
print('配置文件检查通过')
"; then
        log_error "配置文件检查失败"
        exit 1
    fi
    
    log_success "配置文件检查通过"
}

# 检查外部服务连接
check_external_services() {
    log_step "检查外部服务连接..."
    
    # 检查NATS连接
    NATS_SERVERS=$($PYTHON_CMD -c "
import yaml
with open('$CONFIG_FILE', 'r') as f:
    config = yaml.safe_load(f)
servers = config.get('nats', {}).get('servers', ['nats://localhost:4222'])
for server in servers:
    if server.startswith('nats://'):
        host_port = server[7:]  # 移除 'nats://' 前缀
        if ':' in host_port:
            host, port = host_port.split(':')
        else:
            host, port = host_port, '4222'
        print(f'{host}:{port}')
        break
")
    
    if [ -n "$NATS_SERVERS" ]; then
        HOST_PORT=$NATS_SERVERS
        if nc -z ${HOST_PORT/:/ } 2>/dev/null; then
            log_success "NATS服务器连接正常 ($HOST_PORT)"
        else
            log_warning "NATS服务器连接失败 ($HOST_PORT)"
            log_info "请确保NATS服务器已启动"
        fi
    fi
    
    # 检查LLM服务
    LLM_PROVIDER=$($PYTHON_CMD -c "
import yaml
with open('$CONFIG_FILE', 'r') as f:
    config = yaml.safe_load(f)
print(config.get('llm', {}).get('provider', 'ollama'))
")
    
    if [ "$LLM_PROVIDER" = "ollama" ]; then
        OLLAMA_URL=$($PYTHON_CMD -c "
import yaml
with open('$CONFIG_FILE', 'r') as f:
    config = yaml.safe_load(f)
base_url = config.get('llm', {}).get('ollama', {}).get('base_url', 'http://localhost:11434')
print(base_url.replace('http://', '').replace('https://', ''))
")
        
        if nc -z ${OLLAMA_URL/:/ } 2>/dev/null; then
            log_success "Ollama服务连接正常 ($OLLAMA_URL)"
        else
            log_warning "Ollama服务连接失败 ($OLLAMA_URL)"
            log_info "请确保Ollama服务已启动: ollama serve"
        fi
    else
        log_info "LLM提供商: $LLM_PROVIDER (跳过本地服务检查)"
    fi
}

# 运行预检测试
run_pre_check() {
    log_step "运行预检测试..."
    
    cd "$SCRIPT_DIR"
    
    if $PYTHON_CMD simple_test.py >/dev/null 2>&1; then
        log_success "预检测试通过"
    else
        log_error "预检测试失败"
        log_info "运行详细测试查看错误:"
        $PYTHON_CMD simple_test.py
        exit 1
    fi
}

# 启动分析系统
start_analyze_agent() {
    log_step "启动Analyze Agent..."
    
    cd "$SCRIPT_DIR"
    
    log_info "分析系统正在启动..."
    log_info "按 Ctrl+C 停止系统"
    echo ""
    
    # 启动主程序
    $PYTHON_CMD main.py
}

# 显示帮助信息
show_help() {
    echo "Analyze Agent 运行脚本"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -h, --help              显示帮助信息"
    echo "  -c, --check-only        只检查服务状态，不启动"
    echo "  --skip-service-check    跳过外部服务连接检查"
    echo ""
    echo "示例:"
    echo "  $0                      # 正常启动"
    echo "  $0 -c                   # 只检查服务状态"
    echo "  $0 --skip-service-check # 跳过服务检查直接启动"
    echo ""
    echo "注意:"
    echo "  本程序需要外部NATS服务器和LLM服务支持"
    echo "  请确保相关服务已启动并可访问"
    echo ""
}

# 解析命令行参数
CHECK_ONLY=false
SKIP_SERVICE_CHECK=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -c|--check-only)
            CHECK_ONLY=true
            shift
            ;;
        --skip-service-check)
            SKIP_SERVICE_CHECK=true
            shift
            ;;
        *)
            log_error "未知选项: $1"
            show_help
            exit 1
            ;;
    esac
done

# 主函数
main() {
    echo "========================================"
    echo "    Analyze Agent 运行脚本"
    echo "========================================"
    echo ""
    
    # 检测Python命令
    detect_python
    log_info "使用Python命令: $PYTHON_CMD"
    
    # 检查配置文件
    check_config
    
    # 检查外部服务连接
    if [ "$SKIP_SERVICE_CHECK" = "false" ]; then
        check_external_services
    else
        log_info "跳过外部服务检查"
    fi
    
    # 运行预检测试
    run_pre_check
    
    if [ "$CHECK_ONLY" = "true" ]; then
        log_success "所有检查完成，系统准备就绪"
        exit 0
    fi
    
    # 启动分析系统
    start_analyze_agent
}

# 设置信号处理
trap 'log_info "收到中断信号，正在停止..."; exit 0' INT TERM

# 运行主函数
main "$@" 