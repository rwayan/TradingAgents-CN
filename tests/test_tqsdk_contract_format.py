#!/usr/bin/env python3
"""
测试天勤合约格式的脚本
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from tradingagents.dataflows.tqsdk_futures_adapter import get_tqsdk_futures_adapter

async def test_contract_formats():
    """测试天勤合约格式"""
    print("🔍 测试天勤合约格式...")
    
    adapter = get_tqsdk_futures_adapter()
    
    try:
        # 获取指数合约样本
        print("\n📊 指数合约格式:")
        index_contracts = await adapter.query_quotes(ins_class="INDEX", expired=False)
        if index_contracts:
            print(f"总数: {len(index_contracts)}")
            print("前20个样本:")
            for i, contract in enumerate(index_contracts[:20]):
                print(f"  {i+1:2d}. {contract}")
        
        # 获取主连合约样本
        print("\n🔗 主连合约格式:")
        main_contracts = await adapter.query_quotes(ins_class="CONT")
        if main_contracts:
            print(f"总数: {len(main_contracts)}")
            print("前20个样本:")
            for i, contract in enumerate(main_contracts[:20]):
                print(f"  {i+1:2d}. {contract}")
        
        # 获取铜相关合约
        print("\n🔸 铜相关合约:")
        cu_index = await adapter.query_quotes(ins_class="INDEX", product_id="cu")
        cu_main = await adapter.query_quotes(ins_class="CONT", product_id="cu")
        cu_futures = await adapter.query_quotes(ins_class="FUTURE", product_id="cu", expired=False)
        
        print(f"铜指数合约: {cu_index}")
        print(f"铜主连合约: {cu_main}")
        if cu_futures:
            print(f"铜期货合约（前5个）: {cu_futures[:5]}")
        
        # 获取黄金相关合约
        print("\n🔸 黄金相关合约:")
        au_index = await adapter.query_quotes(ins_class="INDEX", product_id="au")
        au_main = await adapter.query_quotes(ins_class="CONT", product_id="au")
        
        print(f"黄金指数合约: {au_index}")
        print(f"黄金主连合约: {au_main}")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        adapter.disconnect()

if __name__ == "__main__":
    asyncio.run(test_contract_formats())