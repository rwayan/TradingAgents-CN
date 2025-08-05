#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
期货与股票关联查询工具
从东方财富网获取期货相关股票数据，实现双向查询功能
支持期货合约代码与股票代码的双向映射
"""

import re
import json
import requests
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass
import time

# 导入统一日志系统
from tradingagents.utils.logging_init import setup_dataflow_logging
logger = setup_dataflow_logging()

# 导入期货合约映射
from tradingagents.utils.future_helper import FUTURES_NAME_MAPPING, FUTURES_CODE_MAPPING, get_futures_product

@dataclass
class StockInfo:
    """股票信息"""
    code: str
    name: str


@dataclass
class FutureInfo:
    """期货信息"""
    name: str
    category: str
    price: str
    change_pct: str
    related_stocks: List[StockInfo]


class FuturesStockCorrelation:
    """期货股票关联查询器"""
    
    def __init__(self):
        self.futures_data: Dict[str, FutureInfo] = {}
        self.stock_to_futures: Dict[str, List[str]] = {}
        self.last_update_time = 0
        self.cache_duration = 360000  # 缓存1小时
        
    def fetch_data(self) -> bool:
        """
        从东方财富网获取期货相关股票数据
        
        Returns:
            bool: 获取成功返回True，失败返回False
        """
        url = "https://data.eastmoney.com/ifdata/xhgp.html"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # 提取pagedata变量的内容
            pattern = r'var\s+pagedata\s*=\s*(\{.*?\});'
            match = re.search(pattern, response.text, re.DOTALL)
            
            if not match:
                logger.warning("未能找到pagedata变量")
                return False
                
            pagedata_str = match.group(1)
            pagedata = json.loads(pagedata_str)
            
            # 解析数据
            self._parse_pagedata(pagedata)
            self.last_update_time = time.time()
            
            logger.info(f"数据获取成功，共获取 {len(self.futures_data)} 个期货品种")
            return True
            
        except requests.RequestException as e:
            logger.warning(f"网络请求失败: {e}")
            return False
        except json.JSONDecodeError as e:
            logger.warning(f"JSON解析失败: {e}")
            return False
        except Exception as e:
            logger.warning(f"数据获取失败: {e}")
            return False
    
    def _parse_pagedata(self, pagedata: dict):
        """
        解析pagedata数据
        
        Args:
            pagedata: 从网页解析得到的数据
        """
        self.futures_data.clear()
        self.stock_to_futures.clear()
        
        if 'datas' not in pagedata:
            return
        
        for category_data in pagedata['datas']:
            category_name = category_data.get('name', '')
            
            for item in category_data.get('list', []):
                future_name = item.get('name', '')
                if not future_name:
                    continue
                
                # 解析股票列表
                related_stocks = []
                for stock_data in item.get('scss', []):
                    stock_code = stock_data.get('code', '')
                    stock_name = stock_data.get('name', '')
                    if stock_code and stock_name:
                        stock_info = StockInfo(code=stock_code, name=stock_name)
                        related_stocks.append(stock_info)
                        
                        # 建立股票到期货的反向映射
                        if stock_name not in self.stock_to_futures:
                            self.stock_to_futures[stock_name] = []
                        if future_name not in self.stock_to_futures[stock_name]:
                            self.stock_to_futures[stock_name].append(future_name)
                
                # 创建期货信息对象
                future_info = FutureInfo(
                    name=future_name,
                    category=category_name,
                    price=item.get('price', ''),
                    change_pct=item.get('zdf', ''),
                    related_stocks=related_stocks
                )
                
                self.futures_data[future_name] = future_info
    
    def _ensure_data_fresh(self) -> bool:
        """
        确保数据是最新的
        
        Returns:
            bool: 数据获取成功返回True
        """
        current_time = time.time()
        if (current_time - self.last_update_time) > self.cache_duration:
            return self.fetch_data()
        return len(self.futures_data) > 0
    
    def get_stocks_by_future(self, future_name: str) -> List[StockInfo]:
        """
        根据期货品种名称获取相关股票
        
        Args:
            future_name: 期货品种名称
            
        Returns:
            List[StockInfo]: 相关股票列表
        """
        if not self._ensure_data_fresh():
            return []
        
        # 精确匹配
        if future_name in self.futures_data:
            return self.futures_data[future_name].related_stocks
        
        # 模糊匹配
        for name, info in self.futures_data.items():
            if future_name in name or name in future_name:
                return info.related_stocks
        
        return []
    
    def get_futures_by_stock(self, stock_name: str) -> List[str]:
        """
        根据股票名称获取相关期货品种
        
        Args:
            stock_name: 股票名称
            
        Returns:
            List[str]: 相关期货品种列表
        """
        if not self._ensure_data_fresh():
            return []
        
        # 精确匹配
        if stock_name in self.stock_to_futures:
            return self.stock_to_futures[stock_name]
        
        # 模糊匹配
        result = []
        for name, futures in self.stock_to_futures.items():
            if stock_name in name or name in stock_name:
                result.extend(futures)
        
        return list(set(result))  # 去重
    
    def search_futures(self, keyword: str) -> List[Tuple[str, str]]:
        """
        搜索期货品种
        
        Args:
            keyword: 搜索关键词
            
        Returns:
            List[Tuple[str, str]]: (期货名称, 分类) 的列表
        """
        if not self._ensure_data_fresh():
            return []
        
        results = []
        keyword = keyword.lower()
        
        for name, info in self.futures_data.items():
            if keyword in name.lower() or keyword in info.category.lower():
                results.append((name, info.category))
        
        return results
    
    def search_stocks(self, keyword: str) -> List[Tuple[str, str]]:
        """
        搜索股票
        
        Args:
            keyword: 搜索关键词
            
        Returns:
            List[Tuple[str, str]]: (股票代码, 股票名称) 的列表
        """
        if not self._ensure_data_fresh():
            return []
        
        results = set()
        keyword = keyword.lower()
        
        for future_info in self.futures_data.values():
            for stock in future_info.related_stocks:
                if (keyword in stock.name.lower() or 
                    keyword in stock.code.lower()):
                    results.add((stock.code, stock.name))
        
        return list(results)
    
    def get_future_info(self, future_name: str) -> Optional[FutureInfo]:
        """
        获取期货详细信息
        
        Args:
            future_name: 期货品种名称
            
        Returns:
            Optional[FutureInfo]: 期货信息，未找到返回None
        """
        if not self._ensure_data_fresh():
            return None
        
        return self.futures_data.get(future_name)
    
    def get_all_categories(self) -> List[str]:
        """
        获取所有期货分类
        
        Returns:
            List[str]: 分类列表
        """
        if not self._ensure_data_fresh():
            return []
        
        categories = set()
        for info in self.futures_data.values():
            categories.add(info.category)
        
        return list(categories)
    
    def get_futures_by_category(self, category: str) -> List[str]:
        """
        根据分类获取期货品种
        
        Args:
            category: 分类名称
            
        Returns:
            List[str]: 期货品种列表
        """
        if not self._ensure_data_fresh():
            return []
        
        result = []
        for name, info in self.futures_data.items():
            if info.category == category:
                result.append(name)
        
        return result
    
    def get_stocks_by_contract_code(self, contract_code: str) -> List[StockInfo]:
        """
        根据期货合约代码获取相关股票
        
        Args:
            contract_code: 期货合约代码，如 "CU2501", "AU99" 等
            
        Returns:
            List[StockInfo]: 相关股票列表
        """
        if not self._ensure_data_fresh():
            return []
        
        # 提取品种代码
        underlying = get_futures_product(contract_code)
        if not underlying:
            logger.warning(f"无法解析期货合约代码: {contract_code}")
            return []
        
        # 获取期货名称
        future_name = FUTURES_NAME_MAPPING.get(underlying)
        if not future_name:
            logger.warning(f"未找到期货品种: {underlying}")
            return []
        
        # 使用现有方法查询相关股票
        return self.get_stocks_by_future(future_name)
    
    def get_contract_codes_by_stock_name(self, stock_name: str) -> List[str]:
        """
        根据股票名称获取相关期货合约代码
        
        Args:
            stock_name: 股票名称
            
        Returns:
            List[str]: 相关期货合约代码列表
        """
        if not self._ensure_data_fresh():
            return []
        
        # 获取相关期货品种名称
        future_names = self.get_futures_by_stock(stock_name)
        if not future_names:
            return []
        
        # 将期货名称转换为合约代码
        contract_codes = []
        for future_name in future_names:
            contract_code = FUTURES_CODE_MAPPING.get(future_name)
            if contract_code:
                contract_codes.append(contract_code)
            else:
                # 尝试模糊匹配
                for name, code in FUTURES_CODE_MAPPING.items():
                    if future_name in name or name in future_name:
                        contract_codes.append(code)
                        break
        
        return list(set(contract_codes))  # 去重
    
    def get_contract_codes_by_stock_code(self, stock_code: str) -> List[str]:
        """
        根据股票代码获取相关期货合约代码
        
        Args:
            stock_code: 股票代码，如 "600362"
            
        Returns:
            List[str]: 相关期货合约代码列表
        """
        if not self._ensure_data_fresh():
            return []
        
        # 通过股票代码找到股票名称
        stock_name = None
        for future_info in self.futures_data.values():
            for stock in future_info.related_stocks:
                if stock.code == stock_code:
                    stock_name = stock.name
                    break
            if stock_name:
                break
        
        if not stock_name:
            logger.warning(f"未找到股票代码对应的股票名称: {stock_code}")
            return []
        
        # 使用股票名称查询合约代码
        return self.get_contract_codes_by_stock_name(stock_name)
    
    def print_summary(self):
        """打印数据统计摘要"""
        if not self._ensure_data_fresh():
            logger.warning("无法获取数据")
            return
        
        logger.info(f"\n=== 期货股票关联数据统计 ===")
        logger.info(f"期货品种总数: {len(self.futures_data)}")
        logger.info(f"涉及股票总数: {len(self.stock_to_futures)}")
        logger.info(f"数据更新时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.last_update_time))}")
        
        logger.info(f"\n=== 分类统计 ===")
        categories = {}
        for info in self.futures_data.values():
            categories[info.category] = categories.get(info.category, 0) + 1
        
        for category, count in categories.items():
            logger.info(f"{category}: {count} 个品种")


# 便利函数，供外部直接调用
def get_related_stocks(future_name: str) -> List[StockInfo]:
    """
    便利函数：根据期货品种获取相关股票
    
    Args:
        future_name: 期货品种名称
        
    Returns:
        List[StockInfo]: 相关股票列表
    """
    correlator = FuturesStockCorrelation()
    return correlator.get_stocks_by_future(future_name)


def get_related_futures(stock_name: str) -> List[str]:
    """
    便利函数：根据股票名称获取相关期货
    
    Args:
        stock_name: 股票名称
        
    Returns:
        List[str]: 相关期货品种列表
    """
    correlator = FuturesStockCorrelation()
    return correlator.get_futures_by_stock(stock_name)


def get_stocks_by_contract(contract_code: str) -> List[StockInfo]:
    """
    便利函数：根据期货合约代码获取相关股票
    
    Args:
        contract_code: 期货合约代码，如 "CU2501", "AU99" 等
        
    Returns:
        List[StockInfo]: 相关股票列表
    """
    correlator = FuturesStockCorrelation()
    return correlator.get_stocks_by_contract_code(contract_code)


def get_contracts_by_stock_code(stock_code: str) -> List[str]:
    """
    便利函数：根据股票代码获取相关期货合约代码
    
    Args:
        stock_code: 股票代码，如 "600362"
        
    Returns:
        List[str]: 相关期货合约代码列表
    """
    correlator = FuturesStockCorrelation()
    return correlator.get_contract_codes_by_stock_code(stock_code)


def get_contracts_by_stock_name(stock_name: str) -> List[str]:
    """
    便利函数：根据股票名称获取相关期货合约代码
    
    Args:
        stock_name: 股票名称
        
    Returns:
        List[str]: 相关期货合约代码列表
    """
    correlator = FuturesStockCorrelation()
    return correlator.get_contract_codes_by_stock_name(stock_name)


def main():
    """主函数，演示用法"""
    correlator = FuturesStockCorrelation()
    
    # 获取数据
    print("正在获取数据...")
    if not correlator.fetch_data():
        print("数据获取失败")
        return
    
    # 打印统计信息
    correlator.print_summary()
    
    print("\n=== 使用示例 ===")
    
    # 示例1：根据期货品种查找相关股票
    print("\n1. 根据期货品种查找相关股票:")
    test_futures = ["炼焦煤", "黄金", "铜"]
    for future_name in test_futures:
        stocks = correlator.get_stocks_by_future(future_name)
        if stocks:
            print(f"{future_name} -> {len(stocks)}只股票:")
            for stock in stocks[:5]:  # 只显示前5只
                print(f"  {stock.code} {stock.name}")
            if len(stocks) > 5:
                print(f"  ... 还有{len(stocks)-5}只股票")
        else:
            print(f"{future_name} -> 未找到相关股票")
    
    # 示例2：根据股票名称查找相关期货
    print("\n2. 根据股票名称查找相关期货:")
    test_stocks = ["中国石油", "万华化学", "紫金矿业"]
    for stock_name in test_stocks:
        futures = correlator.get_futures_by_stock(stock_name)
        if futures:
            print(f"{stock_name} -> 相关期货: {', '.join(futures)}")
        else:
            print(f"{stock_name} -> 未找到相关期货")
    
    # 示例3：根据期货合约代码查找相关股票
    print("\n3. 根据期货合约代码查找相关股票:")
    test_contracts = ["CU2501", "AU2412", "RB2505"]
    for contract_code in test_contracts:
        stocks = correlator.get_stocks_by_contract_code(contract_code)
        if stocks:
            print(f"{contract_code} -> {len(stocks)}只股票:")
            for stock in stocks[:3]:  # 只显示前3只
                print(f"  {stock.code} {stock.name}")
            if len(stocks) > 3:
                print(f"  ... 还有{len(stocks)-3}只股票")
        else:
            print(f"{contract_code} -> 未找到相关股票")
    
    # 示例4：根据股票代码查找相关期货合约
    print("\n4. 根据股票代码查找相关期货合约:")
    test_stock_codes = ["600362", "600309", "601899"]
    for stock_code in test_stock_codes:
        contracts = correlator.get_contract_codes_by_stock_code(stock_code)
        if contracts:
            print(f"{stock_code} -> 相关期货合约: {', '.join(contracts)}")
        else:
            print(f"{stock_code} -> 未找到相关期货合约")
    
    # 示例5：搜索功能
    print("\n5. 搜索功能演示:")
    search_results = correlator.search_futures("煤")
    print(f"搜索'煤'相关期货: {len(search_results)}个结果")
    for name, category in search_results:
        print(f"  {name} ({category})")


if __name__ == "__main__":
    main()