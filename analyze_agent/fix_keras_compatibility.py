#!/usr/bin/env python3
"""
Keras兼容性修复脚本
解决Keras 3与transformers库的兼容性问题
"""

import subprocess
import sys
import importlib.util

def check_package_installed(package_name):
    """检查包是否已安装"""
    spec = importlib.util.find_spec(package_name)
    return spec is not None

def get_keras_version():
    """获取Keras版本"""
    try:
        import keras
        return getattr(keras, '__version__', 'unknown')
    except ImportError:
        return None

def install_package(package_name):
    """安装包"""
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', package_name])
        return True
    except subprocess.CalledProcessError:
        return False

def main():
    print("🔧 Keras兼容性检查和修复工具")
    print("=" * 50)
    
    # 检查Keras版本
    keras_version = get_keras_version()
    
    if keras_version is None:
        print("✅ 未安装Keras，无兼容性问题")
        return
    
    print(f"📦 检测到Keras版本: {keras_version}")
    
    if keras_version.startswith('3.'):
        print("⚠️  检测到Keras 3，需要安装tf-keras以保证transformers兼容性")
        
        # 检查tf-keras是否已安装
        if check_package_installed('tf_keras'):
            print("✅ tf-keras已安装")
        else:
            print("📥 正在安装tf-keras...")
            if install_package('tf-keras'):
                print("✅ tf-keras安装成功")
            else:
                print("❌ tf-keras安装失败")
                print("请手动运行: pip install tf-keras")
                return
        
        # 验证修复
        print("\n🧪 验证修复...")
        try:
            import tf_keras
            print("✅ tf-keras导入成功")
            
            # 尝试导入transformers
            import transformers
            print("✅ transformers导入成功")
            
            print("\n🎉 Keras兼容性问题已修复！")
            
        except ImportError as e:
            print(f"❌ 验证失败: {e}")
            print("\n🔧 建议的解决方案:")
            print("1. 重启Python环境")
            print("2. 如果问题持续，尝试重新安装transformers:")
            print("   pip uninstall transformers")
            print("   pip install transformers")
            print("3. 或者降级Keras到2.x版本:")
            print("   pip install keras==2.15.0")
    
    else:
        print("✅ Keras版本兼容，无需修复")

if __name__ == "__main__":
    main() 