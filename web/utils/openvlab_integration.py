#!/usr/bin/env python3
"""
OpenVLab 期权策略分析集成工具
基于AI决策结果进行期权策略优化分析
"""

import os
import sys
import logging
from typing import Dict, Any, Optional
from pathlib import Path

# 导入日志模块
from tradingagents.utils.logging_manager import get_logger
logger = get_logger('web')

def convert_stock_to_futures(stock_symbol: str) -> str:
    """
    将股票代码转换为对应的期货合约代码
    
    Args:
        stock_symbol: 股票代码
        
    Returns:
        对应的期货合约代码
    """
    # 股票到期货的映射关系
    stock_futures_mapping = {
        # 主要指数ETF和成分股
        '000300': 'IM2509',  # 沪深300指数 → 沪深300股指期货
        '510300': 'IM2509',  # 沪深300ETF → 沪深300股指期货
        '159919': 'IM2509',  # 沪深300ETF → 沪深300股指期货
        
        '000905': 'IC2509',  # 中证500指数 → 中证500期货
        '510500': 'IC2509',  # 中证500ETF → 中证500期货
        '159922': 'IC2509',  # 中证500ETF → 中证500期货
        
        '000852': 'IM2509',  # 中证1000指数 → 中证1000期货（暂用IM）
        '512100': 'IM2509',  # 中证1000ETF → 中证1000期货（暂用IM）
        
        '000001': 'IM2509',  # 上证指数 → 沪深300期货（近似）
        '000016': 'IM2509',  # 上证50 → 沪深300期货（近似）
        '510050': 'IM2509',  # 上证50ETF → 沪深300期货（近似）
        
        # 科技股相关
        '399006': 'IC2509',  # 创业板指 → 中证500期货（近似）
        '159915': 'IC2509',  # 创业板ETF → 中证500期货（近似）
        
        # 个股到相关指数期货的映射（基于行业权重）
        '000858': 'IM2509',  # 五粮液 → 沪深300期货
        '000001.SZ': 'IM2509',  # 平安银行 → 沪深300期货
        '600036': 'IM2509',  # 招商银行 → 沪深300期货
        '600519': 'IM2509',  # 贵州茅台 → 沪深300期货
        '000002': 'IM2509',  # 万科A → 沪深300期货
        
        # 中小盘股票
        '300059': 'IC2509',  # 东方财富 → 中证500期货
        '002415': 'IC2509',  # 海康威视 → 中证500期货
    }
    
    # 清理股票代码格式
    clean_symbol = stock_symbol.upper().replace('.SZ', '').replace('.SH', '')
    
    # 查找映射
    futures_code = stock_futures_mapping.get(clean_symbol)
    
    if futures_code:
        logger.info(f"股票映射: {stock_symbol} → {futures_code}")
        return futures_code
    else:
        # 默认映射到沪深300期货
        default_code = 'IM2509'
        logger.warning(f"未找到股票 {stock_symbol} 的精确映射，使用默认期货合约: {default_code}")
        return default_code

def should_analyze_options(stock_symbol: str, target_price: float) -> bool:
    """
    判断是否应该进行期权策略分析
    
    Args:
        stock_symbol: 股票代码
        target_price: 目标价格
        
    Returns:
        是否应该分析期权策略
    """
    # 检查目标价格是否有效
    if not target_price or target_price <= 0:
        logger.info("目标价格无效，跳过期权策略分析")
        return False
    
    # 检查是否为支持的股票类型
    if not stock_symbol:
        logger.info("股票代码为空，跳过期权策略分析")
        return False
    
    # 目前支持所有股票的期权分析（通过期货映射）
    logger.info(f"股票 {stock_symbol} 符合期权策略分析条件，目标价格: {target_price}")
    return True

def get_openvlab_analysis(stock_symbol: str, target_price: float, 
                         output_dir: str = None) -> Dict[str, Any]:
    """
    基于AI决策结果进行OpenVLab期权策略分析
    
    Args:
        stock_symbol: 股票代码
        target_price: AI预测的目标价格
        output_dir: 输出目录（可选）
        
    Returns:
        期权策略分析结果
    """
    logger.info(f"开始OpenVLab期权策略分析: {stock_symbol} @ {target_price}")
    
    result = {
        'success': False,
        'stock_symbol': stock_symbol,
        'target_price': target_price,
        'futures_code': None,
        'openvlab_results': None,
        'html_content': None,
        'error': None
    }
    
    try:
        # 检查是否应该分析
        if not should_analyze_options(stock_symbol, target_price):
            result['error'] = "不符合期权策略分析条件"
            return result
        
        # 转换股票代码到期货代码
        futures_code = convert_stock_to_futures(stock_symbol)
        result['futures_code'] = futures_code
        
        # 设置输出目录
        if not output_dir:
            # 使用项目根目录下的临时目录
            project_root = Path(__file__).parent.parent.parent
            output_dir = project_root / "temp" / "openvlab_analysis"
        
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"使用期货代码: {futures_code}, 输出目录: {output_dir}")
        
        # 导入并调用OpenVLab分析器
        try:
            sys.path.append(str(Path(__file__).parent.parent.parent / "utils" / "openvlab"))
            from optimized_strategy_extractor import OptimizedStrategyExtractor
            
            logger.info("开始调用OptimizedStrategyExtractor...")
            
            with OptimizedStrategyExtractor(headless=True) as extractor:
                openvlab_results = extractor.extract_precise_strategy_descriptions(
                    strategy_code=futures_code,
                    target_price=target_price,
                    output_dir=str(output_dir),
                    save_svg_files=True
                )
            
            result['openvlab_results'] = openvlab_results
            
            if openvlab_results.get('success'):
                # 读取生成的HTML文件内容
                html_file = openvlab_results.get('html_file')
                if html_file and os.path.exists(html_file):
                    with open(html_file, 'r', encoding='utf-8') as f:
                        result['html_content'] = f.read()
                    logger.info(f"成功读取HTML文件: {html_file}")
                
                result['success'] = True
                logger.info("OpenVLab期权策略分析成功完成")
                
                # 输出简要结果
                best_strategy = openvlab_results.get('best_strategy')
                if best_strategy:
                    logger.info(f"推荐策略: {best_strategy.get('full_description', 'N/A')}")
                    logger.info(f"E值: {openvlab_results.get('max_e_value', 'N/A')}")
                
            else:
                result['error'] = "OpenVLab分析执行失败"
                logger.error("OpenVLab分析执行失败")
                
        except ImportError as e:
            result['error'] = f"无法导入OpenVLab模块: {e}"
            logger.error(f"无法导入OpenVLab模块: {e}")
        except Exception as e:
            result['error'] = f"OpenVLab分析出错: {e}"
            logger.error(f"OpenVLab分析出错: {e}", exc_info=True)
            
    except Exception as e:
        result['error'] = f"期权策略分析失败: {e}"
        logger.error(f"期权策略分析失败: {e}", exc_info=True)
    
    return result

