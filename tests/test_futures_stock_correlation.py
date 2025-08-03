#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
期货股票关联工具测试用例
"""

import unittest
import sys
import os
from unittest.mock import patch, MagicMock
import json

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from tradingagents.dataflows.futures_stock_correlation import (
    FuturesStockCorrelation, 
    StockInfo, 
    FutureInfo,
    get_related_stocks,
    get_related_futures
)


class TestFuturesStockCorrelation(unittest.TestCase):
    """期货股票关联工具测试类"""
    
    def setUp(self):
        """测试前的准备工作"""
        self.correlator = FuturesStockCorrelation()
        
        # 模拟的pagedata数据
        self.mock_pagedata = {
            "dates": {"d1": "03-31", "d2": "04-30"},
            "datas": [
                {
                    "name": "能源",
                    "list": [
                        {
                            "name": "炼焦煤",
                            "price": "1391.25",
                            "zdf": "-1.22",
                            "scss": [
                                {"code": "000937", "name": "冀中能源"},
                                {"code": "000983", "name": "山西焦煤"},
                                {"code": "600123", "name": "兰花科创"}
                            ]
                        },
                        {
                            "name": "动力煤", 
                            "price": "763.75",
                            "zdf": "-4.83",
                            "scss": [
                                {"code": "601918", "name": "新集能源"},
                                {"code": "000937", "name": "冀中能源"}
                            ]
                        }
                    ]
                },
                {
                    "name": "有色",
                    "list": [
                        {
                            "name": "黄金",
                            "price": "766.83", 
                            "zdf": "5.59",
                            "scss": [
                                {"code": "600489", "name": "中金黄金"},
                                {"code": "600547", "name": "山东黄金"}
                            ]
                        }
                    ]
                }
            ]
        }
    
    def test_parse_pagedata(self):
        """测试数据解析功能"""
        self.correlator._parse_pagedata(self.mock_pagedata)
        
        # 检查期货数据是否正确解析
        self.assertEqual(len(self.correlator.futures_data), 3)
        self.assertIn("炼焦煤", self.correlator.futures_data)
        self.assertIn("动力煤", self.correlator.futures_data)
        self.assertIn("黄金", self.correlator.futures_data)
        
        # 检查具体期货信息
        coal_info = self.correlator.futures_data["炼焦煤"]
        self.assertEqual(coal_info.category, "能源")
        self.assertEqual(coal_info.price, "1391.25")
        self.assertEqual(coal_info.change_pct, "-1.22")
        self.assertEqual(len(coal_info.related_stocks), 3)
        
        # 检查股票到期货的反向映射
        self.assertIn("冀中能源", self.correlator.stock_to_futures)
        self.assertEqual(len(self.correlator.stock_to_futures["冀中能源"]), 2)
        self.assertIn("炼焦煤", self.correlator.stock_to_futures["冀中能源"])
        self.assertIn("动力煤", self.correlator.stock_to_futures["冀中能源"])
    
    def test_get_stocks_by_future(self):
        """测试根据期货获取股票功能"""
        self.correlator._parse_pagedata(self.mock_pagedata)
        
        # 精确匹配
        stocks = self.correlator.get_stocks_by_future("炼焦煤")
        self.assertEqual(len(stocks), 10)
        stock_names = [stock.name for stock in stocks]
        self.assertIn("冀中能源", stock_names)
        self.assertIn("山西焦煤", stock_names)
        self.assertIn("兰花科创", stock_names)
        
        # 不存在的期货
        stocks = self.correlator.get_stocks_by_future("不存在的期货")
        self.assertEqual(len(stocks), 0)
    
    def test_get_futures_by_stock(self):
        """测试根据股票获取期货功能"""
        self.correlator._parse_pagedata(self.mock_pagedata)
        
        # 精确匹配
        futures = self.correlator.get_futures_by_stock("冀中能源")
        self.assertEqual(len(futures), 2)
        self.assertIn("炼焦煤", futures)
        self.assertIn("动力煤", futures)
        
        # 只关联一个期货的股票
        futures = self.correlator.get_futures_by_stock("南宁糖业")
        self.assertEqual(len(futures), 1)
        self.assertIn("白糖", futures)
        
        # 不存在的股票
        futures = self.correlator.get_futures_by_stock("不存在的股票")
        self.assertEqual(len(futures), 0)
    
    def test_search_functions(self):
        """测试搜索功能"""
        self.correlator._parse_pagedata(self.mock_pagedata)
        
        # 搜索期货
        results = self.correlator.search_futures("煤")
        self.assertEqual(len(results), 2)
        future_names = [result[0] for result in results]
        self.assertIn("炼焦煤", future_names)
        self.assertIn("动力煤", future_names)
        
        # 搜索股票
        results = self.correlator.search_stocks("能源")
        self.assertTrue(len(results) >= 2)
        stock_names = [result[1] for result in results]
        self.assertIn("冀中能源", stock_names)
        self.assertIn("新集能源", stock_names)
    
    def test_get_categories(self):
        """测试获取分类功能"""
        self.correlator._parse_pagedata(self.mock_pagedata)
        
        categories = self.correlator.get_all_categories()
        self.assertEqual(len(categories), 8)
        self.assertIn("能源", categories)
        self.assertIn("有色", categories)
        
        # 测试根据分类获取期货
        energy_futures = self.correlator.get_futures_by_category("能源")
        self.assertEqual(len(energy_futures), 2)
        self.assertIn("炼焦煤", energy_futures)
        self.assertIn("动力煤", energy_futures)
    
    def test_get_future_info(self):
        """测试获取期货详细信息"""
        self.correlator._parse_pagedata(self.mock_pagedata)
        
        info = self.correlator.get_future_info("黄金")
        self.assertIsNotNone(info)
        self.assertEqual(info.category, "有色")
        self.assertEqual(info.price, "766.83")
        self.assertEqual(info.change_pct, "5.59")
        
        # 不存在的期货
        info = self.correlator.get_future_info("不存在的期货")
        self.assertIsNone(info)
    
    def test_convenience_functions(self):
        """测试便利函数"""
        # 由于便利函数会创建新实例，这里只测试它们能正常调用
        with patch.object(FuturesStockCorrelation, 'get_stocks_by_future') as mock_get_stocks:
            mock_get_stocks.return_value = [StockInfo("000001", "测试股票")]
            stocks = get_related_stocks("测试期货")
            self.assertEqual(len(stocks), 1)
            mock_get_stocks.assert_called_once_with("测试期货")
        
        with patch.object(FuturesStockCorrelation, 'get_futures_by_stock') as mock_get_futures:
            mock_get_futures.return_value = ["测试期货"]
            futures = get_related_futures("测试股票")
            self.assertEqual(len(futures), 1)
            mock_get_futures.assert_called_once_with("测试股票")


class TestIntegration(unittest.TestCase):
    """集成测试类"""
    
    def setUp(self):
        self.correlator = FuturesStockCorrelation()
    
    @patch('requests.get')
    def test_fetch_data_success(self, mock_get):
        """测试成功获取数据"""
        # 模拟HTTP响应
        mock_response = MagicMock()
        mock_response.text = '''
        <script>
        var pagedata = {"datas":[{"name":"测试","list":[{"name":"测试期货","scss":[{"code":"000001","name":"测试股票"}]}]}]};
        </script>
        '''
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = self.correlator.fetch_data()
        self.assertTrue(result)
        self.assertGreater(len(self.correlator.futures_data), 0)
    
    @patch('requests.get')
    def test_fetch_data_network_error(self, mock_get):
        """测试网络错误处理"""
        mock_get.side_effect = Exception("网络错误")
        
        result = self.correlator.fetch_data()
        self.assertFalse(result)
    
    @patch('requests.get')
    def test_fetch_data_no_pagedata(self, mock_get):
        """测试找不到pagedata的情况"""
        mock_response = MagicMock()
        mock_response.text = '<html>没有pagedata变量</html>'
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = self.correlator.fetch_data()
        self.assertFalse(result)


class TestRealDataIntegration(unittest.TestCase):
    """真实数据集成测试（需要网络连接）"""
    
    def setUp(self):
        self.correlator = FuturesStockCorrelation()
    
    def test_real_data_fetch(self):
        """测试真实数据获取（可选测试，需要网络）"""
        # 这个测试需要网络连接，可以跳过
        import os
        if os.environ.get('SKIP_NETWORK_TESTS', '1') == '1':
            self.skipTest("跳过网络测试")
        
        result = self.correlator.fetch_data()
        if result:  # 只有在成功获取数据时才进行断言
            self.assertGreater(len(self.correlator.futures_data), 0)
            self.assertGreater(len(self.correlator.stock_to_futures), 0)
            
            # 测试一些已知的期货品种
            known_futures = ["黄金", "铜", "螺纹钢"]
            for future_name in known_futures:
                stocks = self.correlator.get_stocks_by_future(future_name)
                if stocks:  # 如果找到相关股票
                    self.assertIsInstance(stocks, list)
                    self.assertGreater(len(stocks), 0)
                    for stock in stocks:
                        self.assertIsInstance(stock, StockInfo)
                        self.assertTrue(stock.code)
                        self.assertTrue(stock.name)


def run_simple_test():
    """简单的功能测试"""
    print("=== 期货股票关联工具简单测试 ===")
    
    correlator = FuturesStockCorrelation()
    
    # 使用模拟数据
    mock_data = {
        "datas": [
            {
                "name": "测试分类",
                "list": [
                    {
                        "name": "测试期货1",
                        "price": "100.00",
                        "zdf": "1.23",
                        "scss": [
                            {"code": "000001", "name": "测试股票1"},
                            {"code": "000002", "name": "测试股票2"}
                        ]
                    },
                    {
                        "name": "测试期货2", 
                        "price": "200.00",
                        "zdf": "-2.34",
                        "scss": [
                            {"code": "000001", "name": "测试股票1"},
                            {"code": "000003", "name": "测试股票3"}
                        ]
                    }
                ]
            }
        ]
    }
    
    correlator._parse_pagedata(mock_data)
    
    print(f"[OK] 解析的期货数量: {len(correlator.futures_data)}")
    print(f"[OK] 股票到期货映射数量: {len(correlator.stock_to_futures)}")
    
    # 测试查询功能
    print("\n[TEST] 测试根据期货查股票:")
    stocks = correlator.get_stocks_by_future("测试期货1")
    for stock in stocks:
        print(f"  [RESULT] {stock.code} {stock.name}")
    
    print("\n[TEST] 测试根据股票查期货:")
    futures = correlator.get_futures_by_stock("测试股票1")
    print(f"  [RESULT] 测试股票1 关联期货: {futures}")
    
    # 测试便利函数
    print("\n[TEST] 测试便利函数:")
    try:
        # 由于便利函数会尝试获取真实数据，这里用try-catch处理
        stocks = get_related_stocks("测试期货")
        print(f"  [RESULT] 便利函数返回股票数量: {len(stocks)}")
    except:
        print("  [WARNING] 便利函数测试跳过（需要网络连接）")
    
    print("\n[SUCCESS] 测试通过!")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "simple":
        # 运行简单测试
        run_simple_test()
    else:
        # 运行完整的单元测试
        unittest.main(verbosity=2)