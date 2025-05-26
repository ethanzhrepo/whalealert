# Keras 3 兼容性问题快速修复指南

## 问题描述

如果您在运行去重功能测试时遇到以下错误：

```
ValueError: Your currently installed version of Keras is Keras 3, but this is not yet supported in Transformers. Please install the backwards-compatible tf-keras package with `pip install tf-keras`.
```

这是因为您的系统安装了 Keras 3，但当前版本的 `transformers` 库还不完全支持 Keras 3。

## 快速解决方案

### 方法1: 使用自动修复脚本（推荐）

```bash
python3 fix_keras_compatibility.py
```

这个脚本会：
1. 检测您的Keras版本
2. 如果是Keras 3，自动安装tf-keras包
3. 验证修复是否成功

### 方法2: 手动安装tf-keras

```bash
pip install tf-keras
```

### 方法3: 降级Keras（如果不需要Keras 3）

```bash
pip install keras==2.15.0
```

## 验证修复

运行以下命令验证问题是否解决：

```bash
python3 -c "
try:
    from sentence_transformers import SentenceTransformer
    print('✅ sentence-transformers导入成功')
    
    import transformers
    print('✅ transformers导入成功')
    
    print('🎉 Keras兼容性问题已解决！')
except ImportError as e:
    print(f'❌ 仍有问题: {e}')
"
```

## 重新运行测试

修复后，重新运行去重功能测试：

```bash
python3 test_deduplication.py
python3 test_model_detection.py
```

## 为什么会出现这个问题？

- **Keras 3** 是Keras的最新主要版本，引入了许多重大变化
- **transformers库** 目前还在适配Keras 3，暂时不完全支持
- **tf-keras** 是一个向后兼容包，提供了Keras 2.x的API
- 这是一个临时解决方案，未来transformers库会完全支持Keras 3

## 其他注意事项

1. **不影响基础功能**: 这个问题只影响去重功能，不影响其他Agent功能
2. **临时解决方案**: 随着transformers库的更新，这个问题会被解决
3. **环境隔离**: 建议使用虚拟环境来避免包冲突

## 如果问题仍然存在

如果上述方法都无法解决问题，请尝试：

1. **重启Python环境**
2. **重新安装transformers**:
   ```bash
   pip uninstall transformers
   pip install transformers
   ```
3. **使用虚拟环境**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Linux/Mac
   # 或 venv\Scripts\activate  # Windows
   pip install -r requirements.txt
   ```

## 联系支持

如果问题持续存在，请提供以下信息：
- Python版本
- Keras版本
- transformers版本
- 完整的错误信息 