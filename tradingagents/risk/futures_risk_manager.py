#!/usr/bin/env python3
"""
期货风险管理器
提供期货交易的风险控制、保证金监控、强平机制等功能
"""

import os
from typing import Dict, List, Optional, Tuple, Any
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, timedelta
import warnings

# 导入保证金计算器
from .margin_calculator import get_margin_calculator, MarginCalculator

# 导入统一日志系统
from tradingagents.utils.logging_init import setup_dataflow_logging
logger = setup_dataflow_logging()

warnings.filterwarnings('ignore')


class FuturesRiskManager:
    """期货风险管理器"""
    
    def __init__(self, margin_calculator: MarginCalculator = None):
        """
        初始化期货风险管理器
        
        Args:
            margin_calculator: 保证金计算器实例
        """
        self.margin_calculator = margin_calculator or get_margin_calculator()
        
        # 风险控制参数
        self.risk_limits = {
            'max_position_concentration': Decimal('0.3'),    # 单品种最大持仓集中度30%
            'max_sector_concentration': Decimal('0.5'),      # 单板块最大持仓集中度50%
            'max_leverage': Decimal('10'),                   # 最大杠杆倍数10倍
            'max_daily_loss': Decimal('0.05'),               # 单日最大亏损5%
            'margin_call_threshold': Decimal('1.2'),         # 保证金预警阈值120%
            'force_liquidation_threshold': Decimal('1.0'),   # 强制平仓阈值100%
            'position_size_limit': 100                       # 单品种最大持仓手数
        }
        
        # 期货品种风险分类
        self.risk_categories = {
            'low_risk': {
                'symbols': ['T', 'TF', 'TS'],  # 国债期货
                'max_leverage': Decimal('20'),
                'margin_multiplier': Decimal('1.0')
            },
            'medium_risk': {
                'symbols': ['IF', 'IH', 'IC', 'IM', 'CU', 'AL', 'ZN', 'AU', 'AG', 'RB', 'HC'],
                'max_leverage': Decimal('10'),
                'margin_multiplier': Decimal('1.2')
            },
            'high_risk': {
                'symbols': ['AP', 'CJ', 'SC', 'NI', 'LC', 'SI'],
                'max_leverage': Decimal('5'),
                'margin_multiplier': Decimal('1.5')
            }
        }
        
        # 板块分类
        self.sector_mapping = {
            'financial': ['IF', 'IH', 'IC', 'IM', 'T', 'TF', 'TS'],
            'precious_metals': ['AU', 'AG'],
            'base_metals': ['CU', 'AL', 'ZN', 'PB', 'NI', 'SN', 'BC'],
            'ferrous_metals': ['RB', 'HC', 'SS', 'I', 'J', 'JM'],
            'energy_chemical': ['SC', 'FU', 'LU', 'BU', 'RU', 'L', 'V', 'PP', 'TA', 'MA', 'ZC', 'UR', 'SA', 'PF'],
            'agricultural': ['C', 'CS', 'A', 'B', 'M', 'Y', 'P', 'CF', 'SR', 'OI', 'RM', 'AP', 'CJ', 'JD'],
            'industrial': ['FG', 'SI', 'LC']
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

    def get_symbol_risk_category(self, symbol: str) -> str:
        """获取期货品种的风险分类"""
        underlying = self._extract_underlying(symbol)
        
        for category, info in self.risk_categories.items():
            if underlying in info['symbols']:
                return category
        
        return 'medium_risk'  # 默认中等风险

    def get_symbol_sector(self, symbol: str) -> str:
        """获取期货品种的板块分类"""
        underlying = self._extract_underlying(symbol)
        
        for sector, symbols in self.sector_mapping.items():
            if underlying in symbols:
                return sector
        
        return 'other'

    def check_position_risk(self, symbol: str, price: Decimal, volume: int, position_type: str, account_balance: Decimal, existing_positions: List[Dict] = None) -> Dict:
        """
        检查单个持仓的风险
        
        Args:
            symbol: 期货代码
            price: 价格
            volume: 手数
            position_type: 持仓方向
            account_balance: 账户余额
            existing_positions: 现有持仓列表
            
        Returns:
            Dict: 风险检查结果
        """
        try:
            existing_positions = existing_positions or []
            
            # 计算持仓保证金
            margin_info = self.margin_calculator.calculate_position_margin(symbol, price, volume, position_type)
            
            # 检查各项风险指标
            risk_checks = {
                'symbol': symbol,
                'position_value': margin_info['position_value'],
                'margin_required': margin_info['margin_required'],
                'leverage': margin_info['leverage'],
                'risk_category': self.get_symbol_risk_category(symbol),
                'sector': self.get_symbol_sector(symbol),
                'checks': {},
                'warnings': [],
                'errors': [],
                'overall_risk': 'low'
            }
            
            # 1. 检查保证金充足性
            if margin_info['margin_required'] > account_balance:
                risk_checks['errors'].append('保证金不足')
                risk_checks['overall_risk'] = 'high'
            elif margin_info['margin_required'] > account_balance * Decimal('0.8'):
                risk_checks['warnings'].append('保证金使用率过高')
                risk_checks['overall_risk'] = 'medium'
            
            # 2. 检查杠杆倍数
            max_leverage = self.risk_categories[risk_checks['risk_category']]['max_leverage']
            if margin_info['leverage'] > max_leverage:
                risk_checks['errors'].append(f'杠杆倍数{margin_info["leverage"]:.1f}倍超过限制{max_leverage}倍')
                risk_checks['overall_risk'] = 'high'
            
            # 3. 检查持仓集中度
            total_position_value = margin_info['position_value']
            for pos in existing_positions:
                pos_margin = self.margin_calculator.calculate_position_margin(
                    pos['symbol'], Decimal(str(pos['price'])), pos['volume'], pos.get('position_type', 'long')
                )
                total_position_value += pos_margin['position_value']
            
            position_concentration = margin_info['position_value'] / total_position_value if total_position_value > 0 else Decimal('0')
            if position_concentration > self.risk_limits['max_position_concentration']:
                risk_checks['warnings'].append(f'单品种持仓集中度{position_concentration:.1%}过高')
                risk_checks['overall_risk'] = 'medium'
            
            # 4. 检查板块集中度
            sector_value = margin_info['position_value']
            for pos in existing_positions:
                if self.get_symbol_sector(pos['symbol']) == risk_checks['sector']:
                    pos_margin = self.margin_calculator.calculate_position_margin(
                        pos['symbol'], Decimal(str(pos['price'])), pos['volume'], pos.get('position_type', 'long')
                    )
                    sector_value += pos_margin['position_value']
            
            sector_concentration = sector_value / total_position_value if total_position_value > 0 else Decimal('0')
            if sector_concentration > self.risk_limits['max_sector_concentration']:
                risk_checks['warnings'].append(f'板块持仓集中度{sector_concentration:.1%}过高')
                risk_checks['overall_risk'] = 'medium'
            
            # 5. 检查持仓手数限制
            if volume > self.risk_limits['position_size_limit']:
                risk_checks['errors'].append(f'持仓手数{volume}超过限制{self.risk_limits["position_size_limit"]}手')
                risk_checks['overall_risk'] = 'high'
            
            risk_checks['checks'] = {
                'margin_sufficient': len([e for e in risk_checks['errors'] if '保证金不足' in e]) == 0,
                'leverage_within_limit': margin_info['leverage'] <= max_leverage,
                'position_concentration_ok': position_concentration <= self.risk_limits['max_position_concentration'],
                'sector_concentration_ok': sector_concentration <= self.risk_limits['max_sector_concentration'],
                'position_size_ok': volume <= self.risk_limits['position_size_limit']
            }
            
            logger.info(f"🔍 [风险检查] {symbol} {volume}手 - {risk_checks['overall_risk']}风险")
            return risk_checks
            
        except Exception as e:
            logger.error(f"❌ [风险检查] 检查失败: {e}")
            raise

    def check_portfolio_risk(self, account_balance: Decimal, positions: List[Dict], current_prices: Dict[str, Decimal]) -> Dict:
        """
        检查投资组合整体风险
        
        Args:
            account_balance: 账户余额
            positions: 持仓列表
            current_prices: 当前价格字典
            
        Returns:
            Dict: 组合风险检查结果
        """
        try:
            # 计算动态权益
            equity_info = self.margin_calculator.calculate_dynamic_equity(account_balance, positions, current_prices)
            dynamic_equity = equity_info['dynamic_equity']
            
            # 计算组合保证金
            portfolio_margin = self.margin_calculator.calculate_portfolio_margin(positions)
            total_margin_required = portfolio_margin['total_margin_required']
            
            # 计算保证金充足率
            margin_ratio = dynamic_equity / total_margin_required if total_margin_required > 0 else Decimal('999')
            
            # 分析持仓分布
            sector_distribution = {}
            risk_distribution = {}
            
            for position in positions:
                sector = self.get_symbol_sector(position['symbol'])
                risk_category = self.get_symbol_risk_category(position['symbol'])
                
                # 计算持仓价值
                margin_info = self.margin_calculator.calculate_position_margin(
                    position['symbol'], 
                    Decimal(str(position['price'])), 
                    position['volume'], 
                    position.get('position_type', 'long')
                )
                position_value = margin_info['position_value']
                
                # 板块分布
                if sector not in sector_distribution:
                    sector_distribution[sector] = {'value': Decimal('0'), 'count': 0}
                sector_distribution[sector]['value'] += position_value
                sector_distribution[sector]['count'] += 1
                
                # 风险分布
                if risk_category not in risk_distribution:
                    risk_distribution[risk_category] = {'value': Decimal('0'), 'count': 0}
                risk_distribution[risk_category]['value'] += position_value
                risk_distribution[risk_category]['count'] += 1
            
            # 计算分布比例
            total_portfolio_value = portfolio_margin['total_position_value']
            for sector in sector_distribution:
                sector_distribution[sector]['percentage'] = sector_distribution[sector]['value'] / total_portfolio_value if total_portfolio_value > 0 else Decimal('0')
            
            for risk_cat in risk_distribution:
                risk_distribution[risk_cat]['percentage'] = risk_distribution[risk_cat]['value'] / total_portfolio_value if total_portfolio_value > 0 else Decimal('0')
            
            # 风险等级判断
            overall_risk = 'low'
            warnings = []
            errors = []
            
            # 检查保证金充足率
            if margin_ratio <= self.risk_limits['force_liquidation_threshold']:
                errors.append('达到强制平仓线')
                overall_risk = 'critical'
            elif margin_ratio <= self.risk_limits['margin_call_threshold']:
                warnings.append('接近保证金预警线')
                overall_risk = 'high'
            elif margin_ratio <= Decimal('1.5'):
                warnings.append('保证金充足率偏低')
                overall_risk = 'medium'
            
            # 检查日盈亏
            daily_pnl_rate = equity_info['equity_change_rate']
            if daily_pnl_rate <= -self.risk_limits['max_daily_loss']:
                errors.append(f'单日亏损{daily_pnl_rate:.1%}超过限制')
                overall_risk = 'critical'
            elif daily_pnl_rate <= -self.risk_limits['max_daily_loss'] * Decimal('0.8'):
                warnings.append('单日亏损较大')
                overall_risk = 'high'
            
            # 检查集中度
            for sector, info in sector_distribution.items():
                if info['percentage'] > self.risk_limits['max_sector_concentration']:
                    warnings.append(f'{sector}板块集中度{info["percentage"]:.1%}过高')
                    overall_risk = 'medium'
            
            portfolio_risk = {
                'account_balance': account_balance,
                'dynamic_equity': dynamic_equity,
                'total_margin_required': total_margin_required,
                'margin_ratio': margin_ratio,
                'daily_pnl': equity_info['unrealized_pnl'],
                'daily_pnl_rate': daily_pnl_rate,
                'total_positions': len(positions),
                'total_portfolio_value': total_portfolio_value,
                'sector_distribution': sector_distribution,
                'risk_distribution': risk_distribution,
                'overall_risk': overall_risk,
                'warnings': warnings,
                'errors': errors,
                'risk_checks': {
                    'margin_sufficient': margin_ratio > self.risk_limits['margin_call_threshold'],
                    'daily_loss_within_limit': daily_pnl_rate > -self.risk_limits['max_daily_loss'],
                    'concentration_ok': all(info['percentage'] <= self.risk_limits['max_sector_concentration'] for info in sector_distribution.values())
                },
                'calculation_time': datetime.now()
            }
            
            logger.info(f"🔍 [组合风险] {len(positions)}个持仓，保证金充足率{margin_ratio:.1%}，{overall_risk}风险")
            return portfolio_risk
            
        except Exception as e:
            logger.error(f"❌ [组合风险检查] 检查失败: {e}")
            raise

    def generate_risk_report(self, account_balance: Decimal, positions: List[Dict], current_prices: Dict[str, Decimal]) -> str:
        """
        生成风险管理报告
        
        Args:
            account_balance: 账户余额
            positions: 持仓列表
            current_prices: 当前价格字典
            
        Returns:
            str: 风险管理报告
        """
        try:
            portfolio_risk = self.check_portfolio_risk(account_balance, positions, current_prices)
            
            report = f"""
📊 期货风险管理报告
生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

💰 账户概况:
  账户余额: ¥{portfolio_risk['account_balance']:,.2f}
  动态权益: ¥{portfolio_risk['dynamic_equity']:,.2f}
  浮动盈亏: ¥{portfolio_risk['daily_pnl']:,.2f} ({portfolio_risk['daily_pnl_rate']:+.2%})

📊 保证金状况:
  已用保证金: ¥{portfolio_risk['total_margin_required']:,.2f}
  保证金充足率: {portfolio_risk['margin_ratio']:.1%}
  风险等级: {portfolio_risk['overall_risk'].upper()}

📈 持仓分布:
  总持仓数: {portfolio_risk['total_positions']}个
  总持仓价值: ¥{portfolio_risk['total_portfolio_value']:,.2f}
"""
            
            # 板块分布
            if portfolio_risk['sector_distribution']:
                report += "\n🏭 板块分布:\n"
                for sector, info in portfolio_risk['sector_distribution'].items():
                    report += f"  {sector}: {info['count']}个持仓, ¥{info['value']:,.2f} ({info['percentage']:.1%})\n"
            
            # 风险分布
            if portfolio_risk['risk_distribution']:
                report += "\n⚠️ 风险分布:\n"
                for risk_cat, info in portfolio_risk['risk_distribution'].items():
                    report += f"  {risk_cat}: {info['count']}个持仓, ¥{info['value']:,.2f} ({info['percentage']:.1%})\n"
            
            # 风险提示
            if portfolio_risk['errors']:
                report += "\n❌ 严重风险:\n"
                for error in portfolio_risk['errors']:
                    report += f"  • {error}\n"
            
            if portfolio_risk['warnings']:
                report += "\n⚠️ 风险提示:\n"
                for warning in portfolio_risk['warnings']:
                    report += f"  • {warning}\n"
            
            # 风险建议
            report += "\n💡 风险管理建议:\n"
            if portfolio_risk['margin_ratio'] <= Decimal('1.2'):
                report += "  • 建议及时补充保证金或减少持仓\n"
            if portfolio_risk['daily_pnl_rate'] <= Decimal('-0.03'):
                report += "  • 建议检查持仓，考虑止损\n"
            
            # 检查集中度
            high_concentration_sectors = [sector for sector, info in portfolio_risk['sector_distribution'].items() 
                                        if info['percentage'] > Decimal('0.4')]
            if high_concentration_sectors:
                report += f"  • 建议分散投资，减少{', '.join(high_concentration_sectors)}板块集中度\n"
            
            if portfolio_risk['overall_risk'] == 'low':
                report += "  • 当前风险可控，继续保持谨慎交易\n"
            
            return report
            
        except Exception as e:
            logger.error(f"❌ [风险报告生成] 生成失败: {e}")
            return f"❌ 风险报告生成失败: {str(e)}"

    def suggest_position_size(self, symbol: str, price: Decimal, account_balance: Decimal, risk_tolerance: str = 'medium') -> Dict:
        """
        建议持仓规模
        
        Args:
            symbol: 期货代码
            price: 价格
            account_balance: 账户余额
            risk_tolerance: 风险承受能力 'low', 'medium', 'high'
            
        Returns:
            Dict: 持仓建议
        """
        try:
            # 风险承受能力对应的参数
            risk_params = {
                'low': {'max_position_rate': Decimal('0.1'), 'max_leverage': Decimal('3')},
                'medium': {'max_position_rate': Decimal('0.2'), 'max_leverage': Decimal('5')},
                'high': {'max_position_rate': Decimal('0.3'), 'max_leverage': Decimal('8')}
            }
            
            params = risk_params.get(risk_tolerance, risk_params['medium'])
            
            # 计算单手保证金
            single_margin = self.margin_calculator.calculate_position_margin(symbol, price, 1, 'long')
            margin_per_lot = single_margin['margin_required']
            
            # 根据风险承受能力计算建议手数
            max_margin_budget = account_balance * params['max_position_rate']
            suggested_volume = int(max_margin_budget / margin_per_lot) if margin_per_lot > 0 else 0
            
            # 检查杠杆限制
            actual_leverage = single_margin['leverage']
            if actual_leverage > params['max_leverage']:
                leverage_limited_volume = int(suggested_volume * params['max_leverage'] / actual_leverage)
                suggested_volume = min(suggested_volume, leverage_limited_volume)
            
            # 检查品种风险限制
            risk_category = self.get_symbol_risk_category(symbol)
            category_max_leverage = self.risk_categories[risk_category]['max_leverage']
            if actual_leverage > category_max_leverage:
                category_limited_volume = int(suggested_volume * category_max_leverage / actual_leverage)
                suggested_volume = min(suggested_volume, category_limited_volume)
            
            # 最终建议
            if suggested_volume > 0:
                final_margin = suggested_volume * margin_per_lot
                final_position_value = suggested_volume * price * single_margin['contract_multiplier']
                final_leverage = final_position_value / final_margin if final_margin > 0 else Decimal('0')
                
                suggestion = {
                    'symbol': symbol,
                    'price': price,
                    'suggested_volume': suggested_volume,
                    'margin_required': final_margin,
                    'position_value': final_position_value,
                    'leverage': final_leverage,
                    'risk_tolerance': risk_tolerance,
                    'margin_usage_rate': final_margin / account_balance,
                    'reasoning': f"基于{risk_tolerance}风险承受能力，建议持仓{suggested_volume}手"
                }
            else:
                suggestion = {
                    'symbol': symbol,
                    'price': price,
                    'suggested_volume': 0,
                    'margin_required': Decimal('0'),
                    'position_value': Decimal('0'),
                    'leverage': Decimal('0'),
                    'risk_tolerance': risk_tolerance,
                    'margin_usage_rate': Decimal('0'),
                    'reasoning': "当前价格下风险过高，不建议开仓"
                }
            
            logger.info(f"💡 [持仓建议] {symbol} 建议{suggested_volume}手，保证金¥{suggestion['margin_required']:,.2f}")
            return suggestion
            
        except Exception as e:
            logger.error(f"❌ [持仓建议] 计算失败: {e}")
            raise

    def set_risk_limit(self, limit_name: str, value: Decimal):
        """设置风险限制参数"""
        if limit_name in self.risk_limits:
            self.risk_limits[limit_name] = value
            logger.info(f"🔧 [风险设置] {limit_name} 设置为: {value}")
        else:
            logger.warning(f"⚠️ [风险设置] 未知的风险限制参数: {limit_name}")

    def get_risk_limits(self) -> Dict:
        """获取当前风险限制参数"""
        return self.risk_limits.copy()


# 全局风险管理器实例
_futures_risk_manager = None

def get_futures_risk_manager() -> FuturesRiskManager:
    """获取全局期货风险管理器实例"""
    global _futures_risk_manager
    if _futures_risk_manager is None:
        _futures_risk_manager = FuturesRiskManager()
    return _futures_risk_manager


# 便捷接口函数
def check_futures_position_risk(symbol: str, price: float, volume: int, account_balance: float) -> Dict:
    """
    检查期货持仓风险的便捷接口
    
    Args:
        symbol: 期货代码
        price: 价格
        volume: 手数
        account_balance: 账户余额
        
    Returns:
        Dict: 风险检查结果
    """
    risk_manager = get_futures_risk_manager()
    return risk_manager.check_position_risk(
        symbol, Decimal(str(price)), volume, 'long', Decimal(str(account_balance))
    )


def generate_futures_risk_report(account_balance: float, positions: List[Dict], current_prices: Dict[str, float]) -> str:
    """
    生成期货风险报告的便捷接口
    
    Args:
        account_balance: 账户余额
        positions: 持仓列表
        current_prices: 当前价格字典
        
    Returns:
        str: 风险报告
    """
    risk_manager = get_futures_risk_manager()
    
    # 转换数据类型
    decimal_prices = {k: Decimal(str(v)) for k, v in current_prices.items()}
    
    return risk_manager.generate_risk_report(
        Decimal(str(account_balance)), positions, decimal_prices
    )