
import os
import sys

# 添加项目根目录到Python路径
project_root = '\\'.join(os.path.dirname(os.path.abspath(__file__)).split('\\')[:-1])
sys.path.insert(0, project_root)


from tradingagents.dataflows.tqsdk_futures_adapter import TqSdkFuturesAdapter
adapter = TqSdkFuturesAdapter()
print('完整测试 _normalize_symbol 函数:')
print('=' * 50) 


test_cases = [   
    'T2512',      # 应该返回 CFFEX.T2501
    'TS2501',     # 应该返回 CFFEX.TS2501
    'i2501',      # 应该返回 DCE.i2501
    'cu2509',     # 应该返回 SHFE.cu2509
    'TA601',      # 应该返回 CZCE.TA601
    'fg99',
    'CU99',      # 应该返回 SHFE.CU99
    'CU2509'
]

for case in test_cases:
    result = adapter._normalize_symbol(case)
    contract = adapter.get_futures_info(case)
    
    print(f"输入: {case} -> 输出: {result}")
    print(f"输入: {case} -> 期货信息: {contract}")

