#!/usr/bin/env python3
"""
语法检查脚本
"""

import ast
import sys

def check_syntax(filename):
    """检查Python文件语法"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            source = f.read()
        
        # 解析AST
        ast.parse(source, filename=filename)
        print(f"✅ {filename} 语法检查通过")
        return True
        
    except SyntaxError as e:
        print(f"❌ {filename} 语法错误:")
        print(f"   行 {e.lineno}: {e.text}")
        print(f"   错误: {e.msg}")
        return False
    except Exception as e:
        print(f"❌ {filename} 检查失败: {e}")
        return False

if __name__ == '__main__':
    files_to_check = ['main.py', 'test_syntax.py']
    
    all_passed = True
    for filename in files_to_check:
        if not check_syntax(filename):
            all_passed = False
    
    if all_passed:
        print("\n🎉 所有文件语法检查通过！")
        sys.exit(0)
    else:
        print("\n💥 存在语法错误！")
        sys.exit(1) 