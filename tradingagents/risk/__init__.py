"""
期货风险管理模块
提供期货交易的保证金计算、风险控制、强平机制等功能
"""

from .margin_calculator import (
    MarginCalculator,
    get_margin_calculator,
    calculate_futures_margin,
    get_futures_margin_rate
)

from .futures_risk_manager import (
    FuturesRiskManager,
    get_futures_risk_manager,
    check_futures_position_risk,
    generate_futures_risk_report
)

__all__ = [
    'MarginCalculator',
    'get_margin_calculator',
    'calculate_futures_margin',
    'get_futures_margin_rate',
    'FuturesRiskManager',
    'get_futures_risk_manager',
    'check_futures_position_risk',
    'generate_futures_risk_report'
]