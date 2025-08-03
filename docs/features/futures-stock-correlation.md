# 期货股票关联查询工具

## 概述

这个工具可以帮助你查询期货品种与相关股票之间的关联关系，数据来源于东方财富网。支持双向查询：
- 根据期货品种名称，查找相关股票
- 根据股票名称，查找相关期货品种

## 功能特性

- ✅ **双向查询**: 期货→股票，股票→期货
- ✅ **实时数据**: 从东方财富网获取最新数据
- ✅ **智能搜索**: 支持模糊匹配和关键词搜索  
- ✅ **分类浏览**: 按期货分类（能源、有色、化工等）查看
- ✅ **价格分析**: 查看期货价格和涨跌幅
- ✅ **缓存机制**: 1小时数据缓存，提高查询效率

## 安装和使用

### 基本用法

```python
from tradingagents.dataflows.futures_stock_correlation import FuturesStockCorrelation

# 创建查询器
correlator = FuturesStockCorrelation()

# 获取数据（首次使用需要）
correlator.fetch_data()

# 根据期货查找股票
stocks = correlator.get_stocks_by_future("黄金")
for stock in stocks:
    print(f"{stock.code} {stock.name}")

# 根据股票查找期货
futures = correlator.get_futures_by_stock("中国石油")
print(f"相关期货: {', '.join(futures)}")
```

### 便利函数

```python
from tradingagents.dataflows.futures_stock_correlation import get_related_stocks, get_related_futures

# 快速查询（自动处理数据获取）
stocks = get_related_stocks("黄金")
futures = get_related_futures("中国石油")
```

## API 参考

### FuturesStockCorrelation 类

#### 核心方法

- `fetch_data()` - 获取最新数据
- `get_stocks_by_future(future_name)` - 根据期货获取相关股票
- `get_futures_by_stock(stock_name)` - 根据股票获取相关期货
- `search_futures(keyword)` - 搜索期货品种
- `search_stocks(keyword)` - 搜索股票
- `get_future_info(future_name)` - 获取期货详细信息

#### 分析方法

- `get_all_categories()` - 获取所有期货分类
- `get_futures_by_category(category)` - 根据分类获取期货
- `print_summary()` - 打印数据统计

### 数据结构

#### StockInfo
```python
@dataclass
class StockInfo:
    code: str    # 股票代码
    name: str    # 股票名称
```

#### FutureInfo  
```python
@dataclass
class FutureInfo:
    name: str                    # 期货名称
    category: str               # 分类
    price: str                  # 价格
    change_pct: str            # 涨跌幅
    related_stocks: List[StockInfo]  # 相关股票
```

## 示例代码

### 1. 基本查询示例

```python
correlator = FuturesStockCorrelation()
correlator.fetch_data()

# 查询黄金相关股票
stocks = correlator.get_stocks_by_future("黄金")
print(f"黄金相关股票({len(stocks)}只):")
for stock in stocks:
    print(f"  {stock.code} {stock.name}")

# 查询中国石油相关期货
futures = correlator.get_futures_by_stock("中国石油")
print(f"中国石油相关期货: {', '.join(futures)}")
```

### 2. 搜索示例

```python
# 搜索包含"煤"的期货
results = correlator.search_futures("煤")
for name, category in results:
    print(f"{name} ({category})")

# 搜索包含"中国"的股票  
results = correlator.search_stocks("中国")
for code, name in results:
    print(f"{code} {name}")
```

### 3. 分类分析示例

```python
# 获取所有分类
categories = correlator.get_all_categories()
print(f"期货分类: {', '.join(categories)}")

# 查看能源类期货
energy_futures = correlator.get_futures_by_category("能源")
for future_name in energy_futures:
    info = correlator.get_future_info(future_name)
    print(f"{future_name}: {info.price} ({info.change_pct}%)")
```

### 4. 投资分析示例

```python
# 找出关联股票最多的期货
future_stock_counts = []
for name, info in correlator.futures_data.items():
    future_stock_counts.append((name, len(info.related_stocks)))

future_stock_counts.sort(key=lambda x: x[1], reverse=True)
print("关联股票最多的期货品种:")
for name, count in future_stock_counts[:10]:
    print(f"  {name}: {count}只股票")
```

## 运行示例

### 测试功能
```bash
# 运行简单测试
cd /path/to/project
python -m tests.test_futures_stock_correlation simple

# 运行完整单元测试
python -m tests.test_futures_stock_correlation
```

### 运行演示程序
```bash
python examples/futures_stock_correlation_demo.py
```

## 数据来源

数据来源于东方财富网期货相关股票页面：
https://data.eastmoney.com/ifdata/xhgp.html

数据包括：
- 能源类：炼焦煤、动力煤、原油、液化气等
- 化工类：甲醇、PTA、乙二醇、尿素等  
- 橡塑类：天然橡胶、PVC、聚乙烯等
- 纺织类：棉花、PTA、粘胶短纤等
- 有色类：黄金、铜、铝、锌等
- 钢铁类：螺纹钢、热轧板卷、铁矿石等
- 建材类：玻璃、沥青等
- 农副类：玉米、大豆、生猪、白糖等

## 注意事项

1. **网络依赖**: 首次使用或缓存过期时需要网络连接
2. **数据更新**: 数据每小时自动更新一次
3. **查询精度**: 支持精确匹配和模糊匹配
4. **编码问题**: 在某些Windows环境下可能有中文显示问题

## 故障排除

### 常见问题

**Q: 提示"数据获取失败"怎么办？**
A: 检查网络连接，确保可以访问东方财富网

**Q: 查询结果为空？**  
A: 检查输入的期货/股票名称是否正确，尝试使用关键词搜索

**Q: 中文显示乱码？**
A: Windows环境下的编码问题，不影响功能使用

### 调试模式

```python
# 打印详细统计信息
correlator.print_summary()

# 检查数据状态
print(f"期货数量: {len(correlator.futures_data)}")
print(f"股票数量: {len(correlator.stock_to_futures)}")
print(f"最后更新: {correlator.last_update_time}")
```

## 贡献

欢迎提交 Issues 和 Pull Requests 来改进这个工具！

## 许可证

本项目遵循主项目的许可证。