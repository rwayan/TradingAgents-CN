"""
期货合约管理器使用示例和测试
"""

from tradingagents.dataflows.futures_contract_manager import get_contract_manager

def test_contract_manager():
    """测试期货合约管理器功能"""
    
    manager = get_contract_manager()
    
    print("=== 期货合约管理器测试 ===\n")
    
    # 测试1: 验证期货代码
    test_codes = ["CU99", "IF99", "RB2403", "INVALID", "AL", "SC99"]
    print("1. 验证期货代码:")
    for code in test_codes:
        is_valid, error_msg, contract_info = manager.validate_futures_input(code)
        status = "✅" if is_valid else "❌"
        print(f"   {status} {code}: {error_msg if error_msg else '有效'}")
    
    print("\n2. 解析期货代码:")
    for code in ["CU99", "CU2403", "IF99", "RB2405"]:
        symbol, is_index = manager.parse_futures_code(code)
        if symbol:
            print(f"   {code} -> {symbol} ({'指数合约' if is_index else '具体合约'})")
    
    print("\n3. 获取合约信息:")
    for symbol in ["CU", "IF", "RB"]:
        contract = manager.get_contract(symbol)
        if contract:
            print(f"   {symbol}: {contract.name} ({contract.exchange.value}) - {contract.index_code}")
    
    print("\n4. 搜索合约:")
    search_results = manager.search_contracts("铜")
    print(f"   搜索'铜': 找到 {len(search_results)} 个结果")
    for contract in search_results:
        print(f"     • {contract.symbol} - {contract.name}")
    
    print("\n5. 按交易所分类:")
    from tradingagents.dataflows.futures_contract_manager import FuturesExchange
    shfe_contracts = manager.get_contracts_by_exchange(FuturesExchange.SHFE)
    print(f"   上期所合约数量: {len(shfe_contracts)}")
    
    print("\n6. 按品种分类:")
    from tradingagents.dataflows.futures_contract_manager import FuturesCategory
    metal_contracts = manager.get_contracts_by_category(FuturesCategory.METALS)
    print(f"   有色金属合约数量: {len(metal_contracts)}")
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    test_contract_manager()