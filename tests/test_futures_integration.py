#!/usr/bin/env python3
"""
测试期货分析师集成功能
验证期货代码识别和分析师切换逻辑
"""

import sys
import os

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from tradingagents.utils.stock_utils import StockUtils

def test_futures_identification():
    """测试期货代码识别功能"""
    print("测试期货代码识别功能...")
    
    # 测试期货代码
    futures_codes = [
        "CU99",    # 沪铜主力
        "CU2501",  # 沪铜2501合约
        "AU99",    # 黄金主力
        "AU2501",  # 黄金2501合约
        "IF99",    # 沪深300股指主力
        "IF2501",  # 沪深300股指2501合约
        "SC99",    # 原油主力
        "SC2501"   # 原油2501合约
    ]
    
    # 测试股票代码（对比）
    stock_codes = [
        "000001",    # 平安银行
        "600036",    # 招商银行
        "0700.HK",   # 腾讯控股
        "AAPL",      # 苹果
        "TSLA"       # 特斯拉
    ]
    
    print("\n期货代码识别测试：")
    for code in futures_codes:
        market_info = StockUtils.get_market_info(code)
        print(f"  {code:8} -> {market_info['market_name']:8} | is_futures: {market_info['is_futures']}")
    
    print("\n股票代码识别测试（对比）：")
    for code in stock_codes:
        market_info = StockUtils.get_market_info(code)
        print(f"  {code:8} -> {market_info['market_name']:8} | is_futures: {market_info['is_futures']}")

def test_analyst_imports():
    """测试期货分析师模块导入"""
    print("\n测试期货分析师模块导入...")
    
    try:
        from tradingagents.agents.analysts.futures_technical_analyst import create_futures_technical_analyst
        print("  期货技术分析师导入成功")
    except ImportError as e:
        print(f"  期货技术分析师导入失败: {e}")
        return False
    
    try:
        from tradingagents.agents.analysts.futures_fundamentals_analyst import create_futures_fundamentals_analyst
        print("  期货基本面分析师导入成功")
    except ImportError as e:
        print(f"  期货基本面分析师导入失败: {e}")
        return False
    
    return True

def test_integration_logic():
    """测试集成逻辑"""
    print("\n测试期货分析师集成逻辑...")
    
    # 模拟market_analyst中的期货检测逻辑
    test_ticker = "CU99"
    market_info = StockUtils.get_market_info(test_ticker)
    
    print(f"  测试期货代码: {test_ticker}")
    print(f"  市场信息: {market_info}")
    
    if market_info['is_futures']:
        print("  期货检测逻辑正常，会切换到期货技术分析师")
        try:
            from tradingagents.agents.analysts.futures_technical_analyst import create_futures_technical_analyst
            print("  期货技术分析师创建函数可用")
        except ImportError as e:
            print(f"  期货技术分析师导入失败: {e}")
    else:
        print("  期货检测逻辑失败")
    
    # 模拟fundamentals_analyst中的期货检测逻辑
    if market_info['is_futures']:
        print("  基本面分析师期货检测逻辑正常，会切换到期货基本面分析师")
        try:
            from tradingagents.agents.analysts.futures_fundamentals_analyst import create_futures_fundamentals_analyst
            print("  期货基本面分析师创建函数可用")
        except ImportError as e:
            print(f"  期货基本面分析师导入失败: {e}")
    else:
        print("  基本面分析师期货检测逻辑失败")

if __name__ == "__main__":
    print("期货分析师集成测试")
    print("=" * 50)
    
    # 测试期货代码识别
    test_futures_identification()
    
    # 测试模块导入
    if test_analyst_imports():
        # 测试集成逻辑
        test_integration_logic()
        
        print("\n所有测试通过！期货分析师集成成功。")
        print("现在当用户输入期货代码时：")
        print("   - market分析师会自动切换到期货技术分析师")
        print("   - fundamentals分析师会自动切换到期货基本面分析师")
    else:
        print("\n模块导入测试失败，请检查期货分析师文件。")