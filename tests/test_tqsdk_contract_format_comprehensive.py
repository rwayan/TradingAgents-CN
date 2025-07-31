#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
天勤合约格式和合约管理器测试脚本
测试天勤API的实际合约格式以及合约管理器的功能
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

async def test_contract_formats():
    """测试天勤合约格式"""
    print("=" * 60)
    print("Testing TqSdk Contract Formats")
    print("=" * 60)
    
    try:
        from tradingagents.dataflows.tqsdk_futures_adapter import get_tqsdk_futures_adapter
        from tradingagents.dataflows.futures_contract_manager import get_contract_manager
        
        adapter = get_tqsdk_futures_adapter()
        manager = get_contract_manager()
        
        # 测试指数合约格式
        print("\n1. Index Contracts (ins_class='INDEX'):")
        index_contracts = await adapter.query_quotes(ins_class="INDEX", expired=False)
        if index_contracts:
            print(f"   Total: {len(index_contracts)}")
            print("   Sample formats:")
            for i, contract in enumerate(index_contracts[:8]):
                print(f"     {i+1:2d}. {contract}")
        
        # 测试主连合约格式
        print("\n2. Main Contracts (ins_class='CONT'):")
        main_contracts = await adapter.query_quotes(ins_class="CONT")
        if main_contracts:
            print(f"   Total: {len(main_contracts)}")
            print("   Sample formats:")
            for i, contract in enumerate(main_contracts[:8]):
                print(f"     {i+1:2d}. {contract}")
        
        # 测试具体品种
        print("\n3. Specific Product Tests:")
        test_symbols = ["cu", "au", "cf", "if"]
        
        for symbol in test_symbols:
            print(f"\n   Testing {symbol.upper()}:")
            
            # 指数合约
            symbol_index = await adapter.query_quotes(ins_class="INDEX", product_id=symbol)
            print(f"     Index: {symbol_index}")
            
            # 主连合约
            symbol_main = await adapter.query_quotes(ins_class="CONT", product_id=symbol)
            print(f"     Main:  {symbol_main}")
        
        # 测试合约管理器
        print("\n4. Testing Contract Manager:")
        
        # 强制刷新
        await manager._refresh_contracts(force_refresh=True)
        
        # 测试获取合约信息
        test_symbols = ["cu", "au", "cf", "if"]
        for symbol in test_symbols:
            contract = manager.get_contract(symbol)
            index_code = manager.get_index_code(symbol)
            full_code = manager.get_full_code(symbol)
            
            print(f"\n   {symbol.upper()}:")
            print(f"     Contract: {contract}")
            print(f"     Index:    {index_code}")
            print(f"     Full:     {full_code}")
        
        # 测试解析功能
        print("\n5. Testing Contract Parsing:")
        test_codes = [
            "KQ.i@SHFE.cu",      # 天勤指数格式
            "KQ.m@SHFE.cu",      # 天勤主连格式
            "cu99",              # 传统指数格式
            "cu888",             # 传统主连格式
            "cu2403",            # 具体合约格式
            "SHFE.cu99",         # 交易所格式
        ]
        
        for code in test_codes:
            symbol, is_index = manager.parse_futures_code(code)
            print(f"     {code:15s} -> Symbol: {symbol}, Index: {is_index}")
        
        # 测试获取所有品种
        print("\n6. Available Symbols:")
        all_symbols = manager.get_all_symbols()
        print(f"   Total symbols: {len(all_symbols)}")
        print(f"   First 20: {all_symbols[:20]}")
        
        adapter.disconnect()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

def test_exchange_case_rules():
    """测试交易所大小写规则"""
    print("\n" + "=" * 60)
    print("Exchange Case Rules Analysis")
    print("=" * 60)
    
    # 根据观察到的规律
    exchanges = {
        "SHFE": "lowercase (shfe.cu)",
        "DCE": "lowercase (dce.a)",
        "INE": "lowercase (ine.sc)",
        "CZCE": "uppercase (CZCE.CF)",
        "GFEX": "uppercase (GFEX.SI)",
        "CFFEX": "uppercase (CFFEX.IF)"
    }
    
    print("Expected case rules:")
    for exchange, rule in exchanges.items():
        print(f"  {exchange:6s}: {rule}")

if __name__ == "__main__":
    print("Starting TqSdk Contract Format Tests...")
    
    # 测试交易所大小写规则
    test_exchange_case_rules()
    
    # 异步测试合约格式
    asyncio.run(test_contract_formats())
    
    print("\nTest completed!")