def format_openvlab_summary(openvlab_results: Dict[str, Any]) -> str:
    """
    格式化OpenVLab分析结果摘要
    
    Args:
        openvlab_results: OpenVLab分析结果
        
    Returns:
        格式化的摘要文本
    """
    if not openvlab_results or not openvlab_results.get('success'):
        return "期权策略分析未成功完成"
    
    summary_parts = []
    
    # 基本信息
    futures_code = openvlab_results.get('futures_code', 'N/A')
    target_price = openvlab_results.get('target_price', 'N/A')
    summary_parts.append(f"**分析标的**: {futures_code}")
    summary_parts.append(f"**目标价格**: {target_price}")
    
    # 推荐策略
    openvlab_data = openvlab_results.get('openvlab_results', {})
    best_strategy = openvlab_data.get('best_strategy')
    if best_strategy:
        strategy_desc = best_strategy.get('full_description', 'N/A')
        e_value = openvlab_data.get('max_e_value', 'N/A')
        summary_parts.append(f"**推荐策略**: {strategy_desc}")
        if e_value != 'N/A':
            summary_parts.append(f"**期望收益率(E值)**: {e_value:.4f}")
    
    # 策略数量
    precise_descriptions = openvlab_data.get('precise_descriptions', [])
    if precise_descriptions:
        summary_parts.append(f"**策略总数**: {len(precise_descriptions)}个")
    
    return "\n".join(summary_parts)

def extract_openvlab_markdown(openvlab_results: Dict[str, Any]) -> str:
    """
    提取OpenVLab分析结果的Markdown格式内容
    用于报告导出
    
    Args:
        openvlab_results: OpenVLab分析结果
        
    Returns:
        Markdown格式的内容
    """
    if not openvlab_results or not openvlab_results.get('success'):
        return "## 📊 期权策略优化分析\n\n期权策略分析未成功完成。\n\n"
    
    md_content = "## 📊 期权策略优化分析\n\n"
    
    # 基本信息
    stock_symbol = openvlab_results.get('stock_symbol', 'N/A')
    futures_code = openvlab_results.get('futures_code', 'N/A')
    target_price = openvlab_results.get('target_price', 'N/A')
    
    md_content += f"**原始标的**: {stock_symbol}\n"
    md_content += f"**期货合约**: {futures_code}\n"
    md_content += f"**目标价格**: {target_price}\n\n"
    
    # OpenVLab分析结果
    openvlab_data = openvlab_results.get('openvlab_results', {})
    
    # 推荐策略
    best_strategy = openvlab_data.get('best_strategy')
    if best_strategy:
        md_content += "### 🏆 推荐策略\n\n"
        md_content += f"**策略名称**: {best_strategy.get('full_description', 'N/A')}\n"
        
        e_value = openvlab_data.get('max_e_value')
        if e_value is not None:
            md_content += f"**期望收益率(E值)**: {e_value:.4f}\n"
        
        # 财务信息
        financial_info = best_strategy.get('financial_info', {})
        if financial_info:
            summary = financial_info.get('summary', '')
            if summary:
                md_content += f"**策略概要**: {summary}\n"
        
        md_content += "\n"
    
    # 所有策略列表
    precise_descriptions = openvlab_data.get('precise_descriptions', [])
    if precise_descriptions:
        md_content += "### 📋 策略分析详情\n\n"
        md_content += f"共分析了 {len(precise_descriptions)} 个期权策略：\n\n"
        
        for i, strategy in enumerate(precise_descriptions, 1):
            strategy_name = strategy.get('strategy_name', 'N/A')
            action_desc = strategy.get('action_description', 'N/A')
            md_content += f"{i}. **{strategy_name}** - {action_desc}\n"
            
            # 财务信息
            financial_info = strategy.get('financial_info', {})
            if financial_info:
                e_value = financial_info.get('e_value')
                if e_value is not None:
                    md_content += f"   - E值: {e_value:.4f}\n"
                summary = financial_info.get('summary', '')
                if summary:
                    md_content += f"   - 概要: {summary}\n"
            md_content += "\n"
    
    # 分析说明
    md_content += "### 📝 分析说明\n\n"
    md_content += "- 期权策略分析基于OpenVLab平台的智能优化算法\n"
    md_content += "- E值代表期望收益率，E值越高代表策略理论收益越好\n"
    md_content += "- 推荐策略为E值最高的策略组合\n"
    md_content += "- 实际交易时请结合市场情况和个人风险承受能力\n\n"
    
    return md_content