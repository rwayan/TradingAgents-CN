#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试天勤合约格式的脚本
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

async def test_contract_formats():
    """测试天勤合约格式"""
    print("Testing TqSdk contract formats...")
    
    try:
        from tradingagents.dataflows.tqsdk_futures_adapter import get_tqsdk_futures_adapter
        adapter = get_tqsdk_futures_adapter()
        
        # 获取指数合约样本
        print("\nIndex contracts:")
        index_contracts = await adapter.query_quotes(ins_class="INDEX", expired=False)
        if index_contracts:
            print(f"Total: {len(index_contracts)}")
            print("First 10 samples:")
            for i, contract in enumerate(index_contracts[:10]):
                print(f"  {i+1:2d}. {contract}")
        
        # 获取主连合约样本
        print("\nMain contracts:")
        main_contracts = await adapter.query_quotes(ins_class="CONT")
        if main_contracts:
            print(f"Total: {len(main_contracts)}")
            print("First 10 samples:")
            for i, contract in enumerate(main_contracts[:10]):
                print(f"  {i+1:2d}. {contract}")
        
        # 获取铜相关合约
        print("\nCopper contracts:")
        cu_index = await adapter.query_quotes(ins_class="INDEX", product_id="cu")
        cu_main = await adapter.query_quotes(ins_class="CONT", product_id="cu")
        
        print(f"Copper index: {cu_index}")
        print(f"Copper main: {cu_main}")
        
        adapter.disconnect()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_contract_formats())