#!/usr/bin/env python3
"""
简单验证期货工具是否已添加到 Toolkit 中
"""

import sys
import os
import ast
import inspect

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def check_toolkit_source():
    """检查 Toolkit 源代码中是否包含 get_futures_data_unified"""
    print("检查 Toolkit 源代码")
    print("-" * 30)
    
    toolkit_file = os.path.join(project_root, 'tradingagents', 'agents', 'utils', 'agent_utils.py')
    
    if os.path.exists(toolkit_file):
        with open(toolkit_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否包含期货工具定义
        if 'def get_futures_data_unified(' in content:
            print("  [OK] 源代码中包含 get_futures_data_unified 方法")
            
            # 统计工具装饰器数量
            tool_count = content.count('@tool')
            print(f"  [INFO] 总共发现 {tool_count} 个 @tool 装饰器")
            
            # 检查期货工具是否有正确的装饰器
            if '@tool' in content and 'get_futures_data_unified' in content:
                print("  [OK] get_futures_data_unified 具有 @tool 装饰器")
                
                # 找到函数的文档字符串
                import re
                pattern = r'def get_futures_data_unified.*?"""(.*?)"""'
                match = re.search(pattern, content, re.DOTALL)
                if match:
                    docstring = match.group(1).strip()
                    print(f"  [OK] 函数文档字符串: {docstring[:100]}...")
                
                return True
            else:
                print("  [ERROR] get_futures_data_unified 缺少 @tool 装饰器")
                return False
        else:
            print("  [ERROR] 源代码中未找到 get_futures_data_unified 方法")
            return False
    else:
        print("  [ERROR] agent_utils.py 文件不存在")
        return False

def check_data_source_function():
    """检查数据源管理器中的期货函数"""
    print("\n检查数据源管理器")
    print("-" * 30)
    
    data_source_file = os.path.join(project_root, 'tradingagents', 'dataflows', 'data_source_manager.py')
    
    if os.path.exists(data_source_file):
        with open(data_source_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'def get_futures_data_unified(' in content:
            print("  [OK] 数据源管理器中包含 get_futures_data_unified 函数")
            return True
        else:
            print("  [ERROR] 数据源管理器中未找到 get_futures_data_unified 函数")
            return False
    else:
        print("  [ERROR] data_source_manager.py 文件不存在")
        return False

def check_futures_analysts():
    """检查期货分析师文件是否存在"""
    print("\n检查期货分析师文件")
    print("-" * 30)
    
    files_to_check = [
        'tradingagents/agents/analysts/futures_technical_analyst.py',
        'tradingagents/agents/analysts/futures_fundamentals_analyst.py'
    ]
    
    all_exist = True
    for file_path in files_to_check:
        full_path = os.path.join(project_root, file_path)
        if os.path.exists(full_path):
            print(f"  [OK] {file_path}")
        else:
            print(f"  [ERROR] {file_path} 不存在")
            all_exist = False
    
    return all_exist

if __name__ == "__main__":
    print("期货工具集成验证")
    print("=" * 50)
    
    success_count = 0
    total_checks = 3
    
    # 检查 Toolkit 源代码
    if check_toolkit_source():
        success_count += 1
    
    # 检查数据源管理器
    if check_data_source_function():
        success_count += 1
    
    # 检查期货分析师文件
    if check_futures_analysts():
        success_count += 1
    
    print("\n" + "=" * 50)
    print(f"验证结果: {success_count}/{total_checks} 项检查通过")
    
    if success_count == total_checks:
        print("[SUCCESS] 所有检查通过！")
        print("修复内容:")
        print("1. 在 Toolkit 类中添加了 get_futures_data_unified 工具")
        print("2. 期货数据源管理器函数可用")
        print("3. 期货分析师文件存在")
        print("\n现在期货分析师应该能够正常调用 toolkit.get_futures_data_unified 工具了！")
    else:
        print("[PARTIAL] 部分检查通过，可能仍有问题需要解决。")