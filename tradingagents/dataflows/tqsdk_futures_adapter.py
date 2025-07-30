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

warnings.filterwarnings('ignore')


class TqSdkFuturesAdapter:
    """天勤期货数据适配器"""
    
    def __init__(self, username: str = None, password: str = None):
        """
        初始化天勤适配器
        
        Args:
            username: 天勤用户名
            password: 天勤密码
        """
        self.username = username or os.getenv('TQSDK_USERNAME')
        self.password = password or os.getenv('TQSDK_PASSWORD')
        self.api = None
        self.is_connected = False
        
        # 期货指数合约映射表
        self.index_contracts = {
            # 上期所
            'CU': 'SHFE.CU99',    # 沪铜指数
            'AL': 'SHFE.AL99',    # 沪铝指数
            'ZN': 'SHFE.ZN99',    # 沪锌指数
            'PB': 'SHFE.PB99',    # 沪铅指数
            'NI': 'SHFE.NI99',    # 沪镍指数
            'SN': 'SHFE.SN99',    # 沪锡指数
            'AU': 'SHFE.AU99',    # 黄金指数
            'AG': 'SHFE.AG99',    # 白银指数
            'RB': 'SHFE.RB99',    # 螺纹钢指数
            'HC': 'SHFE.HC99',    # 热卷指数
            'SS': 'SHFE.SS99',    # 不锈钢指数
            'FU': 'SHFE.FU99',    # 燃料油指数
            'BU': 'SHFE.BU99',    # 沥青指数
            'RU': 'SHFE.RU99',    # 橡胶指数
            
            # 大商所
            'C': 'DCE.C99',       # 玉米指数
            'CS': 'DCE.CS99',     # 玉米淀粉指数
            'A': 'DCE.A99',       # 豆一指数
            'B': 'DCE.B99',       # 豆二指数
            'M': 'DCE.M99',       # 豆粕指数
            'Y': 'DCE.Y99',       # 豆油指数
            'P': 'DCE.P99',       # 棕榈油指数
            'J': 'DCE.J99',       # 焦炭指数
            'JM': 'DCE.JM99',     # 焦煤指数
            'I': 'DCE.I99',       # 铁矿石指数
            'JD': 'DCE.JD99',     # 鸡蛋指数
            'L': 'DCE.L99',       # 聚乙烯指数
            'V': 'DCE.V99',       # PVC指数
            'PP': 'DCE.PP99',     # 聚丙烯指数
            
            # 郑商所
            'CF': 'CZCE.CF99',    # 棉花指数
            'SR': 'CZCE.SR99',    # 白糖指数
            'TA': 'CZCE.TA99',    # PTA指数
            'OI': 'CZCE.OI99',    # 菜油指数
            'MA': 'CZCE.MA99',    # 甲醇指数
            'ZC': 'CZCE.ZC99',    # 动力煤指数
            'FG': 'CZCE.FG99',    # 玻璃指数
            'RM': 'CZCE.RM99',    # 菜粕指数
            'AP': 'CZCE.AP99',    # 苹果指数
            'CJ': 'CZCE.CJ99',    # 红枣指数
            'UR': 'CZCE.UR99',    # 尿素指数
            'SA': 'CZCE.SA99',    # 纯碱指数
            'PF': 'CZCE.PF99',    # 短纤指数
            
            # 中金所
            'IF': 'CFFEX.IF99',   # 沪深300股指指数
            'IH': 'CFFEX.IH99',   # 上证50股指指数
            'IC': 'CFFEX.IC99',   # 中证500股指指数
            'IM': 'CFFEX.IM99',   # 中证1000股指指数
            'T': 'CFFEX.T99',     # 10年期国债指数
            'TF': 'CFFEX.TF99',   # 5年期国债指数
            'TS': 'CFFEX.TS99',   # 2年期国债指数
            
            # 上海国际能源中心
            'SC': 'INE.SC99',     # 原油指数
            'LU': 'INE.LU99',     # 低硫燃料油指数
            'BC': 'INE.BC99',     # 国际铜指数
            
            # 广期所
            'SI': 'GFEX.SI99',    # 工业硅指数
            'LC': 'GFEX.LC99',    # 碳酸锂指数
        }
        
        # 期货品种中文名称
        self.futures_names = {
            'CU': '沪铜', 'AL': '沪铝', 'ZN': '沪锌', 'PB': '沪铅', 'NI': '沪镍',
            'SN': '沪锡', 'AU': '黄金', 'AG': '白银', 'RB': '螺纹钢', 'HC': '热卷',
            'SS': '不锈钢', 'FU': '燃料油', 'BU': '沥青', 'RU': '橡胶',
            'C': '玉米', 'CS': '玉米淀粉', 'A': '豆一', 'B': '豆二', 'M': '豆粕',
            'Y': '豆油', 'P': '棕榈油', 'J': '焦炭', 'JM': '焦煤', 'I': '铁矿石',
            'JD': '鸡蛋', 'L': '聚乙烯', 'V': 'PVC', 'PP': '聚丙烯',
            'CF': '棉花', 'SR': '白糖', 'TA': 'PTA', 'OI': '菜油', 'MA': '甲醇',
            'ZC': '动力煤', 'FG': '玻璃', 'RM': '菜粕', 'AP': '苹果', 'CJ': '红枣',
            'UR': '尿素', 'SA': '纯碱', 'PF': '短纤',
            'IF': '沪深300股指', 'IH': '上证50股指', 'IC': '中证500股指', 'IM': '中证1000股指',
            'T': '10年期国债', 'TF': '5年期国债', 'TS': '2年期国债',
            'SC': '原油', 'LU': '低硫燃料油', 'BC': '国际铜',
            'SI': '工业硅', 'LC': '碳酸锂'
        }

    async def connect(self):
        """建立天勤连接"""
        try:
            if self.is_connected:
                return True
                
            # 检查是否需要认证
            if self.username and self.password:
                from tqsdk import TqApi, TqAuth
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
        标准化期货代码
        
        Args:
            symbol: 输入的期货代码，如 'CU'、'cu'、'CU99'、'SHFE.CU99'
            
        Returns:
            str: 标准化的天勤格式代码，如 'SHFE.CU99'
        """
        symbol = symbol.upper().strip()
        
        # 如果已经是完整格式，直接返回
        if '.' in symbol and '99' in symbol:
            return symbol
        
        # 移除数字后缀，提取品种代码
        if symbol.endswith('99'):
            symbol = symbol[:-2]
        elif len(symbol) > 2 and symbol[-2:].isdigit():
            symbol = symbol[:-2]
        elif len(symbol) > 4 and symbol[-4:].isdigit():
            symbol = symbol[:-4]
        
        # 查找对应的指数合约
        if symbol in self.index_contracts:
            return self.index_contracts[symbol]
        
        # 如果找不到，尝试推测交易所
        if symbol in ['IF', 'IH', 'IC', 'IM', 'T', 'TF', 'TS']:
            return f'CFFEX.{symbol}99'
        elif symbol in ['SC', 'LU', 'BC']:
            return f'INE.{symbol}99'
        elif symbol in ['SI', 'LC']:
            return f'GFEX.{symbol}99'
        elif symbol in ['CU', 'AL', 'ZN', 'PB', 'NI', 'SN', 'AU', 'AG', 'RB', 'HC', 'SS', 'FU', 'BU', 'RU']:
            return f'SHFE.{symbol}99'
        elif symbol in ['C', 'CS', 'A', 'B', 'M', 'Y', 'P', 'J', 'JM', 'I', 'JD', 'L', 'V', 'PP']:
            return f'DCE.{symbol}99'
        else:
            return f'CZCE.{symbol}99'

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
        underlying = self._extract_underlying(symbol)
        normalized_symbol = self._normalize_symbol(symbol)
        
        # 获取交易所信息
        exchange = normalized_symbol.split('.')[0] if '.' in normalized_symbol else 'UNKNOWN'
        
        exchange_names = {
            'SHFE': '上海期货交易所',
            'DCE': '大连商品交易所', 
            'CZCE': '郑州商品交易所',
            'CFFEX': '中国金融期货交易所',
            'INE': '上海国际能源交易中心',
            'GFEX': '广州期货交易所'
        }
        
        return {
            'symbol': normalized_symbol,
            'underlying': underlying,
            'name': self.futures_names.get(underlying, f'期货{underlying}'),
            'exchange': exchange,
            'exchange_name': exchange_names.get(exchange, '未知交易所'),
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

    def search_futures(self, keyword: str) -> str:
        """
        搜索期货品种
        
        Args:
            keyword: 搜索关键词
            
        Returns:
            str: 搜索结果
        """
        try:
            results = []
            keyword = keyword.upper()
            
            # 搜索匹配的期货品种
            for symbol, name in self.futures_names.items():
                if keyword in symbol or keyword in name:
                    contract = self.index_contracts.get(symbol, f'{symbol}99')
                    exchange = contract.split('.')[0] if '.' in contract else 'UNKNOWN'
                    results.append({
                        'symbol': symbol,
                        'name': name,
                        'contract': contract,
                        'exchange': exchange
                    })
            
            if not results:
                return f"❌ 未找到匹配'{keyword}'的期货品种"
            
            result = f"🔍 搜索关键词: {keyword}\n"
            result += f"找到 {len(results)} 个期货品种:\n\n"
            
            for item in results[:10]:  # 最多显示10个结果
                result += f"代码: {item['symbol']}\n"
                result += f"名称: {item['name']}\n"
                result += f"合约: {item['contract']}\n"
                result += f"交易所: {item['exchange']}\n"
                result += "-" * 30 + "\n"
            
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