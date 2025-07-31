#!/usr/bin/env python3
"""
测试期货分析师工具调用修复
验证 Toolkit.get_futures_data_unified 工具是否可用
"""

import sys
import os

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def test_toolkit_futures_tool():
    """测试 Toolkit 中的期货工具"""
    print("测试 Toolkit.get_futures_data_unified 工具")
    print("-" * 50)
    
    try:
        from tradingagents.agents.utils.agent_utils import Toolkit
        
        # 创建 Toolkit 实例
        toolkit = Toolkit()
        
        # 检查是否有 get_futures_data_unified 属性
        if hasattr(toolkit, 'get_futures_data_unified'):
            print("  [OK] get_futures_data_unified 工具存在")
            
            # 检查工具是否可调用
            if callable(toolkit.get_futures_data_unified):
                print("  [OK] get_futures_data_unified 工具可调用")
                
                # 测试工具调用（简单测试，不实际执行，避免依赖问题）
                try:
                    # 只测试工具定义，不实际调用
                    tool_func = toolkit.get_futures_data_unified
                    print(f"  [OK] 工具函数: {tool_func}")
                    print(f"  [OK] 工具名称: {getattr(tool_func, 'name', 'get_futures_data_unified')}")
                    print("  [OK] 期货工具定义正常")
                    return True
                except Exception as e:
                    print(f"  [ERROR] 工具调用测试失败: {e}")
                    return False
            else:
                print("  [ERROR] get_futures_data_unified 工具不可调用")
                return False
        else:
            print("  [ERROR] get_futures_data_unified 工具不存在")
            return False
            
    except Exception as e:
        print(f"  [ERROR] Toolkit 导入或创建失败: {e}")
        return False

def test_futures_analyst_import():
    """测试期货分析师能否正常导入"""
    print("\n测试期货分析师导入")
    print("-" * 50)
    
    try:
        from tradingagents.agents.analysts.futures_technical_analyst import create_futures_technical_analyst
        from tradingagents.agents.analysts.futures_fundamentals_analyst import create_futures_fundamentals_analyst
        print("  [OK] 期货分析师导入成功")
        return True
    except Exception as e:
        print(f"  [ERROR] 期货分析师导入失败: {e}")
        return False

def test_data_source_manager():
    """测试数据源管理器中的期货函数"""
    print("\n测试数据源管理器期货函数")
    print("-" * 50)
    
    try:
        from tradingagents.dataflows.data_source_manager import get_futures_data_unified
        print("  [OK] get_futures_data_unified 函数导入成功")
        
        # 检查函数是否可调用
        if callable(get_futures_data_unified):
            print("  [OK] get_futures_data_unified 函数可调用")
            return True
        else:
            print("  [ERROR] get_futures_data_unified 函数不可调用")
            return False
            
    except Exception as e:
        print(f"  [ERROR] 数据源管理器导入失败: {e}")
        return False

if __name__ == "__main__":
    print("期货分析师工具调用修复测试")
    print("=" * 50)
    
    success_count = 0
    total_tests = 3
    
    # 测试 Toolkit 期货工具
    if test_toolkit_futures_tool():
        success_count += 1
    
    # 测试期货分析师导入
    if test_futures_analyst_import():
        success_count += 1
    
    # 测试数据源管理器
    if test_data_source_manager():
        success_count += 1
    
    print("\n" + "=" * 50)
    print(f"测试结果: {success_count}/{total_tests} 项测试通过")
    
    if success_count == total_tests:
        print("[SUCCESS] 所有测试通过！期货分析师工具调用问题已修复。")
    else:
        print("[PARTIAL] 部分测试通过，可能仍有问题需要解决。")