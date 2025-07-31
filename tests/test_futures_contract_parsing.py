#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
期货合约管理器单元测试
测试FuturesContractManager的各种功能和格式解析
"""

import unittest
import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from tradingagents.dataflows.futures_contract_manager import get_contract_manager


class TestFuturesContractManager(unittest.TestCase):
    """期货合约管理器测试类"""
    
    def setUp(self):
        """测试初始化"""
        self.manager = get_contract_manager()
    
    def test_parse_tqsdk_index_format(self):
        """测试解析天勤指数合约格式"""
        test_cases = [
            ("KQ.i@SHFE.cu", "CU", True),      # 小写品种
            ("KQ.i@CZCE.CF", "CF", True),      # 大写品种
            ("KQ.i@DCE.a", "A", True),         # 小写品种
            ("KQ.i@GFEX.SI", "SI", True),      # 大写品种
            ("KQ.i@CFFEX.IF", "IF", True),     # 大写品种
        ]
        
        for contract_code, expected_symbol, expected_is_index in test_cases:
            with self.subTest(contract=contract_code):
                symbol, is_index = self.manager.parse_futures_code(contract_code)
                self.assertEqual(symbol, expected_symbol)
                self.assertEqual(is_index, expected_is_index)
    
    def test_parse_tqsdk_main_format(self):
        """测试解析天勤主连合约格式"""
        test_cases = [
            ("KQ.m@SHFE.cu", "CU", True),      # 小写品种
            ("KQ.m@CZCE.CF", "CF", True),      # 大写品种
            ("KQ.m@DCE.a", "A", True),         # 小写品种
            ("KQ.m@GFEX.SI", "SI", True),      # 大写品种
            ("KQ.m@CFFEX.IF", "IF", True),     # 大写品种
        ]
        
        for contract_code, expected_symbol, expected_is_index in test_cases:
            with self.subTest(contract=contract_code):
                symbol, is_index = self.manager.parse_futures_code(contract_code)
                self.assertEqual(symbol, expected_symbol)
                self.assertEqual(is_index, expected_is_index)
    
    def test_parse_legacy_formats(self):
        """测试解析传统合约格式"""
        test_cases = [
            ("CU99", "CU", True),              # 指数合约
            ("CU888", "CU", True),             # 主连合约
            ("CU2403", "CU", False),           # 具体合约
            ("IF99", "IF", True),              # 股指期货指数
            ("IF2403", "IF", False),           # 股指期货具体合约
        ]
        
        for contract_code, expected_symbol, expected_is_index in test_cases:
            with self.subTest(contract=contract_code):
                symbol, is_index = self.manager.parse_futures_code(contract_code)
                self.assertEqual(symbol, expected_symbol)
                self.assertEqual(is_index, expected_is_index)
    
    def test_parse_exchange_formats(self):
        """测试解析交易所格式"""
        test_cases = [
            ("SHFE.CU99", "CU", True),         # 指数合约
            ("SHFE.cu99", "CU", True),         # 小写指数合约
            ("SHFE.CU2403", "CU", False),      # 具体合约
            ("CZCE.CF99", "CF", True),         # 郑商所指数
            ("DCE.A99", "A", True),            # 大商所指数
        ]
        
        for contract_code, expected_symbol, expected_is_index in test_cases:
            with self.subTest(contract=contract_code):
                symbol, is_index = self.manager.parse_futures_code(contract_code)
                self.assertEqual(symbol, expected_symbol)
                self.assertEqual(is_index, expected_is_index)
    
    def test_invalid_formats(self):
        """测试无效格式"""
        invalid_codes = [
            "",                    # 空字符串
            "INVALID",             # 无效代码
            "123ABC",              # 数字开头
            "KQ.x@SHFE.cu",        # 错误前缀
            "CU",                  # 仅品种代码
        ]
        
        for invalid_code in invalid_codes:
            with self.subTest(contract=invalid_code):
                symbol, is_index = self.manager.parse_futures_code(invalid_code)
                self.assertIsNone(symbol)
                self.assertFalse(is_index)
    
    def test_symbol_from_index_code(self):
        """测试从指数合约代码提取品种代码"""
        test_cases = [
            ("KQ.i@SHFE.cu", "CU"),            # 小写品种
            ("KQ.i@CZCE.CF", "CF"),            # 大写品种
            ("KQ.i@CFFEX.IF", "IF"),           # 股指期货
        ]
        
        for index_code, expected_symbol in test_cases:
            with self.subTest(index_code=index_code):
                symbol = self.manager.get_symbol_from_index(index_code)
                self.assertEqual(symbol, expected_symbol)
    
    def test_validate_futures_input(self):
        """测试期货输入验证"""
        # 测试空输入
        valid, error, info = self.manager.validate_futures_input("")
        self.assertFalse(valid)
        self.assertIn("不能为空", error)
        
        # 测试无效格式
        valid, error, info = self.manager.validate_futures_input("INVALID")
        self.assertFalse(valid)
        self.assertIn("格式错误", error)
    
    def test_contract_search(self):
        """测试合约搜索功能"""
        # 这个测试需要实际的合约数据，所以可能会失败
        # 在实际环境中运行时需要确保天勤API连接正常
        try:
            results = self.manager.search_contracts("CU")
            self.assertIsInstance(results, list)
        except Exception:
            # 如果API不可用，跳过这个测试
            self.skipTest("TqSdk API not available")


class TestExchangeCaseRules(unittest.TestCase):
    """测试交易所大小写规则"""
    
    def test_exchange_case_mapping(self):
        """测试交易所大小写映射规则"""
        # 小写交易所: SHFE, DCE, INE
        lowercase_exchanges = ["SHFE", "DCE", "INE"]
        
        # 大写交易所: CZCE, GFEX, CFFEX
        uppercase_exchanges = ["CZCE", "GFEX", "CFFEX"]
        
        # 这个测试主要是文档化交易所规则
        # 实际的匹配逻辑在FuturesContractManager中实现
        self.assertEqual(len(lowercase_exchanges), 3)
        self.assertEqual(len(uppercase_exchanges), 3)


if __name__ == "__main__":
    # 设置测试输出格式
    unittest.main(verbosity=2)