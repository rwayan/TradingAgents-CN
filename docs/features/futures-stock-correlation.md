# 期货股票关联查询工具

## 概述

这个工具可以帮助你查询期货品种与相关股票之间的关联关系，数据来源于东方财富网。支持多种查询方式：
- 根据期货品种名称，查找相关股票
- 根据股票名称，查找相关期货品种
- **🆕 根据期货合约代码，查找相关股票**
- **🆕 根据股票代码，查找相关期货合约代码**

## 功能特性

- ✅ **双向查询**: 期货↔股票，合约代码↔股票代码
- ✅ **实时数据**: 从东方财富网获取最新数据
- ✅ **智能搜索**: 支持模糊匹配和关键词搜索  
- ✅ **分类浏览**: 按期货分类（能源、有色、化工等）查看
- ✅ **价格分析**: 查看期货价格和涨跌幅
- ✅ **缓存机制**: 1小时数据缓存，提高查询效率
- ✅ **期货合约映射**: 支持85个期货品种的合约代码映射

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

### 🆕 期货合约代码查询

```python
# 根据期货合约代码查找相关股票
stocks = correlator.get_stocks_by_contract_code("CU2501")  # 铜2501合约
for stock in stocks:
    print(f"{stock.code} {stock.name}")

# 根据股票代码查找相关期货合约
contracts = correlator.get_contract_codes_by_stock_code("600362")  # 江西铜业
print(f"相关合约: {', '.join(contracts)}")  # 输出: ['CU', 'PB']

# 根据股票名称查找相关期货合约
contracts = correlator.get_contract_codes_by_stock_name("江西铜业")
print(f"相关合约: {', '.join(contracts)}")
```

### 便利函数

```python
from tradingagents.dataflows.futures_stock_correlation import (
    get_related_stocks, get_related_futures,
    get_stocks_by_contract, get_contracts_by_stock_code, get_contracts_by_stock_name
)

# 原有便利函数
stocks = get_related_stocks("黄金")
futures = get_related_futures("中国石油")

# 🆕 新增便利函数
stocks = get_stocks_by_contract("AU2412")  # 黄金2412合约
contracts = get_contracts_by_stock_code("600362")  # 根据股票代码
contracts = get_contracts_by_stock_name("江西铜业")  # 根据股票名称
```

## API 参考

### FuturesStockCorrelation 类

#### 核心方法

- `fetch_data()` - 获取最新数据
- `get_stocks_by_future(future_name)` - 根据期货获取相关股票
- `get_futures_by_stock(stock_name)` - 根据股票获取相关期货
- **🆕 `get_stocks_by_contract_code(contract_code)`** - 根据期货合约代码获取相关股票
- **🆕 `get_contract_codes_by_stock_code(stock_code)`** - 根据股票代码获取相关期货合约
- **🆕 `get_contract_codes_by_stock_name(stock_name)`** - 根据股票名称获取相关期货合约
- `search_futures(keyword)` - 搜索期货品种
- `search_stocks(keyword)` - 搜索股票
- `get_future_info(future_name)` - 获取期货详细信息

#### 分析方法

- `get_all_categories()` - 获取所有期货分类
- `get_futures_by_category(category)` - 根据分类获取期货
- `print_summary()` - 打印数据统计

### 便利函数

#### 原有便利函数
- `get_related_stocks(future_name)` - 根据期货品种获取相关股票
- `get_related_futures(stock_name)` - 根据股票名称获取相关期货

#### 🆕 新增便利函数
- `get_stocks_by_contract(contract_code)` - 根据期货合约代码获取相关股票
- `get_contracts_by_stock_code(stock_code)` - 根据股票代码获取相关期货合约
- `get_contracts_by_stock_name(stock_name)` - 根据股票名称获取相关期货合约

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

## 期货合约代码映射

支持85个期货品种的合约代码映射，涵盖：

### 🆕 期货合约代码表
| 合约代码 | 期货名称 | 合约代码 | 期货名称 |
|---------|---------|---------|---------|
| CU | 铜 | AU | 黄金 |
| AL | 铝 | AG | 白银 |
| ZN | 锌 | PB | 铅 |
| SN | 锡 | NI | 镍 |
| RB | 螺纹钢 | HC | 热轧卷板 |
| I | 铁矿石 | J | 焦炭 |
| JM | 焦煤 | ZC | 动力煤 |
| FU | 燃料油 | BU | 沥青 |
| RU | 橡胶 | L | 聚乙烯LLDPE |
| V | 聚氯乙稀PVC | PP | 聚丙烯 |
| TA | 精对苯二甲酸PTA | MA | 甲醇 |
| SA | 纯碱 | UR | 尿素 |
| FG | 玻璃 | M | 豆粕 |
| Y | 豆油 | A | 黄大豆1号 |
| ... | ... | ... | ... |

*完整映射表包含85个品种*

## 示例代码

### 1. 期货合约代码查询示例

