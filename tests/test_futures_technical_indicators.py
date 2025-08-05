#!/usr/bin/env python3
"""
测试期货技术指标功能
"""

import sys
import os
# 添加项目根目录到Python路径
project_root = '\\'.join(os.path.dirname(os.path.abspath(__file__)).split('\\')[:-1])
sys.path.insert(0, project_root)

from tradingagents.dataflows.tqsdk_futures_adapter import get_tqsdk_futures_adapter
from datetime import datetime, timedelta

def test_futures_technical_indicators():
    """测试期货技术指标功能"""
    print("🧪 开始测试期货技术指标功能...")
    
    try:
        # 获取适配器实例
        adapter = get_tqsdk_futures_adapter()
        
        # 测试期货代码（使用沪铜指数）
        symbol = "CU99"
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=60)).strftime('%Y-%m-%d')
        
        print(f"📊 测试期货: {symbol}")
        print(f"📅 数据期间: {start_date} 至 {end_date}")
        
        # 获取期货数据（包含技术指标）
        result = adapter.get_futures_data(symbol, start_date, end_date)
        
        print("\n" + "="*80)
        print("📊 期货数据报告（包含技术指标）:")
        print("="*80)
        print(result)
        
        # 检查是否包含技术指标
        if "🔍 技术指标分析:" in result:
            print("\n✅ 技术指标功能测试成功！")
            
            # 检查具体指标
            indicators_found = []
            if "MA5:" in result:
                indicators_found.append("MA5")
            if "RSI:" in result:
                indicators_found.append("RSI")
            if "MACD:" in result:
                indicators_found.append("MACD")
            if "布林带上轨:" in result:
                indicators_found.append("布林带")
            if "KDJ_K:" in result:
                indicators_found.append("KDJ")
            if "威廉指标:" in result:
                indicators_found.append("威廉指标")
            if "持仓量变化:" in result:
                indicators_found.append("持仓量分析")
            
            print(f"📈 检测到的技术指标: {', '.join(indicators_found)}")
            
            if len(indicators_found) >= 5:
                print("🎉 技术指标功能完整！")
            else:
                print("⚠️ 部分技术指标可能未计算成功")
        else:
            print("❌ 未检测到技术指标信息")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_futures_technical_indicators()