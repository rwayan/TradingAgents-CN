#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
期货股票关联工具使用示例
演示如何使用FuturesStockCorrelation类进行各种查询操作
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from tradingagents.dataflows.futures_stock_correlation import (
    FuturesStockCorrelation,
    get_related_stocks,
    get_related_futures
)


def example_basic_usage():
    """基本使用示例"""
    print("=== 基本使用示例 ===")
    
    # 创建关联器实例
    correlator = FuturesStockCorrelation()
    
    # 获取数据
    print("正在获取数据...")
    if not correlator.fetch_data():
        print("❌ 数据获取失败，请检查网络连接")
        return
    
    print("✅ 数据获取成功")
    
    # 打印统计信息
    correlator.print_summary()


def example_future_to_stocks():
    """期货到股票查询示例"""
    print("\n=== 期货到股票查询示例 ===")
    
    correlator = FuturesStockCorrelation()
    if not correlator.fetch_data():
        return
    
    # 测试不同的期货品种
    test_futures = [
        "黄金", "铜", "铝", "螺纹钢", "原油", 
        "动力煤", "焦炭", "PTA", "甲醇", "天然橡胶"
    ]
    
    for future_name in test_futures:
        stocks = correlator.get_stocks_by_future(future_name)
        print(f"\n📈 {future_name} 相关股票 ({len(stocks)}只):")
        
        if stocks:
            for i, stock in enumerate(stocks[:8], 1):  # 只显示前8只
                print(f"  {i}. {stock.code} {stock.name}")
            if len(stocks) > 8:
                print(f"  ... 还有 {len(stocks) - 8} 只股票")
        else:
            print("  🔍 未找到相关股票")


def example_stock_to_futures():
    """股票到期货查询示例"""
    print("\n=== 股票到期货查询示例 ===")
    
    correlator = FuturesStockCorrelation()
    if not correlator.fetch_data():
        return
    
    # 测试不同的股票
    test_stocks = [
        "中国石油", "中国石化", "万华化学", "紫金矿业",
        "中国神华", "宝钢股份", "江西铜业", "山东黄金",
        "新希望", "中粮糖业", "北方稀土", "通威股份"
    ]
    
    for stock_name in test_stocks:
        futures = correlator.get_futures_by_stock(stock_name)
        print(f"📊 {stock_name} -> ", end="")
        
        if futures:
            print(f"关联期货: {', '.join(futures)}")
        else:
            print("🔍 未找到相关期货")


def example_search_functionality():
    """搜索功能示例"""
    print("\n=== 搜索功能示例 ===")
    
    correlator = FuturesStockCorrelation()
    if not correlator.fetch_data():
        return
    
    # 搜索期货
    search_keywords = ["煤", "油", "金", "铜"]
    
    for keyword in search_keywords:
        print(f"\n🔍 搜索包含'{keyword}'的期货:")
        results = correlator.search_futures(keyword)
        
        for name, category in results:
            print(f"  📈 {name} ({category})")
        
        if not results:
            print(f"  未找到包含'{keyword}'的期货")
    
    # 搜索股票
    print(f"\n🔍 搜索包含'中国'的股票:")
    stock_results = correlator.search_stocks("中国")
    
    for code, name in stock_results[:10]:  # 只显示前10个
        print(f"  📊 {code} {name}")
    
    if len(stock_results) > 10:
        print(f"  ... 还有 {len(stock_results) - 10} 只股票")


def example_category_analysis():
    """分类分析示例"""
    print("\n=== 分类分析示例 ===")
    
    correlator = FuturesStockCorrelation()
    if not correlator.fetch_data():
        return
    
    # 获取所有分类
    categories = correlator.get_all_categories()
    print(f"📋 共有 {len(categories)} 个期货分类:")
    
    for category in categories:
        futures_in_category = correlator.get_futures_by_category(category)
        print(f"\n🏷️  {category} ({len(futures_in_category)} 个品种):")
        
        for future_name in futures_in_category[:5]:  # 只显示前5个
            future_info = correlator.get_future_info(future_name)
            if future_info:
                change_symbol = "📈" if float(future_info.change_pct) >= 0 else "📉"
                print(f"  {change_symbol} {future_name}: {future_info.price} ({future_info.change_pct}%)")
        
        if len(futures_in_category) > 5:
            print(f"  ... 还有 {len(futures_in_category) - 5} 个品种")


def example_price_analysis():
    """价格分析示例"""
    print("\n=== 价格分析示例 ===")
    
    correlator = FuturesStockCorrelation()
    if not correlator.fetch_data():
        return
    
    # 分析涨跌幅
    rising_futures = []
    falling_futures = []
    
    for name, info in correlator.futures_data.items():
        try:
            change_pct = float(info.change_pct)
            if change_pct > 0:
                rising_futures.append((name, change_pct, info.category))
            elif change_pct < 0:
                falling_futures.append((name, change_pct, info.category))
        except ValueError:
            continue
    
    # 排序
    rising_futures.sort(key=lambda x: x[1], reverse=True)
    falling_futures.sort(key=lambda x: x[1])
    
    print(f"📈 涨幅最大的期货 (前10名):")
    for i, (name, change, category) in enumerate(rising_futures[:10], 1):
        print(f"  {i}. {name} (+{change}%) - {category}")
    
    print(f"\n📉 跌幅最大的期货 (前10名):")
    for i, (name, change, category) in enumerate(falling_futures[:10], 1):
        print(f"  {i}. {name} ({change}%) - {category}")


