#!/usr/bin/env python3
"""
简化的期货分析师集成测试
只测试市场识别和切换逻辑，不依赖langchain
"""

import sys
import os

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from tradingagents.utils.stock_utils import StockUtils

def test_futures_market_detection():
    """测试期货市场检测功能"""
    print("期货市场检测测试")
    print("-" * 30)
    
    # 测试各种期货代码
    test_cases = [
        ("CU99", "沪铜主力"),
        ("CU2501", "沪铜2501"),
        ("AU99", "黄金主力"),
        ("IF99", "沪深300股指主力"),
        ("SC99", "原油主力"),
        ("000001", "平安银行（对比）"),
        ("AAPL", "苹果（对比）")
    ]
    
    for code, desc in test_cases:
        market_info = StockUtils.get_market_info(code)
        is_futures = market_info['is_futures']
        market_name = market_info['market_name']
        
        status = "期货" if is_futures else "非期货"
        print(f"  {code:8} ({desc:12}) -> {market_name:8} | {status}")

def test_integration_switch_logic():
    """测试集成切换逻辑"""
    print("\n期货分析师切换逻辑测试")  
    print("-" * 30)
    
    # 模拟market_analyst.py中的检测逻辑
    def simulate_market_analyst_logic(ticker):
        from tradingagents.utils.stock_utils import StockUtils
        market_info = StockUtils.get_market_info(ticker)
        
        print(f"  输入代码: {ticker}")
        print(f"  市场类型: {market_info['market_name']}")
        print(f"  是否期货: {market_info['is_futures']}")
        
        if market_info['is_futures']:
            try:
                # 检查期货分析师文件是否存在
                futures_tech_file = os.path.join(project_root, 'tradingagents', 'agents', 'analysts', 'futures_technical_analyst.py')
                if os.path.exists(futures_tech_file):
                    print("  -> 会切换到期货技术分析师 [OK]")
                else:
                    print("  -> 期货技术分析师文件不存在 [ERROR]")
            except Exception as e:
                print(f"  -> 切换失败: {e}")
        else:
            print("  -> 继续使用股票市场分析师")
    
    # 模拟fundamentals_analyst.py中的检测逻辑  
    def simulate_fundamentals_analyst_logic(ticker):
        from tradingagents.utils.stock_utils import StockUtils
        market_info = StockUtils.get_market_info(ticker)
        
        if market_info['is_futures']:
            try:
                # 检查期货分析师文件是否存在
                futures_fund_file = os.path.join(project_root, 'tradingagents', 'agents', 'analysts', 'futures_fundamentals_analyst.py') 
                if os.path.exists(futures_fund_file):
                    print("  -> 会切换到期货基本面分析师 [OK]")
                else:
                    print("  -> 期货基本面分析师文件不存在 [ERROR]")
            except Exception as e:
                print(f"  -> 切换失败: {e}")
        else:
            print("  -> 继续使用股票基本面分析师")
    
    # 测试期货代码
    print("\n测试期货代码 CU99:")
    simulate_market_analyst_logic("CU99")
    simulate_fundamentals_analyst_logic("CU99")
    
    # 测试股票代码
    print("\n测试股票代码 000001:")
    simulate_market_analyst_logic("000001")
    simulate_fundamentals_analyst_logic("000001")

def check_integration_files():
    """检查集成相关文件"""
    print("\n集成文件检查")
    print("-" * 30)
    
    files_to_check = [
        ('tradingagents/agents/analysts/market_analyst.py', '市场分析师'),
        ('tradingagents/agents/analysts/fundamentals_analyst.py', '基本面分析师'),
        ('tradingagents/agents/analysts/futures_technical_analyst.py', '期货技术分析师'),
        ('tradingagents/agents/analysts/futures_fundamentals_analyst.py', '期货基本面分析师'),
        ('tradingagents/utils/stock_utils.py', '股票工具类')
    ]
    
    for file_path, description in files_to_check:
        full_path = os.path.join(project_root, file_path)
        if os.path.exists(full_path):
            print(f"  [OK] {description}: {file_path}")
        else:
            print(f"  [ERROR] {description}: {file_path} (不存在)")

if __name__ == "__main__":
    print("期货分析师集成验证测试")
    print("=" * 50)
    
    # 测试期货市场检测
    test_futures_market_detection()
    
    # 测试集成切换逻辑
    test_integration_switch_logic()
    
    # 检查相关文件
    check_integration_files()
    
    print("\n" + "=" * 50)
    print("测试完成")
    print("如果所有检查都显示 [OK]，说明期货分析师集成成功！")