#!/usr/bin/env python3
"""
期货数据验证功能测试

测试期货代码格式验证、市场类型检测和数据准备功能
"""

import sys
import os
import unittest
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tradingagents.utils.stock_validator import StockDataPreparer


class TestFuturesDataValidation(unittest.TestCase):
    """期货数据验证测试类"""
    
    def setUp(self):
        """设置测试环境"""
        self.preparer = StockDataPreparer()
    
    def test_futures_market_type_detection(self):
        """测试期货市场类型自动检测"""
        test_cases = [
            # 指数合约格式
            ("CU99", "期货"),
            ("IF99", "期货"),
            ("RB99", "期货"),
            ("AL99", "期货"),
            ("SC99", "期货"),
            
            # 具体合约格式
            ("CU2403", "期货"),
            ("IF2403", "期货"),
            ("RB2403", "期货"),
            ("AL2403", "期货"),
            
            # 非期货代码
            ("AAPL", "美股"),
            ("000001", "A股"),
            ("0700", "港股"),
            ("INVALID", "未知"),
        ]
        
        for code, expected_market in test_cases:
            with self.subTest(code=code):
                detected_market = self.preparer._detect_market_type(code)
                self.assertEqual(detected_market, expected_market,
                               f"代码 {code} 应该被识别为 {expected_market}，但被识别为 {detected_market}")
    
    def test_futures_format_validation(self):
        """测试期货代码格式验证"""
        # 有效的期货代码
        valid_codes = [
            "CU99", "IF99", "RB99", "AL99", "SC99",  # 指数合约
            "CU2403", "IF2403", "RB2403", "AL2403"   # 具体合约
        ]
        
        for code in valid_codes:
            with self.subTest(code=code):
                result = self.preparer._validate_format(code, "期货")
                self.assertTrue(result.is_valid, 
                              f"期货代码 {code} 应该通过格式验证，但失败了: {result.error_message}")
                self.assertEqual(result.market_type, "期货")
        
        # 无效的期货代码
        invalid_codes = [
            "INVALID", "123456", "ABC", "CU", "TOOLONG99", "CU9", "CU999"
        ]
        
        for code in invalid_codes:
            with self.subTest(code=code):
                result = self.preparer._validate_format(code, "期货")
                self.assertFalse(result.is_valid,
                               f"期货代码 {code} 应该格式验证失败，但通过了")
                self.assertIn("期货代码格式错误", result.error_message)
    
    def test_futures_data_preparation_workflow(self):
        """测试期货数据准备完整流程"""
        test_codes = ["CU99", "IF99", "RB99"]
        
        for code in test_codes:
            with self.subTest(code=code):
                # 使用较短的时间段避免实际数据获取
                result = self.preparer.prepare_stock_data(code, market_type="auto", period_days=7)
                
                # 验证基本属性
                self.assertEqual(result.stock_code, code.upper())
                self.assertEqual(result.market_type, "期货")
                
                # 由于期货数据模块可能未配置，我们主要验证格式验证和市场检测
                if not result.is_valid:
                    # 如果失败，应该是因为数据模块未配置，而不是格式错误
                    self.assertIn("期货数据模块", result.error_message)
    
    def test_futures_auto_market_detection(self):
        """测试期货代码的自动市场类型检测"""
        test_cases = [
            "CU99", "IF99", "RB99", "CU2403", "IF2403"
        ]
        
        for code in test_cases:
            with self.subTest(code=code):
                result = self.preparer.prepare_stock_data(code, market_type="auto", period_days=7)
                self.assertEqual(result.market_type, "期货",
                               f"代码 {code} 应该被自动识别为期货市场类型")
    
    def test_futures_error_handling(self):
        """测试期货验证的错误处理"""
        # 测试无效格式
        invalid_result = self.preparer.prepare_stock_data("INVALID", market_type="期货", period_days=7)
        self.assertFalse(invalid_result.is_valid)
        self.assertIn("期货代码格式错误", invalid_result.error_message)
        
        # 测试空代码
        empty_result = self.preparer.prepare_stock_data("", market_type="期货", period_days=7)
        self.assertFalse(empty_result.is_valid)
        self.assertIn("不能为空", empty_result.error_message)
    
    def test_futures_suggestion_messages(self):
        """测试期货验证的建议消息"""
        result = self.preparer.prepare_stock_data("INVALID", market_type="期货", period_days=7)
        self.assertFalse(result.is_valid)
        self.assertIn("CU99", result.suggestion)  # 应该包含示例代码
        self.assertIn("CU2403", result.suggestion)  # 应该包含示例代码


class TestFuturesValidationIntegration(unittest.TestCase):
    """期货验证集成测试"""
    
    def test_market_type_consistency(self):
        """测试市场类型检测的一致性"""
        preparer = StockDataPreparer()
        
        # 测试各种期货代码格式
        futures_codes = [
            "CU99", "cu99", "Cu99",  # 大小写测试
            "IF99", "RB99", "AL99",  # 不同品种
            "CU2403", "IF2412", "RB2506"  # 具体合约
        ]
        
        for code in futures_codes:
            with self.subTest(code=code):
                # 检测市场类型
                detected = preparer._detect_market_type(code)
                self.assertEqual(detected, "期货")
                
                # 格式验证
                format_result = preparer._validate_format(code, "期货")
                self.assertTrue(format_result.is_valid)
                
                # 自动检测模式
                auto_result = preparer.prepare_stock_data(code, market_type="auto", period_days=7)
                self.assertEqual(auto_result.market_type, "期货")


def run_futures_validation_tests():
    """运行期货验证测试套件"""
    # 创建测试套件
    suite = unittest.TestSuite()
    
    # 添加测试类
    suite.addTest(unittest.makeSuite(TestFuturesDataValidation))
    suite.addTest(unittest.makeSuite(TestFuturesValidationIntegration))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    print("=== 期货数据验证功能测试 ===")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    success = run_futures_validation_tests()
    
    print()
    if success:
        print("✅ 所有测试通过！期货验证功能正常。")
    else:
        print("❌ 部分测试失败，请检查期货验证功能。")
        sys.exit(1)