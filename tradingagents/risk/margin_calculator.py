#!/usr/bin/env python3
"""
期货保证金计算器
计算期货交易的保证金需求、风险暴露和强平风险
"""

import os
from typing import Dict, List, Optional, Tuple
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime
import warnings

# 导入统一日志系统
from tradingagents.utils.logging_init import setup_dataflow_logging
logger = setup_dataflow_logging()

warnings.filterwarnings('ignore')


class MarginCalculator:
    """期货保证金计算器"""
    
    def __init__(self):
        """初始化保证金计算器"""
        
        # 交易所标准保证金比例（基础保证金）
        self.exchange_margin_rates = {
            # 中金所 - 金融期货
            'IF': Decimal('0.12'),    # 沪深300股指期货 12%
            'IH': Decimal('0.12'),    # 上证50股指期货 12%
            'IC': Decimal('0.12'),    # 中证500股指期货 12%
            'IM': Decimal('0.12'),    # 中证1000股指期货 12%
            'T': Decimal('0.015'),    # 10年期国债期货 1.5%
            'TF': Decimal('0.012'),   # 5年期国债期货 1.2%
            'TS': Decimal('0.005'),   # 2年期国债期货 0.5%
            
            # 上期所 - 有色金属和贵金属
            'CU': Decimal('0.08'),    # 沪铜 8%
            'AL': Decimal('0.07'),    # 沪铝 7%
            'ZN': Decimal('0.08'),    # 沪锌 8%
            'PB': Decimal('0.08'),    # 沪铅 8%
            'NI': Decimal('0.08'),    # 沪镍 8%
            'SN': Decimal('0.07'),    # 沪锡 7%
            'AU': Decimal('0.06'),    # 黄金 6%
            'AG': Decimal('0.08'),    # 白银 8%
            'RB': Decimal('0.09'),    # 螺纹钢 9%
            'HC': Decimal('0.08'),    # 热卷 8%
            'SS': Decimal('0.08'),    # 不锈钢 8%
            'FU': Decimal('0.10'),    # 燃料油 10%
            'BU': Decimal('0.08'),    # 沥青 8%
            'RU': Decimal('0.09'),    # 橡胶 9%
            
            # 大商所 - 农产品和化工
            'C': Decimal('0.05'),     # 玉米 5%
            'CS': Decimal('0.05'),    # 玉米淀粉 5%
            'A': Decimal('0.05'),     # 豆一 5%
            'B': Decimal('0.05'),     # 豆二 5%
            'M': Decimal('0.05'),     # 豆粕 5%
            'Y': Decimal('0.05'),     # 豆油 5%
            'P': Decimal('0.05'),     # 棕榈油 5%
            'J': Decimal('0.08'),     # 焦炭 8%
            'JM': Decimal('0.08'),    # 焦煤 8%
            'I': Decimal('0.08'),     # 铁矿石 8%
            'JD': Decimal('0.08'),    # 鸡蛋 8%
            'L': Decimal('0.05'),     # 聚乙烯 5%
            'V': Decimal('0.05'),     # PVC 5%
            'PP': Decimal('0.05'),    # 聚丙烯 5%
            
            # 郑商所 - 农产品和化工
            'CF': Decimal('0.05'),    # 棉花 5%
            'SR': Decimal('0.06'),    # 白糖 6%
            'TA': Decimal('0.06'),    # PTA 6%
            'OI': Decimal('0.05'),    # 菜油 5%
            'MA': Decimal('0.06'),    # 甲醇 6%
            'ZC': Decimal('0.06'),    # 动力煤 6%
            'FG': Decimal('0.06'),    # 玻璃 6%
            'RM': Decimal('0.05'),    # 菜粕 5%
            'AP': Decimal('0.10'),    # 苹果 10%
            'CJ': Decimal('0.05'),    # 红枣 5%
            'UR': Decimal('0.05'),    # 尿素 5%
            'SA': Decimal('0.06'),    # 纯碱 6%
            'PF': Decimal('0.05'),    # 短纤 5%
            
            # 上海国际能源中心
            'SC': Decimal('0.10'),    # 原油 10%
            'LU': Decimal('0.08'),    # 低硫燃料油 8%
            'BC': Decimal('0.08'),    # 国际铜 8%
            
            # 广期所
            'SI': Decimal('0.08'),    # 工业硅 8%
            'LC': Decimal('0.12'),    # 碳酸锂 12%
        }
        
        # 合约乘数
        self.contract_multipliers = {
            # 股指期货
            'IF': 300, 'IH': 300, 'IC': 200, 'IM': 200,
            # 国债期货
            'T': 10000, 'TF': 10000, 'TS': 20000,
            # 有色金属（吨）
            'CU': 5, 'AL': 5, 'ZN': 5, 'PB': 5, 'NI': 1, 'SN': 1,
            # 贵金属
            'AU': 1000, 'AG': 15,  # 黄金：千克，白银：千克
            # 黑色系（吨）
            'RB': 10, 'HC': 10, 'SS': 5, 'I': 100, 'J': 100, 'JM': 60,
            # 能源化工（吨）
            'SC': 1000, 'FU': 10, 'LU': 10, 'BU': 10, 'RU': 10,
            'L': 5, 'V': 5, 'PP': 5, 'TA': 5, 'MA': 10,
            # 农产品（吨）
            'C': 10, 'CS': 10, 'A': 10, 'B': 10, 'M': 10, 'Y': 10, 'P': 10,
            'CF': 5, 'SR': 10, 'OI': 10, 'RM': 10, 'AP': 10, 'CJ': 5,
            # 其他
            'ZC': 100, 'FG': 20, 'UR': 20, 'SA': 20, 'PF': 5, 'JD': 10,
            'SI': 10, 'LC': 1, 'BC': 5
        }
        
        # 期货公司通常在交易所基础上加收保证金
        self.broker_margin_multiplier = Decimal('1.2')  # 默认1.2倍
        
        # 风险等级阈值
        self.risk_thresholds = {
            'safe': Decimal('2.0'),        # 保证金充足率200%以上为安全
            'warning': Decimal('1.5'),     # 150%为预警
            'danger': Decimal('1.2'),      # 120%为危险
            'liquidation': Decimal('1.0')  # 100%为强平
        }

    def _extract_underlying(self, symbol: str) -> str:
        """提取期货品种代码"""
        symbol = symbol.upper()
        if symbol.endswith('99'):
            return symbol[:-2]
        elif len(symbol) > 2 and symbol[-2:].isdigit():
            return symbol[:-2]
        elif len(symbol) > 4 and symbol[-4:].isdigit():
            return symbol[:-4]
        elif '.' in symbol:
            return symbol.split('.')[1].replace('99', '')
        return symbol

    def get_margin_rate(self, symbol: str) -> Decimal:
        """
        获取期货品种的保证金比例
        
        Args:
            symbol: 期货代码
            
        Returns:
            Decimal: 保证金比例
        """
        underlying = self._extract_underlying(symbol)
        exchange_rate = self.exchange_margin_rates.get(underlying, Decimal('0.10'))
        actual_rate = exchange_rate * self.broker_margin_multiplier
        
        logger.debug(f"📊 [保证金] {symbol} 保证金比例: 交易所{exchange_rate:.1%} × {self.broker_margin_multiplier} = {actual_rate:.1%}")
        return actual_rate

    def get_contract_multiplier(self, symbol: str) -> int:
        """
        获取期货合约乘数
        
        Args:
            symbol: 期货代码
            
        Returns:
            int: 合约乘数
        """
        underlying = self._extract_underlying(symbol)
        multiplier = self.contract_multipliers.get(underlying, 10)
        
        logger.debug(f"📊 [保证金] {symbol} 合约乘数: {multiplier}")
        return multiplier

    def calculate_position_margin(self, symbol: str, price: Decimal, volume: int, position_type: str = 'long') -> Dict:
        """
        计算持仓保证金
        
        Args:
            symbol: 期货代码
            price: 持仓价格
            volume: 持仓量（手）
            position_type: 持仓方向 'long'多头, 'short'空头
            
        Returns:
            Dict: 保证金计算结果
        """
        try:
            underlying = self._extract_underlying(symbol)
            margin_rate = self.get_margin_rate(symbol)
            multiplier = self.get_contract_multiplier(symbol)
            
            # 计算持仓价值
            position_value = price * volume * multiplier
            
            # 计算保证金需求
            margin_required = position_value * margin_rate
            
            # 计算杠杆倍数
            leverage = Decimal('1') / margin_rate if margin_rate > 0 else Decimal('0')
            
            result = {
                'symbol': symbol,
                'underlying': underlying,
                'price': price,
                'volume': volume,
                'position_type': position_type,
                'position_value': position_value,
                'margin_rate': margin_rate,
                'margin_required': margin_required,
                'contract_multiplier': multiplier,
                'leverage': leverage,
                'currency': 'CNY'
            }
            
            logger.debug(f"💰 [保证金计算] {symbol} {volume}手：价值¥{position_value:,.2f}，保证金¥{margin_required:,.2f}")
            return result
            
        except Exception as e:
            logger.error(f"❌ [保证金计算] 计算失败: {e}")
            raise

    def calculate_portfolio_margin(self, positions: List[Dict]) -> Dict:
        """
        计算投资组合总保证金
        
        Args:
            positions: 持仓列表，每个元素包含 symbol, price, volume, position_type
            
        Returns:
            Dict: 组合保证金信息
        """
        try:
            total_margin_required = Decimal('0')
            total_position_value = Decimal('0')
            position_details = []
            
            for position in positions:
                margin_info = self.calculate_position_margin(
                    position['symbol'],
                    Decimal(str(position['price'])),
                    int(position['volume']),
                    position.get('position_type', 'long')
                )
                
                total_margin_required += margin_info['margin_required']
                total_position_value += margin_info['position_value']
                position_details.append(margin_info)
            
            # 计算加权平均保证金比例
            avg_margin_rate = total_margin_required / total_position_value if total_position_value > 0 else Decimal('0')
            
            result = {
                'total_positions': len(positions),
                'total_position_value': total_position_value,
                'total_margin_required': total_margin_required,
                'average_margin_rate': avg_margin_rate,
                'position_details': position_details,
                'currency': 'CNY',
                'calculation_time': datetime.now()
            }
            
            logger.info(f"💰 [组合保证金] {len(positions)}个持仓：总价值¥{total_position_value:,.2f}，总保证金¥{total_margin_required:,.2f}")
            return result
            
        except Exception as e:
            logger.error(f"❌ [组合保证金计算] 计算失败: {e}")
            raise

    def calculate_available_margin(self, account_balance: Decimal, positions: List[Dict]) -> Dict:
        """
        计算可用保证金
        
        Args:
            account_balance: 账户余额
            positions: 当前持仓列表
            
        Returns:
            Dict: 可用保证金信息
        """
        try:
            # 计算已使用保证金
            portfolio_margin = self.calculate_portfolio_margin(positions)
            used_margin = portfolio_margin['total_margin_required']
            
            # 计算可用保证金
            available_margin = account_balance - used_margin
            
            # 计算保证金使用率
            margin_usage_rate = used_margin / account_balance if account_balance > 0 else Decimal('0')
            
            result = {
                'account_balance': account_balance,
                'used_margin': used_margin,
                'available_margin': max(available_margin, Decimal('0')),
                'margin_usage_rate': margin_usage_rate,
                'positions_count': len(positions),
                'currency': 'CNY',
                'calculation_time': datetime.now()
            }
            
            logger.info(f"💰 [可用保证金] 余额¥{account_balance:,.2f}，已用¥{used_margin:,.2f}，可用¥{available_margin:,.2f}")
            return result
            
        except Exception as e:
            logger.error(f"❌ [可用保证金计算] 计算失败: {e}")
            raise

    def calculate_unrealized_pnl(self, positions: List[Dict], current_prices: Dict[str, Decimal]) -> Dict:
        """
        计算未实现盈亏
        
        Args:
            positions: 持仓列表
            current_prices: 当前价格字典 {symbol: price}
            
        Returns:
            Dict: 未实现盈亏信息
        """
        try:
            total_unrealized_pnl = Decimal('0')
            position_pnls = []
            
            for position in positions:
                symbol = position['symbol']
                entry_price = Decimal(str(position['price']))
                volume = int(position['volume'])
                position_type = position.get('position_type', 'long')
                
                current_price = current_prices.get(symbol, entry_price)
                multiplier = self.get_contract_multiplier(symbol)
                
                # 计算盈亏
                if position_type == 'long':
                    pnl = (current_price - entry_price) * volume * multiplier
                else:  # short
                    pnl = (entry_price - current_price) * volume * multiplier
                
                pnl_rate = pnl / (entry_price * volume * multiplier) if entry_price > 0 else Decimal('0')
                
                position_pnl = {
                    'symbol': symbol,
                    'entry_price': entry_price,
                    'current_price': current_price,
                    'volume': volume,
                    'position_type': position_type,
                    'unrealized_pnl': pnl,
                    'pnl_rate': pnl_rate,
                    'contract_multiplier': multiplier
                }
                
                total_unrealized_pnl += pnl
                position_pnls.append(position_pnl)
            
            result = {
                'total_unrealized_pnl': total_unrealized_pnl,
                'position_pnls': position_pnls,
                'profitable_positions': len([p for p in position_pnls if p['unrealized_pnl'] > 0]),
                'losing_positions': len([p for p in position_pnls if p['unrealized_pnl'] < 0]),
                'currency': 'CNY',
                'calculation_time': datetime.now()
            }
            
            logger.info(f"📈 [未实现盈亏] 总计¥{total_unrealized_pnl:,.2f}，盈利{result['profitable_positions']}个，亏损{result['losing_positions']}个")
            return result
            
        except Exception as e:
            logger.error(f"❌ [未实现盈亏计算] 计算失败: {e}")
            raise

    def calculate_dynamic_equity(self, account_balance: Decimal, positions: List[Dict], current_prices: Dict[str, Decimal]) -> Dict:
        """
        计算动态权益
        
        Args:
            account_balance: 账户余额
            positions: 持仓列表
            current_prices: 当前价格字典
            
        Returns:
            Dict: 动态权益信息
        """
        try:
            # 计算未实现盈亏
            pnl_info = self.calculate_unrealized_pnl(positions, current_prices)
            total_unrealized_pnl = pnl_info['total_unrealized_pnl']
            
            # 计算动态权益
            dynamic_equity = account_balance + total_unrealized_pnl
            
            # 计算权益变化率
            equity_change_rate = total_unrealized_pnl / account_balance if account_balance > 0 else Decimal('0')
            
            result = {
                'account_balance': account_balance,
                'unrealized_pnl': total_unrealized_pnl,
                'dynamic_equity': dynamic_equity,
                'equity_change_rate': equity_change_rate,
                'position_pnls': pnl_info['position_pnls'],
                'currency': 'CNY',
                'calculation_time': datetime.now()
            }
            
            logger.info(f"💎 [动态权益] 静态余额¥{account_balance:,.2f} + 浮盈¥{total_unrealized_pnl:,.2f} = 动态权益¥{dynamic_equity:,.2f}")
            return result
            
        except Exception as e:
            logger.error(f"❌ [动态权益计算] 计算失败: {e}")
            raise

    def set_broker_margin_multiplier(self, multiplier: Decimal):
        """设置期货公司保证金倍数"""
        self.broker_margin_multiplier = multiplier
        logger.info(f"🔧 [保证金设置] 期货公司保证金倍数设置为: {multiplier}")

    def set_custom_margin_rate(self, symbol: str, rate: Decimal):
        """设置自定义保证金比例"""
        underlying = self._extract_underlying(symbol)
        self.exchange_margin_rates[underlying] = rate
        logger.info(f"🔧 [保证金设置] {symbol} 自定义保证金比例设置为: {rate:.1%}")

    def get_margin_summary(self, symbol: str) -> Dict:
        """
        获取期货品种保证金概览
        
        Args:
            symbol: 期货代码
            
        Returns:
            Dict: 保证金概览信息
        """
        try:
            underlying = self._extract_underlying(symbol)
            exchange_rate = self.exchange_margin_rates.get(underlying, Decimal('0.10'))
            actual_rate = self.get_margin_rate(symbol)
            multiplier = self.get_contract_multiplier(symbol)
            leverage = Decimal('1') / actual_rate if actual_rate > 0 else Decimal('0')
            
            # 计算示例（以当前价格1000为例）
            example_price = Decimal('1000')
            example_volume = 1
            example_margin = self.calculate_position_margin(symbol, example_price, example_volume)
            
            result = {
                'symbol': symbol,
                'underlying': underlying,
                'exchange_margin_rate': exchange_rate,
                'broker_multiplier': self.broker_margin_multiplier,
                'actual_margin_rate': actual_rate,
                'contract_multiplier': multiplier,
                'leverage': leverage,
                'example_calculation': {
                    'price': example_price,
                    'volume': example_volume,
                    'position_value': example_margin['position_value'],
                    'margin_required': example_margin['margin_required']
                }
            }
            
            return result
            
        except Exception as e:
            logger.error(f"❌ [保证金概览] 获取失败: {e}")
            raise


# 全局保证金计算器实例
_margin_calculator = None

def get_margin_calculator() -> MarginCalculator:
    """获取全局保证金计算器实例"""
    global _margin_calculator
    if _margin_calculator is None:
        _margin_calculator = MarginCalculator()
    return _margin_calculator


# 便捷接口函数
def calculate_futures_margin(symbol: str, price: float, volume: int, position_type: str = 'long') -> Dict:
    """
    计算期货保证金的便捷接口
    
    Args:
        symbol: 期货代码
        price: 价格
        volume: 手数
        position_type: 持仓方向
        
    Returns:
        Dict: 保证金信息
    """
    calculator = get_margin_calculator()
    return calculator.calculate_position_margin(symbol, Decimal(str(price)), volume, position_type)


def get_futures_margin_rate(symbol: str) -> float:
    """
    获取期货保证金比例的便捷接口
    
    Args:
        symbol: 期货代码
        
    Returns:
        float: 保证金比例
    """
    calculator = get_margin_calculator()
    return float(calculator.get_margin_rate(symbol))