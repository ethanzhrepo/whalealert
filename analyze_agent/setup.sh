#!/bin/bash

# Analyze Agent 安装脚本
# 用于安装程序依赖

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

# 检查命令是否存在
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# 检测Python命令
detect_python() {
    if command_exists python3; then
        PYTHON_CMD="python3"
        PIP_CMD="pip3"
    elif command_exists python; then
        # 检查是否为Python 3
        if python -c "import sys; exit(0 if sys.version_info[0] == 3 else 1)" 2>/dev/null; then
            PYTHON_CMD="python"
            PIP_CMD="pip"
        else
            log_error "找到的python命令是Python 2，需要Python 3"
            exit 1
        fi
    else
        log_error "未找到Python，请先安装Python 3.8+"
        exit 1
    fi
    
    # 检查pip
    if ! command_exists $PIP_CMD; then
        if command_exists pip; then
            PIP_CMD="pip"
        else
            log_error "未找到pip，请先安装pip"
            exit 1
        fi
    fi
}

# 检查Python版本
check_python() {
    log_info "检查Python版本..."
    
    detect_python
    
    PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | cut -d' ' -f2)
    log_success "Python版本: $PYTHON_VERSION (命令: $PYTHON_CMD)"
    
    # 检查是否为Python 3.8+
    if $PYTHON_CMD -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
        log_success "Python版本满足要求 (>= 3.8)"
    else
        log_error "Python版本过低，需要 >= 3.8"
        exit 1
    fi
}

# 安装Python依赖
install_python_deps() {
    log_info "安装Python依赖包..."
    
    log_info "使用 $PIP_CMD 安装依赖..."
    
    # 升级pip
    log_info "升级pip..."
    $PIP_CMD install --upgrade pip
    
    # 安装基础依赖
    log_info "安装基础依赖..."
    $PIP_CMD install pyyaml nats-py pydantic
    
    # 安装LangChain相关
    log_info "安装LangChain框架..."
    $PIP_CMD install langchain langchain-core
    
    # 安装LLM提供商支持
    log_info "安装LLM提供商支持..."
    $PIP_CMD install langchain-ollama langchain-openai langchain-anthropic
    
    # 安装其他依赖
    log_info "安装其他依赖..."
    $PIP_CMD install aiohttp regex
    
    # 安装消息去重功能依赖
    log_info "安装消息去重功能依赖..."
    $PIP_CMD install sentence-transformers>=2.2.0
    $PIP_CMD install faiss-cpu>=1.7.0
    $PIP_CMD install numpy>=1.21.0
    $PIP_CMD install transformers>=4.21.0
    
    # 检查并安装tf-keras（解决Keras 3兼容性问题）
    log_info "检查Keras兼容性..."
    if $PYTHON_CMD -c "
try:
    import keras
    if hasattr(keras, '__version__') and keras.__version__.startswith('3.'):
        print('检测到Keras 3，需要安装tf-keras以保证兼容性')
        exit(1)
    else:
        print('Keras版本兼容')
        exit(0)
except ImportError:
    print('未安装Keras，跳过检查')
    exit(0)
" 2>/dev/null; then
        log_info "Keras版本兼容"
    else
        log_warning "检测到Keras 3，安装tf-keras以保证兼容性..."
        $PIP_CMD install tf-keras
    fi
    
    # 验证去重功能依赖安装
    log_info "验证消息去重功能依赖..."
    if $PYTHON_CMD -c "
try:
    import sentence_transformers
    import faiss
    import numpy as np
    import transformers
    
    # 检查Keras兼容性
    try:
        import keras
        if hasattr(keras, '__version__') and keras.__version__.startswith('3.'):
            try:
                import tf_keras
                print('✓ 检测到Keras 3，tf-keras已安装以保证兼容性')
            except ImportError:
                print('✗ 检测到Keras 3但tf-keras未安装，可能会有兼容性问题')
                exit(1)
        else:
            print('✓ Keras版本兼容')
    except ImportError:
        print('✓ 未安装Keras，无兼容性问题')
    
    print('✓ 消息去重功能依赖安装成功')
    print(f'  sentence-transformers: {sentence_transformers.__version__}')
    print(f'  faiss: {faiss.__version__}')
    print(f'  numpy: {np.__version__}')
    print(f'  transformers: {transformers.__version__}')
except ImportError as e:
    print(f'✗ 消息去重功能依赖安装失败: {e}')
    exit(1)
" 2>/dev/null; then
        log_success "消息去重功能依赖验证通过"
    else
        log_warning "消息去重功能依赖验证失败，但不影响基础功能"
    fi
    
    log_success "Python依赖安装完成"
}

# 创建配置文件
setup_config() {
    log_info "设置配置文件..."
    
    if [ ! -f "config.yml" ]; then
        if [ -f "config.yml.example" ]; then
            cp config.yml.example config.yml
            log_success "已从示例创建配置文件 config.yml"
        else
            log_error "未找到配置文件示例"
            exit 1
        fi
    else
        log_info "配置文件已存在，跳过创建"
    fi
}

# 运行测试
run_tests() {
    log_info "运行基础测试..."
    
    if $PYTHON_CMD simple_test.py; then
        log_success "基础测试通过"
    else
        log_error "基础测试失败"
        exit 1
    fi
}

