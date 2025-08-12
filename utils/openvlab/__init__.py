#!/usr/bin/env python3
"""
OpenVlab 包初始化文件

这个包提供了从 OpenVlab 网站获取策略图表 SVG 的工具。
"""

# 版本信息
__version__ = "0.1.0"
__author__ = "Claude Code Assistant"
__description__ = "OpenVlab策略SVG获取工具"

# 导入主要类
try:
    from .local_svg_fetcher import LocalCalculationSVGFetcher
    from .openvlab_svg_fetcher import OpenVLabSVGFetcher  
    from .simple_svg_fetcher import SimpleOpenVLabFetcher
    from .api_detector import APIDetector

    __all__ = [
        'LocalCalculationSVGFetcher',
        'OpenVLabSVGFetcher', 
        'SimpleOpenVLabFetcher',
        'APIDetector'
    ]
except ImportError as e:
    # 如果依赖没有安装，至少让模块可以导入
    print(f"Warning: Some dependencies not installed: {e}")
    __all__ = []

# 快捷函数
def quick_fetch_svg(strategy_code: str, target_price: float, headless: bool = True) -> str:
    """
    快速获取SVG的便捷函数
    
    Args:
        strategy_code: 策略代码
        target_price: 目标价格
        headless: 是否无头模式
        
    Returns:
        SVG内容字符串，如果失败返回None
    """
    try:
        with LocalCalculationSVGFetcher(headless=headless) as fetcher:
            return fetcher.fetch_svg_with_target_price(strategy_code, target_price)
    except Exception as e:
        print(f"快速获取失败: {e}")
        return None