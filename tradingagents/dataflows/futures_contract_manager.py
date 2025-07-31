"""
期货指数合约管理器
统一管理期货品种到指数合约的映射关系，提供合约代码转换和验证功能
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import re

class FuturesExchange(Enum):
    """期货交易所枚举"""
    SHFE = "上海期货交易所"
    DCE = "大连商品交易所"
    CZCE = "郑州商品交易所"
    CFFEX = "中国金融期货交易所"
    INE = "上海国际能源交易中心"
    GFEX = "广州期货交易所"

class FuturesCategory(Enum):
    """期货品种分类"""
    METALS = "有色金属"
    PRECIOUS_METALS = "贵金属"
    ENERGY = "能源化工"
    AGRICULTURE = "农产品"
    FINANCIAL = "金融期货"
    INDUSTRIAL = "工业品"

@dataclass
class FuturesContract:
    """期货合约信息"""
    symbol: str          # 品种代码 (如: CU)
    name: str           # 品种名称 (如: 沪铜)
    exchange: FuturesExchange  # 交易所
    category: FuturesCategory  # 品种分类
    index_code: str     # 指数合约代码 (如: CU99)
    full_code: str      # 完整代码 (如: SHFE.CU99)
    multiplier: int     # 合约乘数
    min_change: float   # 最小变动价位
    margin_rate: float  # 保证金比率
    trading_unit: str   # 交易单位
    delivery_month: str # 交割月份规则

class FuturesContractManager:
    """期货指数合约管理器"""
    
    def __init__(self):
        """初始化合约管理器"""
        self._contracts: Dict[str, FuturesContract] = {}
        self._symbol_to_index: Dict[str, str] = {}
        self._index_to_symbol: Dict[str, str] = {}
        self._exchange_mapping: Dict[str, str] = {}
        
        # 初始化合约数据
        self._initialize_contracts()
    
    def _initialize_contracts(self):
        """初始化所有期货合约数据"""
        
        # 上海期货交易所 (SHFE)
        shfe_contracts = [
            FuturesContract("CU", "沪铜", FuturesExchange.SHFE, FuturesCategory.METALS, 
                          "CU99", "KQ.i@SHFE.cu", 5, 10, 0.07, "5吨/手", "1-12月"),
            FuturesContract("AL", "沪铝", FuturesExchange.SHFE, FuturesCategory.METALS,
                          "AL99", "SHFE.AL99", 5, 5, 0.07, "5吨/手", "1-12月"),
            FuturesContract("ZN", "沪锌", FuturesExchange.SHFE, FuturesCategory.METALS,
                          "ZN99", "SHFE.ZN99", 5, 5, 0.08, "5吨/手", "1-12月"),
            FuturesContract("PB", "沪铅", FuturesExchange.SHFE, FuturesCategory.METALS,
                          "PB99", "SHFE.PB99", 5, 5, 0.08, "5吨/手", "1-12月"),
            FuturesContract("NI", "沪镍", FuturesExchange.SHFE, FuturesCategory.METALS,
                          "NI99", "SHFE.NI99", 1, 10, 0.08, "1吨/手", "1-12月"),
            FuturesContract("SN", "沪锡", FuturesExchange.SHFE, FuturesCategory.METALS,
                          "SN99", "SHFE.SN99", 1, 10, 0.08, "1吨/手", "1-12月"),
            FuturesContract("AU", "沪金", FuturesExchange.SHFE, FuturesCategory.PRECIOUS_METALS,
                          "AU99", "SHFE.AU99", 1000, 0.02, 0.06, "1000克/手", "2,4,6,8,10,12月"),
            FuturesContract("AG", "沪银", FuturesExchange.SHFE, FuturesCategory.PRECIOUS_METALS,
                          "AG99", "SHFE.AG99", 15, 1, 0.08, "15千克/手", "1-12月"),
            FuturesContract("RB", "螺纹钢", FuturesExchange.SHFE, FuturesCategory.INDUSTRIAL,
                          "RB99", "SHFE.RB99", 10, 1, 0.08, "10吨/手", "1-12月"),
            FuturesContract("HC", "热轧卷板", FuturesExchange.SHFE, FuturesCategory.INDUSTRIAL,
                          "HC99", "SHFE.HC99", 10, 1, 0.08, "10吨/手", "1-12月"),
            FuturesContract("SS", "不锈钢", FuturesExchange.SHFE, FuturesCategory.INDUSTRIAL,
                          "SS99", "SHFE.SS99", 5, 5, 0.10, "5吨/手", "1-12月"),
            FuturesContract("WR", "线材", FuturesExchange.SHFE, FuturesCategory.INDUSTRIAL,
                          "WR99", "SHFE.WR99", 10, 1, 0.08, "10吨/手", "1-12月"),
            FuturesContract("FU", "燃料油", FuturesExchange.SHFE, FuturesCategory.ENERGY,
                          "FU99", "SHFE.FU99", 10, 1, 0.08, "10吨/手", "1-12月"),
            FuturesContract("BU", "沥青", FuturesExchange.SHFE, FuturesCategory.ENERGY,
                          "BU99", "SHFE.BU99", 10, 2, 0.08, "10吨/手", "3,6,9,12月"),
            FuturesContract("RU", "天然橡胶", FuturesExchange.SHFE, FuturesCategory.INDUSTRIAL,
                          "RU99", "SHFE.RU99", 10, 5, 0.08, "10吨/手", "1,3,4,5,6,7,8,9,10,11月"),
        ]
        
        # 大连商品交易所 (DCE)
        dce_contracts = [
            FuturesContract("C", "玉米", FuturesExchange.DCE, FuturesCategory.AGRICULTURE,
                          "C99", "DCE.C99", 10, 1, 0.05, "10吨/手", "1,3,5,7,9,11月"),
            FuturesContract("CS", "玉米淀粉", FuturesExchange.DCE, FuturesCategory.AGRICULTURE,
                          "CS99", "DCE.CS99", 10, 1, 0.06, "10吨/手", "1,3,5,7,9,11月"),
            FuturesContract("A", "豆一", FuturesExchange.DCE, FuturesCategory.AGRICULTURE,
                          "A99", "DCE.A99", 10, 1, 0.05, "10吨/手", "1,3,5,7,9,11月"),
            FuturesContract("B", "豆二", FuturesExchange.DCE, FuturesCategory.AGRICULTURE,
                          "B99", "DCE.B99", 10, 1, 0.05, "10吨/手", "1,3,5,7,9,11月"),
            FuturesContract("M", "豆粕", FuturesExchange.DCE, FuturesCategory.AGRICULTURE,
                          "M99", "DCE.M99", 10, 1, 0.05, "10吨/手", "1,3,5,7,8,9,11,12月"),
            FuturesContract("Y", "豆油", FuturesExchange.DCE, FuturesCategory.AGRICULTURE,
                          "Y99", "DCE.Y99", 10, 2, 0.05, "10吨/手", "1,3,5,7,8,9,11,12月"),
            FuturesContract("P", "棕榈油", FuturesExchange.DCE, FuturesCategory.AGRICULTURE,
                          "P99", "DCE.P99", 10, 2, 0.05, "10吨/手", "1,3,5,7,8,9,11,12月"),
            FuturesContract("L", "聚乙烯", FuturesExchange.DCE, FuturesCategory.ENERGY,
                          "L99", "DCE.L99", 5, 5, 0.05, "5吨/手", "1,3,5,7,9,11月"),
            FuturesContract("V", "聚氯乙烯", FuturesExchange.DCE, FuturesCategory.ENERGY,
                          "V99", "DCE.V99", 5, 5, 0.05, "5吨/手", "1,3,5,7,9,11月"),
            FuturesContract("PP", "聚丙烯", FuturesExchange.DCE, FuturesCategory.ENERGY,
                          "PP99", "DCE.PP99", 5, 1, 0.05, "5吨/手", "1,3,5,7,9,11月"),
            FuturesContract("JD", "鸡蛋", FuturesExchange.DCE, FuturesCategory.AGRICULTURE,
                          "JD99", "DCE.JD99", 10, 1, 0.08, "10吨/手", "1,3,4,5,6,9,10,11,12月"),
            FuturesContract("I", "铁矿石", FuturesExchange.DCE, FuturesCategory.INDUSTRIAL,
                          "I99", "DCE.I99", 100, 0.5, 0.08, "100吨/手", "1,3,5,7,9,11月"),
            FuturesContract("J", "焦炭", FuturesExchange.DCE, FuturesCategory.ENERGY,
                          "J99", "DCE.J99", 100, 0.5, 0.08, "100吨/手", "1,3,5,7,9,11月"),
            FuturesContract("JM", "焦煤", FuturesExchange.DCE, FuturesCategory.ENERGY,
                          "JM99", "DCE.JM99", 60, 0.5, 0.08, "60吨/手", "1,3,5,7,9,11月"),
        ]
        
        # 郑州商品交易所 (CZCE)
        czce_contracts = [
            FuturesContract("WH", "强筋麦", FuturesExchange.CZCE, FuturesCategory.AGRICULTURE,
                          "WH99", "CZCE.WH99", 20, 1, 0.05, "20吨/手", "1,3,5,7,9,11月"),
            FuturesContract("PM", "普麦", FuturesExchange.CZCE, FuturesCategory.AGRICULTURE,
                          "PM99", "CZCE.PM99", 50, 1, 0.05, "50吨/手", "1,3,5,7,9,11月"),
            FuturesContract("CF", "棉花", FuturesExchange.CZCE, FuturesCategory.AGRICULTURE,
                          "CF99", "CZCE.CF99", 5, 5, 0.05, "5吨/手", "1,3,5,7,9,11月"),
            FuturesContract("CY", "棉纱", FuturesExchange.CZCE, FuturesCategory.AGRICULTURE,
                          "CY99", "CZCE.CY99", 5, 5, 0.06, "5吨/手", "1,3,5,7,9,11月"),
            FuturesContract("SR", "白糖", FuturesExchange.CZCE, FuturesCategory.AGRICULTURE,
                          "SR99", "CZCE.SR99", 10, 1, 0.05, "10吨/手", "1,3,5,7,9,11月"),
            FuturesContract("TA", "PTA", FuturesExchange.CZCE, FuturesCategory.ENERGY,
                          "TA99", "CZCE.TA99", 5, 2, 0.06, "5吨/手", "1,3,5,7,9,11月"),
            FuturesContract("MA", "甲醇", FuturesExchange.CZCE, FuturesCategory.ENERGY,
                          "MA99", "CZCE.MA99", 10, 1, 0.06, "10吨/手", "1,3,5,7,9,11月"),
            FuturesContract("FG", "玻璃", FuturesExchange.CZCE, FuturesCategory.INDUSTRIAL,
                          "FG99", "CZCE.FG99", 20, 1, 0.06, "20吨/手", "1,3,5,7,9,11月"),
            FuturesContract("OI", "菜籽油", FuturesExchange.CZCE, FuturesCategory.AGRICULTURE,
                          "OI99", "CZCE.OI99", 10, 1, 0.05, "10吨/手", "1,3,5,7,9,11月"),
            FuturesContract("RM", "菜籽粕", FuturesExchange.CZCE, FuturesCategory.AGRICULTURE,
                          "RM99", "CZCE.RM99", 10, 1, 0.05, "10吨/手", "1,3,5,7,9,11月"),
            FuturesContract("ZC", "动力煤", FuturesExchange.CZCE, FuturesCategory.ENERGY,
                          "ZC99", "CZCE.ZC99", 100, 0.2, 0.06, "100吨/手", "1,3,5,7,9,11月"),
            FuturesContract("SA", "纯碱", FuturesExchange.CZCE, FuturesCategory.INDUSTRIAL,
                          "SA99", "CZCE.SA99", 20, 1, 0.06, "20吨/手", "1,3,5,7,9,11月"),
        ]
        
        # 中国金融期货交易所 (CFFEX)
        cffex_contracts = [
            FuturesContract("IF", "沪深300股指", FuturesExchange.CFFEX, FuturesCategory.FINANCIAL,
                          "IF99", "CFFEX.IF99", 300, 0.2, 0.12, "300元/点", "当月,下月,随后两个季月"),
            FuturesContract("IC", "中证500股指", FuturesExchange.CFFEX, FuturesCategory.FINANCIAL,
                          "IC99", "CFFEX.IC99", 200, 0.2, 0.15, "200元/点", "当月,下月,随后两个季月"),
            FuturesContract("IH", "上证50股指", FuturesExchange.CFFEX, FuturesCategory.FINANCIAL,
                          "IH99", "CFFEX.IH99", 300, 0.2, 0.12, "300元/点", "当月,下月,随后两个季月"),
            FuturesContract("IM", "中证1000股指", FuturesExchange.CFFEX, FuturesCategory.FINANCIAL,
                          "IM99", "CFFEX.IM99", 200, 0.2, 0.15, "200元/点", "当月,下月,随后两个季月"),
            FuturesContract("T", "10年期国债", FuturesExchange.CFFEX, FuturesCategory.FINANCIAL,
                          "T99", "CFFEX.T99", 10000, 0.005, 0.02, "10000元/张", "3,6,9,12月"),
            FuturesContract("TF", "5年期国债", FuturesExchange.CFFEX, FuturesCategory.FINANCIAL,
                          "TF99", "CFFEX.TF99", 10000, 0.005, 0.015, "10000元/张", "3,6,9,12月"),
            FuturesContract("TS", "2年期国债", FuturesExchange.CFFEX, FuturesCategory.FINANCIAL,
                          "TS99", "CFFEX.TS99", 20000, 0.002, 0.005, "20000元/张", "3,6,9,12月"),
        ]
        
        # 上海国际能源交易中心 (INE)
        ine_contracts = [
            FuturesContract("SC", "原油", FuturesExchange.INE, FuturesCategory.ENERGY,
                          "SC99", "INE.SC99", 1000, 0.1, 0.07, "1000桶/手", "最近1-12个月连续月份及随后8个季月"),
            FuturesContract("NR", "20号胶", FuturesExchange.INE, FuturesCategory.INDUSTRIAL,
                          "NR99", "INE.NR99", 10, 5, 0.08, "10吨/手", "1,3,4,5,6,7,8,9,10,11月"),
            FuturesContract("LU", "低硫燃料油", FuturesExchange.INE, FuturesCategory.ENERGY,
                          "LU99", "INE.LU99", 10, 1, 0.08, "10吨/手", "1-12月"),
        ]
        
        # 广州期货交易所 (GFEX)
        gfex_contracts = [
            FuturesContract("SI", "工业硅", FuturesExchange.GFEX, FuturesCategory.INDUSTRIAL,
                          "SI99", "GFEX.SI99", 5, 5, 0.08, "5吨/手", "1,3,5,7,9,11月"),
        ]
        
        # 合并所有合约
        all_contracts = shfe_contracts + dce_contracts + czce_contracts + cffex_contracts + ine_contracts + gfex_contracts
        
        # 构建映射关系
        for contract in all_contracts:
            self._contracts[contract.symbol] = contract
            self._symbol_to_index[contract.symbol] = contract.index_code
            self._index_to_symbol[contract.index_code] = contract.symbol
            self._exchange_mapping[contract.symbol] = contract.full_code
    
    def get_contract(self, symbol: str) -> Optional[FuturesContract]:
        """根据品种代码获取合约信息"""
        return self._contracts.get(symbol.upper())
    
    def get_index_code(self, symbol: str) -> Optional[str]:
        """根据品种代码获取指数合约代码"""
        return self._symbol_to_index.get(symbol.upper())
    
    def get_symbol_from_index(self, index_code: str) -> Optional[str]:
        """根据指数合约代码获取品种代码"""
        return self._index_to_symbol.get(index_code.upper())
    
    def get_full_code(self, symbol: str) -> Optional[str]:
        """根据品种代码获取完整合约代码"""
        return self._exchange_mapping.get(symbol.upper())
    
    def is_valid_symbol(self, symbol: str) -> bool:
        """验证品种代码是否有效"""
        return symbol.upper() in self._contracts
    
    def is_valid_index_code(self, index_code: str) -> bool:
        """验证指数合约代码是否有效"""
        return index_code.upper() in self._index_to_symbol
    
    def parse_futures_code(self, code: str) -> Tuple[Optional[str], bool]:
        """
        解析期货代码
        返回: (品种代码, 是否为指数合约)
        """
        code = code.upper().strip()
        
        # 检查是否为指数合约格式 (如: CU99, IF99)
        index_match = re.match(r'^([A-Z]{1,3})99$', code)
        if index_match:
            symbol = index_match.group(1)
            if self.is_valid_symbol(symbol):
                return symbol, True
        
        # 检查是否为具体合约格式 (如: CU2403, IF2403)
        specific_match = re.match(r'^([A-Z]{1,3})\d{4}$', code)
        if specific_match:
            symbol = specific_match.group(1)
            if self.is_valid_symbol(symbol):
                return symbol, False
        
        return None, False
    
    def get_contracts_by_exchange(self, exchange: FuturesExchange) -> List[FuturesContract]:
        """根据交易所获取合约列表"""
        return [contract for contract in self._contracts.values() 
                if contract.exchange == exchange]
    
    def get_contracts_by_category(self, category: FuturesCategory) -> List[FuturesContract]:
        """根据品种分类获取合约列表"""
        return [contract for contract in self._contracts.values() 
                if contract.category == category]
    
    def search_contracts(self, keyword: str) -> List[FuturesContract]:
        """根据关键词搜索合约"""
        keyword = keyword.lower()
        results = []
        
        for contract in self._contracts.values():
            if (keyword in contract.symbol.lower() or 
                keyword in contract.name.lower() or
                keyword in contract.index_code.lower()):
                results.append(contract)
        
        return results
    
    def get_all_symbols(self) -> List[str]:
        """获取所有品种代码"""
        return list(self._contracts.keys())
    
    def get_all_index_codes(self) -> List[str]:
        """获取所有指数合约代码"""
        return list(self._index_to_symbol.keys())
    
    def get_contract_info(self, symbol: str) -> Dict:
        """获取合约详细信息（字典格式）"""
        contract = self.get_contract(symbol)
        if not contract:
            return {}
        
        return {
            "symbol": contract.symbol,
            "name": contract.name,
            "exchange": contract.exchange.value,
            "category": contract.category.value,
            "index_code": contract.index_code,
            "full_code": contract.full_code,
            "multiplier": contract.multiplier,
            "min_change": contract.min_change,
            "margin_rate": contract.margin_rate,
            "trading_unit": contract.trading_unit,
            "delivery_month": contract.delivery_month
        }
    
    def validate_futures_input(self, code: str) -> Tuple[bool, str, Optional[Dict]]:
        """
        验证期货输入代码
        返回: (是否有效, 错误信息, 合约信息)
        """
        if not code or not code.strip():
            return False, "期货代码不能为空", None
        
        symbol, is_index = self.parse_futures_code(code)
        if not symbol:
            return False, "期货代码格式错误，应为指数合约格式（如：CU99）或具体合约格式（如：CU2403）", None
        
        contract_info = self.get_contract_info(symbol)
        if not contract_info:
            return False, f"不支持的期货品种: {symbol}", None
        
        return True, "", contract_info

# 全局单例实例
_contract_manager = None

def get_contract_manager() -> FuturesContractManager:
    """获取期货合约管理器单例"""
    global _contract_manager
    if _contract_manager is None:
        _contract_manager = FuturesContractManager()
    return _contract_manager