# 测试消息去重功能
test_deduplication() {
    log_info "测试消息去重功能..."
    
    if [ -f "test_deduplication.py" ]; then
        log_info "运行去重功能测试（这可能需要几分钟来下载模型）..."
        if $PYTHON_CMD test_deduplication.py; then
            log_success "消息去重功能测试通过"
        else
            log_warning "消息去重功能测试失败，但不影响基础功能"
            
            # 检查是否是Keras兼容性问题
            if $PYTHON_CMD -c "
try:
    import keras
    if hasattr(keras, '__version__') and keras.__version__.startswith('3.'):
        print('检测到Keras 3兼容性问题')
        exit(1)
except:
    pass
exit(0)
" 2>/dev/null; then
                :  # 不是Keras问题
            else
                log_warning "检测到可能的Keras 3兼容性问题"
                log_info "尝试运行修复脚本: python3 fix_keras_compatibility.py"
                log_info "或手动安装: pip install tf-keras"
            fi
        fi
    else
        log_warning "未找到去重功能测试文件，跳过测试"
    fi
}

# 测试模型检测功能
test_model_detection() {
    log_info "测试模型检测功能..."
    
    if [ -f "test_model_detection.py" ]; then
        log_info "运行模型检测测试..."
        if $PYTHON_CMD test_model_detection.py; then
            log_success "模型检测功能测试通过"
        else
            log_warning "模型检测功能测试失败"
            
            # 检查是否是Keras兼容性问题
            if $PYTHON_CMD -c "
try:
    import keras
    if hasattr(keras, '__version__') and keras.__version__.startswith('3.'):
        print('检测到Keras 3兼容性问题')
        exit(1)
except:
    pass
exit(0)
" 2>/dev/null; then
                :  # 不是Keras问题
            else
                log_warning "检测到可能的Keras 3兼容性问题"
                log_info "尝试运行修复脚本: python3 fix_keras_compatibility.py"
                log_info "或手动安装: pip install tf-keras"
            fi
        fi
    else
        log_warning "未找到模型检测测试文件，跳过测试"
    fi
}

# 显示后续步骤
show_next_steps() {
    echo ""
    log_success "Analyze Agent 安装完成！"
    echo ""
    echo "后续步骤："
    echo "1. 确保外部服务已启动:"
    echo "   - NATS服务器 (端口 4222)"
    echo "   - LLM服务 (如Ollama在端口 11434，或配置OpenAI/Anthropic API)"
    echo ""
    echo "2. 配置LLM提供商 (编辑 config.yml):"
    echo "   - 如果使用OpenAI: 设置 api_key"
    echo "   - 如果使用Anthropic: 设置 api_key"
    echo "   - 如果使用Ollama: 确保服务运行在 localhost:11434"
    echo ""
    echo "3. 配置消息去重功能 (可选，编辑 config.yml):"
    echo "   - deduplication.enabled: true/false (是否启用去重)"
    echo "   - deduplication.similarity_threshold: 0.85 (相似度阈值)"
    echo "   - deduplication.time_window_hours: 2 (时间窗口)"
    echo ""
    echo "4. 运行测试:"
    echo "   $PYTHON_CMD test_agent.py          # 基础功能测试"
    echo "   $PYTHON_CMD test_deduplication.py  # 消息去重功能测试"
    echo "   $PYTHON_CMD test_model_detection.py  # 模型检测功能测试"
    echo ""
    echo "5. 启动分析系统:"
    echo "   ./run.sh"
    echo "   或者: $PYTHON_CMD main.py"
    echo ""
    echo "注意: "
    echo "- 本程序需要外部NATS服务器和LLM服务支持"
    echo "- 消息去重功能首次运行时会下载BGE-M3模型(约1-2GB)"
    echo "- 详细配置说明请参考 DEDUPLICATION_GUIDE.md"
    echo ""
    echo "故障排除:"
    echo "- 如果遇到Keras 3兼容性问题，运行: $PYTHON_CMD fix_keras_compatibility.py"
    echo "- 或手动安装: pip install tf-keras"
    echo "- 详细故障排除请参考文档"
    echo ""
}

# 主函数
main() {
    echo "========================================"
    echo "    Analyze Agent 安装脚本"
    echo "========================================"
    echo ""
    
    # 解析命令行参数
    SKIP_DEDUP_TEST=false
    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-dedup-test)
                SKIP_DEDUP_TEST=true
                shift
                ;;
            --help|-h)
                echo "用法: $0 [选项]"
                echo ""
                echo "选项:"
                echo "  --skip-dedup-test    跳过消息去重功能测试"
                echo "  --help, -h          显示此帮助信息"
                echo ""
                exit 0
                ;;
            *)
                log_error "未知参数: $1"
                echo "使用 --help 查看帮助信息"
                exit 1
                ;;
        esac
    done
    
    # 检查Python
    check_python
    
    # 安装Python依赖
    install_python_deps
    
    # 设置配置文件
    setup_config
    
    # 运行测试
    run_tests
    
    # 测试消息去重功能
    if [ "$SKIP_DEDUP_TEST" = false ]; then
        test_deduplication
    else
        log_info "跳过消息去重功能测试"
    fi
    
    # 测试模型检测功能
    test_model_detection
    
    # 显示后续步骤
    show_next_steps
}

# 处理中断信号
trap 'log_error "安装被中断"; exit 1' INT TERM

# 运行主函数
main "$@" 