def example_investment_analysis():
    """投资分析示例"""
    print("\n=== 投资分析示例 ===")
    
    correlator = FuturesStockCorrelation()
    if not correlator.fetch_data():
        return
    
    # 找出关联股票最多的期货品种
    future_stock_counts = []
    for name, info in correlator.futures_data.items():
        future_stock_counts.append((name, len(info.related_stocks), info.category))
    
    future_stock_counts.sort(key=lambda x: x[1], reverse=True)
    
    print("🏆 关联股票最多的期货品种 (前10名):")
    for i, (name, count, category) in enumerate(future_stock_counts[:10], 1):
        print(f"  {i}. {name}: {count}只股票 - {category}")
    
    # 找出关联期货最多的股票
    stock_future_counts = []
    for stock_name, futures in correlator.stock_to_futures.items():
        stock_future_counts.append((stock_name, len(futures)))
    
    stock_future_counts.sort(key=lambda x: x[1], reverse=True)
    
    print(f"\n🏆 关联期货最多的股票 (前10名):")
    for i, (name, count) in enumerate(stock_future_counts[:10], 1):
        futures = correlator.get_futures_by_stock(name)
        print(f"  {i}. {name}: {count}个期货 - {', '.join(futures[:3])}{'...' if len(futures) > 3 else ''}")


def example_convenience_functions():
    """便利函数使用示例"""
    print("\n=== 便利函数使用示例 ===")
    
    # 使用便利函数进行快速查询
    print("📈 使用便利函数查询期货相关股票:")
    test_futures = ["黄金", "铜", "螺纹钢"]
    
    for future_name in test_futures:
        try:
            stocks = get_related_stocks(future_name)
            print(f"  {future_name}: {len(stocks)}只相关股票")
            for stock in stocks[:3]:  # 只显示前3只
                print(f"    📊 {stock.code} {stock.name}")
            if len(stocks) > 3:
                print(f"    ... 还有{len(stocks)-3}只")
        except Exception as e:
            print(f"  {future_name}: 查询失败 - {e}")
    
    print("\n📊 使用便利函数查询股票相关期货:")
    test_stocks = ["中国石油", "万华化学", "紫金矿业"]
    
    for stock_name in test_stocks:
        try:
            futures = get_related_futures(stock_name)
            if futures:
                print(f"  {stock_name}: {', '.join(futures)}")
            else:
                print(f"  {stock_name}: 未找到相关期货")
        except Exception as e:
            print(f"  {stock_name}: 查询失败 - {e}")


def example_interactive_query():
    """交互式查询示例"""
    print("\n=== 交互式查询示例 ===")
    
    correlator = FuturesStockCorrelation()
    if not correlator.fetch_data():
        return
    
    print("💡 交互式查询已启动，输入 'quit' 退出")
    print("📝 支持的命令:")
    print("  - 期货名称: 查询相关股票")
    print("  - 股票名称: 查询相关期货") 
    print("  - search <关键词>: 搜索期货和股票")
    print("  - categories: 显示所有分类")
    print("  - help: 显示帮助信息")
    
    while True:
        try:
            query = input("\n🔍 请输入查询内容: ").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                print("👋 再见!")
                break
            
            if query.lower() == 'help':
                print("📝 支持的命令:")
                print("  - 期货名称: 查询相关股票")
                print("  - 股票名称: 查询相关期货") 
                print("  - search <关键词>: 搜索期货和股票")
                print("  - categories: 显示所有分类")
                continue
            
            if query.lower() == 'categories':
                categories = correlator.get_all_categories()
                print(f"📋 期货分类: {', '.join(categories)}")
                continue
            
            if query.lower().startswith('search '):
                keyword = query[7:].strip()
                if keyword:
                    future_results = correlator.search_futures(keyword)
                    stock_results = correlator.search_stocks(keyword)
                    
                    print(f"📈 期货搜索结果 ({len(future_results)}个):")
                    for name, category in future_results[:5]:
                        print(f"  {name} ({category})")
                    
                    print(f"📊 股票搜索结果 ({len(stock_results)}个):")
                    for code, name in stock_results[:5]:
                        print(f"  {code} {name}")
                continue
            
            # 尝试作为期货查询
            stocks = correlator.get_stocks_by_future(query)
            if stocks:
                print(f"📈 {query} 相关股票 ({len(stocks)}只):")
                for stock in stocks[:10]:
                    print(f"  📊 {stock.code} {stock.name}")
                continue
            
            # 尝试作为股票查询
            futures = correlator.get_futures_by_stock(query)
            if futures:
                print(f"📊 {query} 相关期货: {', '.join(futures)}")
                continue
            
            print(f"❌ 未找到与'{query}'相关的信息")
            
        except KeyboardInterrupt:
            print("\n👋 再见!")
            break
        except Exception as e:
            print(f"❌ 查询出错: {e}")


def main():
    """主函数"""
    print("🚀 期货股票关联工具示例程序")
    print("=" * 50)
    
    # 运行各种示例
    try:
        example_basic_usage()
        example_future_to_stocks()
        example_stock_to_futures()
        example_search_functionality()
        example_category_analysis()
        example_price_analysis()
        example_investment_analysis()
        example_convenience_functions()
        
        # 可选的交互式查询
        print("\n" + "=" * 50)
        response = input("是否启动交互式查询? (y/n): ").strip().lower()
        if response in ['y', 'yes', '是']:
            example_interactive_query()
        
    except KeyboardInterrupt:
        print("\n👋 程序已终止")
    except Exception as e:
        print(f"❌ 程序运行出错: {e}")


if __name__ == "__main__":
    main()