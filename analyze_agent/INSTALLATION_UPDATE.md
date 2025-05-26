# 安装脚本更新说明

## 更新内容

消息去重功能的依赖安装已经合并到主安装脚本 `setup.sh` 中，不再需要单独的安装脚本。

## 新的安装方式

### 完整安装（推荐）

```bash
./setup.sh
```

这将安装所有依赖，包括：
- 基础依赖（NATS、LangChain等）
- LLM提供商支持
- 消息去重功能依赖
- 运行基础测试和去重功能测试

### 快速安装（跳过去重测试）

```bash
./setup.sh --skip-dedup-test
```

如果网络较慢或不需要立即测试去重功能，可以使用此选项。

## 安装脚本功能

### 新增功能
- ✅ 自动安装消息去重依赖（sentence-transformers、faiss-cpu、numpy）
- ✅ 验证去重功能依赖安装状态
- ✅ 可选的去重功能测试
- ✅ 命令行参数支持
- ✅ 详细的配置指导

### 安装流程
1. **Python版本检查** - 确保Python >= 3.8
2. **依赖安装** - 安装所有必需的Python包
3. **配置文件设置** - 从示例创建配置文件
4. **基础测试** - 验证基本功能
5. **去重功能测试** - 验证消息去重功能（可选）
6. **使用指导** - 显示后续配置和使用步骤

## 命令行选项

```bash
./setup.sh [选项]

选项:
  --skip-dedup-test    跳过消息去重功能测试
  --help, -h          显示帮助信息
```

## 注意事项

- 首次运行去重功能测试时会下载BGE-M3模型（约1-2GB）
- 如果网络较慢，建议使用 `--skip-dedup-test` 选项
- 去重功能测试失败不会影响基础功能的使用
- 详细的去重功能配置请参考 `DEDUPLICATION_GUIDE.md`

## 迁移说明

如果之前使用过独立的 `install_deduplication.sh` 脚本：

1. 该脚本已被删除
2. 所有功能已合并到 `setup.sh` 中
3. 重新运行 `./setup.sh` 即可完成完整安装

## 故障排除

### 依赖安装失败
```bash
# 手动安装去重依赖
pip install sentence-transformers>=2.2.0 faiss-cpu>=1.7.0 numpy>=1.21.0
```

### 模型下载失败
```bash
# 跳过测试，稍后手动测试
./setup.sh --skip-dedup-test
python test_deduplication.py  # 稍后运行
```

### 权限问题
```bash
# 确保脚本有执行权限
chmod +x setup.sh
``` 