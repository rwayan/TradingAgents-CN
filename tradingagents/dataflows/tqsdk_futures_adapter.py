#!/usr/bin/env python3
"""
天勤期货数据适配器
使用TqSdk获取期货指数合约数据，支持实时行情和历史数据
"""

import os
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import pandas as pd
from decimal import Decimal
import warnings

# 导入统一日志系统
from tradingagents.utils.logging_init import setup_dataflow_logging
logger = setup_dataflow_logging()

# 导入期货合约管理器
from .futures_contract_manager import get_contract_manager

warnings.filterwarnings('ignore')


class TqSdkFuturesAdapter:
    """天勤期货数据适配器"""
    
    def __init__(self, username: str = "test", password: str = "test"):
        """
        初始化天勤适配器
        
        Args:
            username: 天勤用户名
            password: 天勤密码
        """
        self.username = "username"
        self.password = "password"
        self.api = None
        self.is_connected = False
        
        # 使用期货合约管理器
        self.contract_manager = get_contract_manager()
        
        logger.info("🔧 天勤期货数据适配器初始化完成")

    async def connect(self):
        """建立天勤连接"""
        try:
            if self.is_connected:
                return True
                
            # 检查是否需要认证
            if self.username and self.password:
                from tqsdk import TqApi
                # 这里我需要判断tqsdk_utility.py是否存在, 如果存在从中导入TqCustomAuth
                if os.path.exists('tradingagents/dataflows/tqsdk_utility.py') or os.path.exists('tqsdk_utility.py'):
                    from .tqsdk_utility import TqCustomAuth as TqAuth
                    logger.info("🔗 使用自定义TqCustomAuth进行认证...")
                else:
                    # 如果不存在，直接使用TqAuth
                    from tqsdk import TqAuth
                    logger.warning("⚠️ 未找到tqsdk_utility.py，使用默认TqAuth")
                # 使用认证方式连接天勤API
                logger.info(f"🔗 使用认证方式连接天勤API...")
                auth = TqAuth(self.username, self.password)
                self.api = TqApi(auth=auth, web_gui=False)
            else:
                # 使用免费模式
                from tqsdk import TqApi
                logger.info(f"🔗 使用免费模式连接天勤API...")
                self.api = TqApi(web_gui=False)
            
            self.is_connected = True
            logger.info(f"✅ 天勤API连接成功")
            return True
            
        except Exception as e:
            logger.error(f"❌ 天勤API连接失败: {e}")
            self.is_connected = False
            return False

    def disconnect(self):
        """断开天勤连接"""
        if self.api:
            try:
                self.api.close()
                logger.info(f"🔗 天勤API连接已断开")
            except Exception as e:
                logger.warning(f"⚠️ 断开天勤API连接时出现异常: {e}")
        
        self.api = None
        self.is_connected = False

    def _normalize_symbol(self, symbol: str) -> str:
        """
        标准化期货代码，保持用户输入的具体月份合约格式
        
        Args:
            symbol: 输入的期货代码，如 'CU'、'cu2509'、'CU2501'、'SHFE.CU2501'
            
        Returns:
            str: 标准化的天勤格式代码，保持用户输入的月份格式
        """
        original_symbol = symbol.strip()  # 保持用户原始输入的大小写
        symbol = symbol.upper().strip()  # 用于匹配的大写版本
        
        # 如果已经是完整格式，直接返回
        if '.' in symbol:
            return original_symbol
        
        # 检查是否为具体月份合约（包含数字）
        import re
        match = re.match(r'^([A-Za-z]+)(\d{3,4})$', original_symbol)
        if match:
            base_symbol = match.group(1)
            month_code = match.group(2)
            
            # 直接通过指数合约获取交易所信息
            index_code = self.contract_manager.get_index_code(base_symbol.upper())
            if index_code:
                # 从指数合约中提取交易所，格式如 KQ.i@SHFE.cu -> SHFE
                if 'KQ.i@' in index_code:
                    exchange_part = index_code.replace('KQ.i@', '').split('.')[0]
                    product_part = index_code.replace('KQ.i@', '').split('.')[1]
                else:
                    exchange_part = index_code.split('.')[0]
                    product_part = index_code.split('.')[1]
                
                # 构建用户要求的月份合约，保持用户原始大小写
                user_contract = f"{exchange_part}.{product_part}{month_code}"
                logger.debug(f"🔍 构建用户输入的月份合约: {user_contract}")
                return user_contract
        
        # 如果用户只输入了品种代码（如CU），使用指数合约作为兜底
        parsed_symbol, is_index = self.contract_manager.parse_futures_code(symbol)
        if parsed_symbol:
            full_code = self.contract_manager.get_full_code(parsed_symbol)
            if full_code:
                logger.debug(f"🔍 使用指数合约作为兜底: {full_code}")
                return full_code
        
        # 如果解析失败，尝试直接从输入构建
        if symbol.endswith('99'):
            base_symbol = symbol[:-2]
        elif len(symbol) > 2 and symbol[-2:].isdigit():
            base_symbol = symbol[:-2]
        elif len(symbol) > 4 and symbol[-4:].isdigit():
            base_symbol = symbol[:-4]
        else:
            base_symbol = symbol
        
        # 尝试获取完整代码（作为最后的兜底）
        full_code = self.contract_manager.get_full_code(base_symbol)
        if full_code:
            return full_code
        
        # 最后的兜底逻辑
        logger.warning(f"⚠️ 无法识别期货代码: {symbol}，返回原始代码")
        return original_symbol

    def get_futures_name(self, symbol: str) -> str:
        """获取期货品种中文名称"""
        parsed_symbol, is_index = self.contract_manager.parse_futures_code(symbol)
        if parsed_symbol:
            contract = self.contract_manager.get_contract(parsed_symbol)
            if contract:
                return contract['name']
        return f'期货{symbol.upper()}'

    def _extract_underlying(self, symbol: str) -> str:
        """提取期货品种代码"""
        normalized = self._normalize_symbol(symbol)
        if '.' in normalized:
            return normalized.split('.')[1].replace('99', '')
        return symbol.upper()

    def get_futures_info(self, symbol: str) -> Dict[str, Any]:
        """
        获取期货品种基本信息
        
        Args:
            symbol: 期货代码
            
        Returns:
            Dict: 期货基本信息
        """
        parsed_symbol, is_index = self.contract_manager.parse_futures_code(symbol)
        
        if parsed_symbol:
            contract = self.contract_manager.get_contract(parsed_symbol)
            if contract:
                return {
                    'symbol': contract['full_code'],
                    'underlying': contract['symbol'],
                    'name': contract['name'],
                    'exchange': contract.get('exchange', 'UNKNOWN'),
                    'exchange_name': contract.get('exchange_name', '未知交易所'),
                    'category': contract.get('category', '未知分类'),
                    'multiplier': contract.get('multiplier', 1),
                    'min_change': contract.get('min_change', 0.01),
                    'margin_rate': contract.get('margin_rate', 0.1),
                    'trading_unit': contract.get('trading_unit', '1手'),
                    'is_futures': True,
                    'is_index_contract': contract.get('is_index', False),
                    'contract_type': contract.get('contract_type', 'UNKNOWN'),
                    'currency': 'CNY'
                }
        
        # 兜底处理
        normalized_symbol = self._normalize_symbol(symbol)
        underlying = self._extract_underlying(symbol)
        
        return {
            'symbol': normalized_symbol,
            'underlying': underlying,
            'name': self.get_futures_name(symbol),
            'exchange': normalized_symbol.split('.')[0] if '.' in normalized_symbol else 'UNKNOWN',
            'exchange_name': '未知交易所',
            'is_futures': True,
            'is_index_contract': True,
            'currency': 'CNY'
        }

    async def get_realtime_quote(self, symbol: str) -> Dict[str, Any]:
        """
        获取实时行情
        
        Args:
            symbol: 期货代码
            
        Returns:
            Dict: 实时行情数据
        """
        if not await self.connect():
            raise Exception("无法连接到天勤API")
        
        try:
            normalized_symbol = self._normalize_symbol(symbol)
            logger.debug(f"📊 获取{normalized_symbol}实时行情...")
            
            quote = self.api.get_quote(normalized_symbol)
            
            if not quote:
                raise Exception(f"无法获取{normalized_symbol}的行情数据")
            
            # 等待数据更新
            await asyncio.sleep(0.5)
            
            return {
                'symbol': normalized_symbol,
                'last_price': float(quote.last_price) if quote.last_price and quote.last_price == quote.last_price else 0,
                'open_price': float(quote.open) if quote.open and quote.open == quote.open else 0,
                'high_price': float(quote.highest) if quote.highest and quote.highest == quote.highest else 0,
                'low_price': float(quote.lowest) if quote.lowest and quote.lowest == quote.lowest else 0,
                'pre_close': float(quote.pre_close) if quote.pre_close and quote.pre_close == quote.pre_close else 0,
                'pre_settlement': float(quote.pre_settlement) if quote.pre_settlement and quote.pre_settlement == quote.pre_settlement else 0,
                'settlement': float(quote.settlement) if quote.settlement and quote.settlement == quote.settlement else 0,
                'volume': int(quote.volume) if quote.volume and quote.volume == quote.volume else 0,
                'amount': float(quote.amount) if quote.amount and quote.amount == quote.amount else 0,
                'open_interest': int(quote.open_interest) if quote.open_interest and quote.open_interest == quote.open_interest else 0,
                'upper_limit': float(quote.upper_limit) if quote.upper_limit and quote.upper_limit == quote.upper_limit else 0,
                'lower_limit': float(quote.lower_limit) if quote.lower_limit and quote.lower_limit == quote.lower_limit else 0,
                'average': float(quote.average) if quote.average and quote.average == quote.average else 0,
                'change': 0,
                'change_percent': 0,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"❌ 获取{symbol}实时行情失败: {e}")
            raise

    async def get_historical_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        获取历史数据
        
        Args:
            symbol: 期货代码
            start_date: 开始日期 'YYYY-MM-DD'
            end_date: 结束日期 'YYYY-MM-DD'
            
        Returns:
            pd.DataFrame: 历史数据
        """
        if not await self.connect():
            raise Exception("无法连接到天勤API")
        
        try:
            normalized_symbol = self._normalize_symbol(symbol)
            logger.debug(f"📊 获取{normalized_symbol}历史数据: {start_date} 至 {end_date}")
            
            # 计算数据长度（天数）
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d') 
            days = (end_dt - start_dt).days + 1
            
            # 获取K线数据
            klines = self.api.get_kline_serial(
                normalized_symbol, 
                duration_seconds=24*3600,  # 日线
                data_length=days * 2  # 获取更多数据以确保覆盖时间范围
            )
            
            if klines is None or klines.empty:
                logger.warning(f"⚠️ 未获取到{normalized_symbol}的历史数据")
                return pd.DataFrame()
            
            # 复制数据并处理
            df = klines.copy()
            
            # 确保有datetime列
            if 'datetime' not in df.columns and df.index.name == 'datetime':
                df.reset_index(inplace=True)
            
            # 转换日期格式
            df['date'] = pd.to_datetime(df['datetime']).dt.date
            
            # 筛选日期范围
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
            df = df[(df['date'] >= start_date_obj) & (df['date'] <= end_date_obj)]
            
            # 重命名列以保持一致性
            column_mapping = {
                'open': 'open',
                'high': 'high', 
                'low': 'low',
                'close': 'close',
                'volume': 'volume',
                'close_oi': 'open_interest'
            }
            
            df = df.rename(columns=column_mapping)
            
            # 确保必要的列存在
            required_columns = ['date', 'open', 'high', 'low', 'close', 'volume']
            for col in required_columns:
                if col not in df.columns:
                    df[col] = 0
            
            # 添加其他有用信息
            df['symbol'] = normalized_symbol
            
            logger.debug(f"✅ 获取到{len(df)}条{normalized_symbol}历史数据")
            return df[required_columns + ['symbol', 'open_interest']].copy()
            
        except Exception as e:
            logger.error(f"❌ 获取{symbol}历史数据失败: {e}")
            return pd.DataFrame()

    def get_futures_data(self, symbol: str, start_date: str, end_date: str) -> str:
        """
        获取期货数据的统一接口（同步版本）
        
        Args:
            symbol: 期货代码
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            str: 格式化的期货数据报告
        """
        try:
            # 获取期货基本信息
            futures_info = self.get_futures_info(symbol)
            
            # 运行异步函数获取历史数据
            loop = None
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            if loop.is_running():
                # 如果事件循环正在运行，创建任务
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        lambda: asyncio.run(self.get_historical_data(symbol, start_date, end_date))
                    )
                    data = future.result(timeout=30)
            else:
                # 如果事件循环没有运行，直接运行
                data = loop.run_until_complete(self.get_historical_data(symbol, start_date, end_date))
            
            if data.empty:
                return f"❌ 未获取到{futures_info['name']}({symbol})的数据"
            
            # 计算最新价格信息
            latest_data = data.iloc[-1]
            latest_price = latest_data['close']
            prev_close = data.iloc[-2]['close'] if len(data) > 1 else latest_price
            change = latest_price - prev_close
            change_pct = (change / prev_close * 100) if prev_close != 0 else 0
            
            # 格式化数据报告
            result = f"📊 {futures_info['name']}({futures_info['symbol']}) - 天勤期货数据\n"
            result += f"交易所: {futures_info['exchange_name']}\n"
            result += f"数据期间: {start_date} 至 {end_date}\n"
            result += f"数据条数: {len(data)}条\n\n"
            
            result += f"💰 最新价格: ¥{latest_price:.2f}\n"
            result += f"📈 涨跌额: {change:+.2f} ({change_pct:+.2f}%)\n\n"
            
            # 添加统计信息
            result += f"📊 价格统计:\n"
            result += f"   最高价: ¥{data['high'].max():.2f}\n"
            result += f"   最低价: ¥{data['low'].min():.2f}\n"
            result += f"   平均价: ¥{data['close'].mean():.2f}\n"
            result += f"   成交量: {data['volume'].sum():,.0f}手\n"
            if 'open_interest' in data.columns:
                result += f"   持仓量: {data['open_interest'].iloc[-1]:,.0f}手\n"
            
            result += f"\n📈 最近5日数据:\n"
            recent_data = data.tail(5)[['date', 'open', 'high', 'low', 'close', 'volume']].copy()
            result += recent_data.to_string(index=False, float_format='%.2f')
            
            logger.info(f"✅ 成功获取{futures_info['name']}数据，{len(data)}条记录")
            return result
            
        except Exception as e:
            logger.error(f"❌ 获取期货数据失败: {e}")
            return f"❌ 获取期货数据失败: {str(e)}"

    async def query_quotes(self, ins_class=None, exchange_id=None, product_id=None, expired=None, has_night=None):
        """
        根据条件查询合约列表
        
        Args:
            ins_class: 合约类型 ("FUTURE", "INDEX", "CONT", "OPTION", "STOCK")
            exchange_id: 交易所 ("SHFE", "DCE", "CZCE", "CFFEX", "INE", "GFEX")
            product_id: 品种代码
            expired: 是否已下市
            has_night: 是否有夜盘
            
        Returns:
            List[str]: 符合条件的合约代码列表
        """
        if not await self.connect():
            raise Exception("无法连接到天勤API")
        
        try:
            quotes = self.api.query_quotes(
                ins_class=ins_class,
                exchange_id=exchange_id,
                product_id=product_id,
                expired=expired,
                has_night=has_night
            )
            return quotes
        except Exception as e:
            logger.error(f"❌ 查询合约失败: {e}")
            return []

    async def get_index_contracts(self, product_id=None):
        """
        获取指数合约
        
        Args:
            product_id: 品种代码，如 "cu", "au" 等
            
        Returns:
            List[str]: 指数合约列表
        """
        return await self.query_quotes(ins_class="INDEX", product_id=product_id, expired=False)

    async def get_main_contracts(self, product_id=None):
        """
        获取主连合约
        
        Args:
            product_id: 品种代码，如 "cu", "au" 等
            
        Returns:
            List[str]: 主连合约列表
        """
        return await self.query_quotes(ins_class="CONT", product_id=product_id)

    def search_futures(self, keyword: str) -> str:
        """
        搜索期货品种
        
        Args:
            keyword: 搜索关键词
            
        Returns:
            str: 搜索结果
        """
        try:
            # 使用query_quotes搜索相关合约
            loop = None
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            # 搜索期货合约
            futures_contracts = []
            index_contracts = []
            main_contracts = []
            
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    # 搜索期货合约
                    future_futures = executor.submit(
                        lambda: asyncio.run(self.query_quotes(ins_class="FUTURE", product_id=keyword.lower(), expired=False))
                    )
                    # 搜索指数合约
                    future_index = executor.submit(
                        lambda: asyncio.run(self.query_quotes(ins_class="INDEX", product_id=keyword.lower()))
                    )
                    # 搜索主连合约
                    future_main = executor.submit(
                        lambda: asyncio.run(self.query_quotes(ins_class="CONT", product_id=keyword.lower()))
                    )
                    
                    futures_contracts = future_futures.result(timeout=10)
                    index_contracts = future_index.result(timeout=10)
                    main_contracts = future_main.result(timeout=10)
            else:
                futures_contracts = loop.run_until_complete(self.query_quotes(ins_class="FUTURE", product_id=keyword.lower(), expired=False))
                index_contracts = loop.run_until_complete(self.query_quotes(ins_class="INDEX", product_id=keyword.lower()))
                main_contracts = loop.run_until_complete(self.query_quotes(ins_class="CONT", product_id=keyword.lower()))
            
            if not futures_contracts and not index_contracts and not main_contracts:
                return f"❌ 未找到匹配'{keyword}'的期货品种"
            
            result = f"🔍 搜索关键词: {keyword}\n\n"
            
            if index_contracts:
                result += f"📊 指数合约 ({len(index_contracts)}个):\n"
                for contract in index_contracts[:5]:
                    result += f"  {contract}\n"
                result += "\n"
            
            if main_contracts:
                result += f"🔗 主连合约 ({len(main_contracts)}个):\n"
                for contract in main_contracts[:5]:
                    result += f"  {contract}\n"
                result += "\n"
            
            if futures_contracts:
                result += f"📈 期货合约 ({len(futures_contracts)}个，显示前10个):\n"
                for contract in futures_contracts[:10]:
                    result += f"  {contract}\n"
            
            return result
            
        except Exception as e:
            logger.error(f"❌ 搜索期货品种失败: {e}")
            return f"❌ 搜索期货品种失败: {str(e)}"

    def is_futures_symbol(self, symbol: str) -> bool:
        """
        判断是否为期货代码
        
        Args:
            symbol: 待检查的代码
            
        Returns:
            bool: 是否为期货代码
        """
        try:
            underlying = self._extract_underlying(symbol)
            return underlying in self.futures_names
        except:
            return False

    def __del__(self):
        """析构函数，确保连接被关闭"""
        if hasattr(self, 'api') and self.api:
            try:
                self.disconnect()
            except:
                pass


# 全局适配器实例
_tqsdk_adapter = None

def get_tqsdk_futures_adapter() -> TqSdkFuturesAdapter:
    """获取全局天勤期货适配器实例"""
    global _tqsdk_adapter
    if _tqsdk_adapter is None:
        username = os.getenv('TQSDK_USERNAME')
        password = os.getenv('TQSDK_PASSWORD')
        _tqsdk_adapter = TqSdkFuturesAdapter(username, password)
    return _tqsdk_adapter


# 统一接口函数
def get_futures_data_tqsdk(symbol: str, start_date: str, end_date: str) -> str:
    """
    获取期货数据的统一接口
    
    Args:
        symbol: 期货代码
        start_date: 开始日期
        end_date: 结束日期
        
    Returns:
        str: 格式化的期货数据
    """
    adapter = get_tqsdk_futures_adapter()
    return adapter.get_futures_data(symbol, start_date, end_date)


def search_futures_tqsdk(keyword: str) -> str:
    """
    搜索期货品种的统一接口
    
    Args:
        keyword: 搜索关键词
        
    Returns:
        str: 搜索结果
    """
    adapter = get_tqsdk_futures_adapter()
    return adapter.search_futures(keyword)


def get_futures_info_tqsdk(symbol: str) -> Dict[str, Any]:
    """
    获取期货基本信息的统一接口
    
    Args:
        symbol: 期货代码
        
    Returns:
        Dict: 期货基本信息
    """
    adapter = get_tqsdk_futures_adapter()
    return adapter.get_futures_info(symbol)


def query_quotes_tqsdk(ins_class=None, exchange_id=None, product_id=None, expired=None, has_night=None):
    """
    查询合约列表的统一接口
    
    Args:
        ins_class: 合约类型 ("FUTURE", "INDEX", "CONT", "OPTION", "STOCK")
        exchange_id: 交易所 ("SHFE", "DCE", "CZCE", "CFFEX", "INE", "GFEX")
        product_id: 品种代码
        expired: 是否已下市
        has_night: 是否有夜盘
        
    Returns:
        List[str]: 符合条件的合约代码列表
    """
    import asyncio
    adapter = get_tqsdk_futures_adapter()
    
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
                lambda: asyncio.run(adapter.query_quotes(ins_class, exchange_id, product_id, expired, has_night))
            )
            return future.result(timeout=10)
    else:
        return loop.run_until_complete(adapter.query_quotes(ins_class, exchange_id, product_id, expired, has_night))


def get_index_contracts_tqsdk(product_id=None):
    """
    获取指数合约的统一接口
    
    Args:
        product_id: 品种代码，如 "cu", "au" 等
        
    Returns:
        List[str]: 指数合约列表
    """
    return query_quotes_tqsdk(ins_class="INDEX", product_id=product_id, expired=False)


def get_main_contracts_tqsdk(product_id=None):
    """
    获取主连合约的统一接口
    
    Args:
        product_id: 品种代码，如 "cu", "au" 等
        
    Returns:
        List[str]: 主连合约列表
    """
    return query_quotes_tqsdk(ins_class="CONT", product_id=product_id)