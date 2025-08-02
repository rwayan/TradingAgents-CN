"""
期货指数合约管理器
统一管理期货品种到指数合约的映射关系，提供合约代码转换和验证功能
支持从TQSdk API动态获取合约信息
"""

import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import re
import asyncio
import json
import os
from datetime import datetime
import logging

# 导入统一日志系统
from tradingagents.utils.logging_init import setup_dataflow_logging
logger = setup_dataflow_logging()

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
    """期货指数合约管理器 - 使用天勤API动态获取合约信息"""
    
    def __init__(self):
        """初始化合约管理器"""
        self._contracts_cache: List[str]= []  # 动态合约缓存
        self._index_contracts: List[str] = []        # 指数合约列表
        self._main_contracts: List[str] = []         # 主连合约列表
        self._futures_contracts: Dict[str, List[str]] = {}  # 期货合约按交易所分类
        self._last_update: Optional[datetime] = None
        self._tqsdk_adapter = None
        
        logger.info("🔧 期货合约管理器初始化完成（使用天勤API动态获取）")

    def _get_tqsdk_adapter(self):
        """获取天勤适配器实例"""
        if self._tqsdk_adapter is None:
            try:
                from .tqsdk_futures_adapter import get_tqsdk_futures_adapter
                self._tqsdk_adapter = get_tqsdk_futures_adapter()
                logger.info("🔗 天勤适配器已连接到合约管理器")
            except ImportError as e:
                logger.warning(f"⚠️ 无法导入天勤适配器: {e}")
                return None
            except Exception as e:
                logger.error(f"❌ 获取天勤适配器失败: {e}")
                return None
        return self._tqsdk_adapter

    async def _refresh_contracts(self, force_refresh: bool = False) -> bool:
        """
        从天勤API刷新合约信息
        
        Args:
            force_refresh: 是否强制刷新
            
        Returns:
            bool: 是否成功刷新
        """
        try:
            # 检查是否需要刷新（每4小时刷新一次）
            if not force_refresh and self._last_update:
                elapsed = datetime.now() - self._last_update
                if elapsed.total_seconds() < 14400:  # 4小时内不重复刷新
                    return True

            adapter = self._get_tqsdk_adapter()
            if not adapter:
                return False

            logger.info("🔄 从天勤API刷新合约信息...")
            
            # 获取指数合约
            self._index_contracts = await adapter.query_quotes(ins_class="INDEX", expired=False)
            if self._index_contracts:
                logger.info(f"✅ 获取 {len(self._index_contracts)} 个指数合约")
            
            # 获取主连合约
            self._main_contracts = await adapter.query_quotes(ins_class="CONT")
            if self._main_contracts:
                logger.info(f"✅ 获取 {len(self._main_contracts)} 个主连合约")
            
            # 获取各交易所期货合约
            exchanges = ["SHFE", "DCE", "CZCE", "CFFEX", "INE", "GFEX"]
            for exchange in exchanges:
                try:
                    contracts = await adapter.query_quotes(
                        ins_class="FUTURE", 
                        exchange_id=exchange, 
                        expired=False
                    )
                    if contracts:
                        self._futures_contracts[exchange] = contracts
                        logger.debug(f"✅ {exchange}: {len(contracts)} 个期货合约")
                except Exception as e:
                    logger.warning(f"⚠️ 获取 {exchange} 合约失败: {e}")
            
            self._contracts_cache = [item for sublist in self._futures_contracts.values() for item in sublist]
            self._contracts_cache += self._index_contracts + self._main_contracts
            logger.info(f"✅ 合约信息刷新完成，共 {len(self._contracts_cache)} 个合约")
            self._last_update = datetime.now()
            logger.info("🎉 合约信息刷新完成")
            return True
            
        except Exception as e:
            logger.error(f"❌ 刷新合约信息失败: {e}")
            return False

    def _sync_refresh_contracts(self, force_refresh: bool = False) -> bool:
        """同步方式刷新合约（用于同步方法调用）"""
        try:
            loop = None
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        lambda: asyncio.run(self._refresh_contracts(force_refresh))
                    )
                    return future.result(timeout=30)
            else:
                return loop.run_until_complete(self._refresh_contracts(force_refresh))
                
        except Exception as e:
            logger.error(f"❌ 同步刷新合约失败: {e}")
            return False
    
    def get_contract(self, symbol: str) -> Optional[Dict]:
        """根据品种代码获取合约信息（动态从天勤API获取）"""
        # 确保合约数据是最新的
        self._sync_refresh_contracts()
        
        symbol_lower = symbol.lower()
        symbol_upper = symbol.upper()
        
        
        # 在指数合约中查找 (考虑不同交易所的大小写规则)
        for contract in self._index_contracts:
            contract_lower = contract.lower()
            # 匹配小写格式 (SHFE, DCE, INE)
            if f".{symbol_lower}" in contract_lower:
                return {
                    "symbol": symbol_upper,
                    "name": f"期货{symbol_upper}",
                    "full_code": contract,
                    "contract_type": "INDEX",
                    "is_index": True
                }
            # 匹配大写格式 (CZCE, GFEX, CFFEX)
            if f".{symbol_upper}" in contract:
                return {
                    "symbol": symbol_upper,
                    "name": f"期货{symbol_upper}",
                    "full_code": contract,
                    "contract_type": "INDEX",
                    "is_index": True
                }
        
        # 在主连合约中查找 (考虑不同交易所的大小写规则)
        for contract in self._main_contracts:
            contract_lower = contract.lower()
            # 匹配小写格式 (SHFE, DCE, INE)
            if f".{symbol_lower}" in contract_lower:
                return {
                    "symbol": symbol_upper,
                    "name": f"期货{symbol_upper}",
                    "full_code": contract,
                    "contract_type": "CONT",
                    "is_main": True
                }
            # 匹配大写格式 (CZCE, GFEX, CFFEX)
            if f".{symbol_upper}" in contract:
                return {
                    "symbol": symbol_upper,
                    "name": f"期货{symbol_upper}",
                    "full_code": contract,
                    "contract_type": "CONT",
                    "is_main": True
                }
        
        return None
    
    def get_index_code(self, symbol: str) -> Optional[str]:
        """根据品种代码获取指数合约代码
        输入是品种代码（如 CU99）不区分大小写，
        返回完整的指数合约代码（如KQ.i@SHFE.rb）区分大小写
        """
        self._sync_refresh_contracts()
        
        symbol_lower = symbol.lower()
        symbol_upper = symbol.upper()
        
        # 在指数合约中查找，使用精确匹配避免混淆
        for contract in self._index_contracts:
            if 'KQ.i@' in contract:
                # 提取合约中的品种代码部分，格式: KQ.i@EXCHANGE.SYMBOL
                contract_part = contract.replace('KQ.i@', '')
                if '.' in contract_part:
                    parts = contract_part.split('.')
                    if len(parts) >= 2:
                        exchange, contract_symbol = parts[0], parts[1]
                        # 精确匹配品种代码（大小写不敏感）
                        if contract_symbol.upper() == symbol_upper:
                            return contract
            else:
                # 处理其他格式的指数合约，使用精确的结尾匹配
                # 小写格式 (SHFE, DCE, INE)
                if contract.lower().endswith(f".{symbol_lower}"):
                    return contract
                # 大写格式 (CZCE, GFEX, CFFEX)  
                if contract.endswith(f".{symbol_upper}"):
                    return contract
        
        return None
    
    def get_symbol_from_index(self, index_code: str) -> Optional[str]:
        """根据指数合约代码获取品种代码
        这里返回的品种代码都是大写的
        """
        index_code = index_code.upper()
        
        # 从指数合约代码中提取品种代码 (格式: KQ.i@EXCHANGE.SYMBOL)
        import re
        # 匹配大写品种代码 (CZCE, GFEX, CFFEX)
        match = re.match(r'^KQ\.i@[A-Z]+\.([A-Z]+)$', index_code)
        if match:
            return match.group(1)
        
        # 匹配小写品种代码 (SHFE, DCE, INE) - 转换为大写返回
        match = re.match(r'^KQ\.i@[A-Z]+\.([a-z]+)$', index_code)
        if match:
            return match.group(1).upper()
        
        return None
    
    def get_full_code(self, symbol: str) -> Optional[str]:
        """根据品种代码获取完整合约代码（优先指数合约）"""
        # 首先尝试获取指数合约
        index_code = self.get_index_code(symbol)
        if index_code:
            return index_code
            
        # 其次尝试主连合约
        symbol_lower = symbol.lower()
        symbol_upper = symbol.upper()
        
        for contract in self._main_contracts:
            # 小写格式 (SHFE, DCE, INE)
            if f".{symbol_lower}" in contract.lower():
                return contract
            # 大写格式 (CZCE, GFEX, CFFEX)
            if f".{symbol_upper}" in contract:
                return contract
        
        return None
    
    def is_valid_symbol(self, symbol: str) -> bool:
        """验证品种代码是否有效（从天勤API动态验证）
        目前看到的品种代码都是product_id的意思
        """
        return self.get_contract(symbol) is not None
    
    def is_valid_index_code(self, index_code: str) -> bool:
        """验证指数合约代码是否有效"""
        self._sync_refresh_contracts()
        return index_code.upper() in [c.upper() for c in self._index_contracts]
    
    def parse_futures_code(self, code: str) -> Tuple[Optional[str], bool]:
        """
        解析期货代码
        返回: (品种代码product_id 大写的, 是否为指数合约)
        """
        code = code.strip()
        
        # 检查是否为天勤指数合约格式 (KQ.i@EXCHANGE.SYMBOL)
        import re
        # 大写品种代码 (CZCE, GFEX, CFFEX)
        index_match = re.match(r'^KQ\.i@[A-Z]+\.([A-Z]+)$', code)
        if index_match:
            symbol = index_match.group(1)
            return symbol, True
        
        # 小写品种代码 (SHFE, DCE, INE)
        index_match_lower = re.match(r'^KQ\.i@[A-Z]+\.([a-z]+)$', code)
        if index_match_lower:
            symbol = index_match_lower.group(1).upper()
            return symbol, True
        
        # 检查是否为天勤主连合约格式 (KQ.m@EXCHANGE.SYMBOL)
        # 大写品种代码 (CZCE, GFEX, CFFEX)
        main_match = re.match(r'^KQ\.m@[A-Z]+\.([A-Z]+)$', code)
        if main_match:
            symbol = main_match.group(1)
            return symbol, True
        
        # 小写品种代码 (SHFE, DCE, INE)
        main_match_lower = re.match(r'^KQ\.m@[A-Z]+\.([a-z]+)$', code)
        if main_match_lower:
            symbol = main_match_lower.group(1).upper()
            return symbol, True
        
        # 检查是否为传统指数合约格式 (SYMBOL99)
        legacy_index_match = re.match(r'^([A-Z]{1,4})99$', code.upper())
        if legacy_index_match:
            symbol = legacy_index_match.group(1)
            if self.is_valid_symbol(symbol):
                return symbol, True
        
        # 检查是否为传统主连合约格式 (SYMBOL888)
        legacy_main_match = re.match(r'^([A-Z]{1,4})888$', code.upper())
        if legacy_main_match:
            symbol = legacy_main_match.group(1)
            if self.is_valid_symbol(symbol):
                return symbol, True
        
        # 检查是否为具体合约格式 (SYMBOL2403)
        specific_match = re.match(r'^([A-Z]{1,4})\d{3,4}$', code.upper())
        if specific_match:
            symbol = specific_match.group(1)
            if self.is_valid_symbol(symbol):
                return symbol, False
        
        # 检查是否为交易所格式 (EXCHANGE.SYMBOL99 或 EXCHANGE.SYMBOL2403)
        exchange_match = re.match(r'^([A-Z]+)\.([A-Za-z]{1,4})(\d{2,4})$', code)
        if exchange_match:
            symbol = exchange_match.group(2).upper()
            number = exchange_match.group(3)
            if self.is_valid_symbol(symbol):
                is_index = number == "99"
                return symbol, is_index
        
        return None, False
    
    def get_contracts_by_exchange(self, exchange: str) -> List[str]:
        """根据交易所获取合约列表"""
        self._sync_refresh_contracts()
        return self._futures_contracts.get(exchange.upper(), [])
    
    def search_contracts(self, keyword: str) -> List[str]:
        """根据关键词搜索合约"""
        self._sync_refresh_contracts()
        
        keyword = keyword.upper()
        results = []
        
        # 搜索指数合约
        for contract in self._index_contracts:
            if keyword in contract.upper():
                results.append(contract)
        
        # 搜索主连合约
        for contract in self._main_contracts:
            if keyword in contract.upper():
                results.append(contract)
        
        # 搜索期货合约
        for exchange_contracts in self._futures_contracts.values():
            for contract in exchange_contracts:
                if keyword in contract.upper():
                    results.append(contract)
        
        return list(set(results))  # 去重
    
    def get_all_symbols(self) -> List[str]:
        """获取所有品种代码"""
        self._sync_refresh_contracts()
        
        symbols = set()
        
        # 从指数合约中提取品种代码
        import re
        for contract in self._index_contracts:
            # 匹配大写品种代码 (CZCE, GFEX, CFFEX) # 匹配小写品种代码 (SHFE, DCE, INE)
            match = re.match(r'^KQ\.i@[A-Z]+\.([A-Za-z]+)$', contract)
            if match:
                symbols.add(match.group(1))        
        return list(symbols)
    
    def get_all_index_codes(self) -> List[str]:
        """获取所有指数合约代码"""
        self._sync_refresh_contracts()
        return self._index_contracts.copy()
    
    def get_contract_info(self, symbol: str) -> Dict:
        """获取合约详细信息（字典格式）"""
        try:
            adapter = self._get_tqsdk_adapter()
            if not adapter:
                logger.warning(f"⚠️ 无法获取天勤适配器，返回空合约信息")
                return {}
            
            normalized_symbol = adapter._normalize_symbol(symbol)
            
            # 添加异常处理来保护 query_symbol_info 调用
            try:
                # query_symbol_info 返回 pandas DataFrame，需要传入列表
                if normalized_symbol in self._contracts_cache:
                    df_result = adapter.api.query_symbol_info(normalized_symbol)
                    if df_result is None or df_result.empty:
                        logger.warning(f"⚠️ 未找到合约信息: {normalized_symbol}")
                        return {}
                
                    # 将 DataFrame 的第一行转为字典
                    raw_data = dict(df_result.iloc[0])
                
                    # 转换为标准化的合约信息格式，满足各调用方的期望
                    contract_info = {
                        # 基本信息（满足测试和验证需求）
                        'symbol': normalized_symbol,
                        'underlying': self._extract_underlying_from_symbol(normalized_symbol),
                        'name': raw_data.get("instrument_name",self._get_contract_name(symbol)),
                        
                        # 交易所信息
                        'exchange': normalized_symbol.split('.')[0] if '.' in normalized_symbol else 'UNKNOWN',
                        'exchange_name': self._get_exchange_name(normalized_symbol),
                        
                        # 价格信息（处理 NaN 值）
                        'upper_limit': float(raw_data.get('upper_limit', 0)) if self._is_valid_number(raw_data.get('upper_limit')) else 0,
                        'lower_limit': float(raw_data.get('lower_limit', 0)) if self._is_valid_number(raw_data.get('lower_limit')) else 0,
                        'pre_settlement': float(raw_data.get('pre_settlement', 0)) if self._is_valid_number(raw_data.get('pre_settlement')) else 0,
                        'pre_close': float(raw_data.get('pre_close', 0)) if self._is_valid_number(raw_data.get('pre_close')) else 0,
                        'pre_open_interest': int(raw_data.get('pre_open_interest', 0)) if self._is_valid_number(raw_data.get('pre_open_interest')) else 0,
                        
                        # 合约属性
                        'is_futures': True,
                        'is_index_contract': '99' in normalized_symbol or 'KQ.i@' in normalized_symbol,
                        'currency': 'CNY',
                        
                        # 期货特有信息
                        'delivery_year': int(raw_data.get('delivery_year', 0)) if self._is_valid_number(raw_data.get('delivery_year')) else 0,
                        'delivery_month': int(raw_data.get('delivery_month', 0)) if self._is_valid_number(raw_data.get('delivery_month')) else 0,
                        
                        # 原始数据（保留所有TQSdk返回的字段）
                        'raw_data': raw_data
                    }
                    
                    return contract_info
                else:
                    logger.warning(f"⚠️ 合约 {normalized_symbol} 不在缓存中，无法获取信息")
                    return {}
            except Exception as e:
                logger.error(f"❌ 查询合约信息失败1 {normalized_symbol}: {e}")
                adapter.api.wait_update(deadline=time.time() + 2 )  # 确保API状态更新
                return {}
                
        except Exception as e:
            logger.error(f"❌ 获取合约信息失败 {symbol}: {e}")
            adapter.api.wait_update(deadline=time.time() + 2)  # 确保API状态更新
            return {}
    
    def _is_valid_number(self, value) -> bool:
        """检查值是否为有效数字（非NaN）"""
        if value is None:
            return False
        try:
            import math
            return not math.isnan(float(value))
        except (ValueError, TypeError):
            return False
    
    def _extract_underlying_from_symbol(self, symbol: str) -> str:
        """从合约代码中提取基础品种代码"""
        if 'KQ.i@' in symbol:
            # 指数合约格式: KQ.i@SHFE.cu
            return symbol.replace('KQ.i@', '').split('.')[1].upper()
        elif 'KQ.m@' in symbol:
            # 主连合约格式: KQ.m@SHFE.cu  
            return symbol.replace('KQ.m@', '').split('.')[1].upper()
        elif '.' in symbol:
            # 标准格式: SHFE.cu2501
            parts = symbol.split('.')[1]
            import re
            match = re.match(r'^([A-Za-z]+)', parts)
            return match.group(1).upper() if match else parts.upper()
        else:
            # 简单格式
            import re
            match = re.match(r'^([A-Za-z]+)', symbol)
            return match.group(1).upper() if match else symbol.upper()
    
    def _get_contract_name(self, symbol: str) -> str:
        """获取合约中文名称"""
        underlying = self._extract_underlying_from_symbol(symbol)
        # 这里可以扩展为更具体的品种名称映射
        return f'期货{underlying}'
    
    def _get_exchange_name(self, symbol: str) -> str:
        """获取交易所中文名称"""
        if '.' in symbol:
            exchange_code = symbol.split('.')[0]
            if 'KQ.i@' in symbol or 'KQ.m@' in symbol:
                exchange_code = symbol.replace('KQ.i@', '').replace('KQ.m@', '').split('.')[0]
            
            exchange_mapping = {
                'SHFE': '上海期货交易所',
                'DCE': '大连商品交易所', 
                'CZCE': '郑州商品交易所',
                'CFFEX': '中国金融期货交易所',
                'INE': '上海国际能源交易中心',
                'GFEX': '广州期货交易所'
            }
            return exchange_mapping.get(exchange_code, '未知交易所')
        return '未知交易所'
    
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

    def get_available_contracts(self, product_id: str = None) -> Dict[str, List[str]]:
        """
        获取可用的合约信息
        
        Args:
            product_id: 品种代码过滤
            
        Returns:
            Dict: 包含指数、主连、期货合约的字典
        """
        self._sync_refresh_contracts()
        
        result = {
            "index_contracts": [],
            "main_contracts": [],
            "futures_contracts": {}
        }
        
        if product_id:
            product_id = product_id.upper()
            # 过滤指数合约
            result["index_contracts"] = [c for c in self._index_contracts if product_id in c.upper()]
            # 过滤主连合约
            result["main_contracts"] = [c for c in self._main_contracts if product_id in c.upper()]
            # 过滤期货合约
            for exchange, contracts in self._futures_contracts.items():
                filtered = [c for c in contracts if product_id in c.upper()]
                if filtered:
                    result["futures_contracts"][exchange] = filtered
        else:
            result["index_contracts"] = self._index_contracts.copy()
            result["main_contracts"] = self._main_contracts.copy()
            result["futures_contracts"] = self._futures_contracts.copy()
        
        return result

# 全局单例实例
_contract_manager = None

def get_contract_manager() -> FuturesContractManager:
    """获取期货合约管理器单例"""
    global _contract_manager
    if _contract_manager is None:
        _contract_manager = FuturesContractManager()
    return _contract_manager