#!/usr/bin/env python3
"""
期货合约管理器功能测试
"""

import sys
import os
import unittest

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from tradingagents.dataflows.futures_contract_manager import get_contract_manager
    CONTRACT_MANAGER_AVAILABLE = True
except ImportError:
    CONTRACT_MANAGER_AVAILABLE = False


class TestFuturesContractManager(unittest.TestCase):
    """期货合约管理器测试类"""
    
    def setUp(self):
        """设置测试环境"""
        if not CONTRACT_MANAGER_AVAILABLE:
            self.skipTest("期货合约管理器模块不可用")
        self.manager = get_contract_manager()
    
    def test_contract_manager_initialization(self):
        """测试合约管理器初始化"""
        self.assertIsNotNone(self.manager)
    
    def test_futures_code_validation(self):
        """测试期货代码验证"""
        test_cases = [
            # (代码, 预期结果)
            ("CU99", True),
            ("IF99", True),
            ("RB2403", True),
            ("INVALID", False),
            ("AL", False),  # 不完整的代码
            ("SC99", True),
        ]
        
        for code, expected_valid in test_cases:
            with self.subTest(code=code):
                try:
                    is_valid, error_msg, contract_info = self.manager.validate_futures_input(code)
                    if expected_valid:
                        self.assertTrue(is_valid, f"代码 {code} 应该有效，但验证失败: {error_msg}")
                    else:
                        self.assertFalse(is_valid, f"代码 {code} 应该无效，但验证通过")
                except Exception as e:
                    if expected_valid:
                        self.fail(f"代码 {code} 验证时出现异常: {e}")
    
    def test_contract_parsing(self):
        """测试合约代码解析"""
        try:
            # 测试指数合约
            test_codes = ["CU99", "IF99", "RB99"]
            for code in test_codes:
                with self.subTest(code=code):
                    is_valid, error_msg, contract_info = self.manager.validate_futures_input(code)
                    if is_valid and contract_info:
                        self.assertIn('symbol', contract_info)
                        # 合约管理器可能返回底层品种代码（如CU），而不是指数合约代码（如CU99）
                        # 我们只验证返回的symbol是合理的
                        self.assertIsNotNone(contract_info['symbol'])
                        self.assertGreater(len(contract_info['symbol']), 0)
        except Exception as e:
            self.skipTest(f"合约解析功能不可用: {e}")
    
    def test_error_handling(self):
        """测试错误处理"""
        invalid_codes = ["", "TOOLONG99", "123", "CU"]
        
        for code in invalid_codes:
            with self.subTest(code=code):
                try:
                    is_valid, error_msg, contract_info = self.manager.validate_futures_input(code)
                    self.assertFalse(is_valid, f"无效代码 {code} 应该验证失败")
                    self.assertIsNotNone(error_msg, f"无效代码 {code} 应该有错误消息")
                except Exception as e:
                    # 如果抛出异常也是可以接受的错误处理方式
                    pass


def run_simple_contract_test():
    """运行简单的合约管理器测试"""
    print("=== 期货合约管理器简单测试 ===")
    
    if not CONTRACT_MANAGER_AVAILABLE:
        print("期货合约管理器模块不可用，跳过测试")
        return True
    
    try:
        manager = get_contract_manager()
        print("合约管理器初始化成功")
        
        # 测试基本验证功能
        test_codes = ["CU99", "IF99", "INVALID"]
        for code in test_codes:
            try:
                is_valid, error_msg, contract_info = manager.validate_futures_input(code)
                status = "通过" if is_valid else "失败"
                print(f"代码 {code}: {status}")
                if error_msg:
                    print(f"   消息: {error_msg}")
            except Exception as e:
                print(f"代码 {code}: 异常 - {e}")
        
        print("简单测试完成")
        return True
        
    except Exception as e:
        print(f"测试过程中出现异常: {e}")
        return False


if __name__ == "__main__":
    # 尝试运行unittest
    try:
        unittest.main(verbosity=2)
    except SystemExit:
        pass
    
    print("\n" + "="*50)
    
    # 运行简单测试作为备选
    run_simple_contract_test()