```python
correlator = FuturesStockCorrelation()
correlator.fetch_data()

# 查询铜期货相关股票
stocks = correlator.get_stocks_by_contract_code("CU2501")
print(f"铜2501合约相关股票({len(stocks)}只):")
for stock in stocks[:5]:  # 显示前5只
    print(f"  {stock.code} {stock.name}")

# 查询江西铜业相关期货合约
contracts = correlator.get_contract_codes_by_stock_code("600362")
print(f"江西铜业相关期货合约: {', '.join(contracts)}")
```

### 2. 批量查询示例

```python
# 批量查询多个合约的相关股票
contract_codes = ["CU2501", "AU2412", "RB2505", "AL2503"]

for contract in contract_codes:
    stocks = correlator.get_stocks_by_contract_code(contract)
    print(f"{contract}: {len(stocks)}只相关股票")
    
# 批量查询多只股票的相关合约
stock_codes = ["600362", "600309", "601899", "600028"]

for stock_code in stock_codes:
    contracts = correlator.get_contract_codes_by_stock_code(stock_code)
    if contracts:
        print(f"{stock_code}: {', '.join(contracts)}")
```

### 3. 投资组合分析示例

```python
def analyze_portfolio_futures_exposure(stock_codes):
    """分析股票组合的期货敞口"""
    correlator = FuturesStockCorrelation()
    correlator.fetch_data()
    
    exposure = {}
    for stock_code in stock_codes:
        contracts = correlator.get_contract_codes_by_stock_code(stock_code)
        for contract in contracts:
            if contract not in exposure:
                exposure[contract] = []
            exposure[contract].append(stock_code)
    
    print("投资组合期货敞口分析:")
    for contract, stocks in exposure.items():
        print(f"  {contract}: {len(stocks)}只股票 - {', '.join(stocks[:3])}")
    
    return exposure

# 使用示例
portfolio = ["600362", "600309", "601899", "600028", "000001"]
analyze_portfolio_futures_exposure(portfolio)
```

### 4. 套利机会分析示例

```python
def find_arbitrage_opportunities():
    """寻找期货套利机会"""
    correlator = FuturesStockCorrelation()
    correlator.fetch_data()
    
    # 找出同时关联多个期货品种的股票
    multi_future_stocks = {}
    for stock_name, futures in correlator.stock_to_futures.items():
        if len(futures) > 2:  # 关联3个以上期货品种
            # 获取股票代码
            contracts = correlator.get_contract_codes_by_stock_name(stock_name)
            if contracts:
                multi_future_stocks[stock_name] = contracts
    
    print("多期货品种关联股票（套利机会）:")
    for stock_name, contracts in sorted(multi_future_stocks.items(), 
                                       key=lambda x: len(x[1]), reverse=True)[:10]:
        print(f"  {stock_name}: {', '.join(contracts)}")

find_arbitrage_opportunities()
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
python -c "from tradingagents.dataflows.futures_stock_correlation import main; main()"
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

## 数据统计

- **期货品种总数**: 85个
- **东方财富网品种数**: 75个
- **成功映射品种**: 50个
- **映射覆盖率**: 58.8%
- **支持的合约代码**: 85个

## 注意事项

1. **网络依赖**: 首次使用或缓存过期时需要网络连接
2. **数据更新**: 数据每小时自动更新一次
3. **查询精度**: 支持精确匹配和模糊匹配
4. **合约代码**: 支持标准期货合约代码格式（如CU2501, AU99等）
5. **一对多关系**: 一个期货可能对应多只股票，一只股票可能对应多个期货合约

## 故障排除

### 常见问题

**Q: 提示"数据获取失败"怎么办？**
A: 检查网络连接，确保可以访问东方财富网

**Q: 合约代码查询结果为空？**  
A: 检查合约代码格式是否正确，确保对应的期货品种在映射表中

**Q: 股票代码查询结果为空？**
A: 确认股票代码正确，该股票是否与期货品种相关

### 调试模式

```python
# 打印详细统计信息
correlator.print_summary()

# 检查映射关系
from tradingagents.utils.future_helper import FUTURES_NAME_MAPPING
print("支持的期货合约代码:")
for code, name in FUTURES_NAME_MAPPING.items():
    print(f"  {code}: {name}")

# 检查数据状态
print(f"期货数量: {len(correlator.futures_data)}")
print(f"股票数量: {len(correlator.stock_to_futures)}")
```

## 更新日志

### v2.0.0 - 🆕 期货合约代码支持
- ✅ 新增期货合约代码到股票的映射查询
- ✅ 新增股票代码到期货合约代码的反向查询  
- ✅ 新增85个期货品种的合约代码映射表
- ✅ 新增5个便利函数
- ✅ 增强测试用例覆盖期货合约代码功能
- ✅ 更新文档和使用示例

### v1.0.0 - 基础版本
- ✅ 期货品种名称与股票的双向查询
- ✅ 数据缓存和自动更新机制
- ✅ 搜索和分类功能

## 贡献

欢迎提交 Issues 和 Pull Requests 来改进这个工具！

## 许可证

本项目遵循主项目的许可证。