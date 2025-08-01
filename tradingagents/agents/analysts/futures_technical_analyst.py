"""
期货技术分析师 - 专门分析期货品种技术形态
支持期货特有的技术指标分析，如持仓量变化、成交量分析等
"""

from datetime import datetime, timedelta
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import AIMessage

# 导入分析模块日志装饰器
from tradingagents.utils.tool_logging import log_analyst_module

# 导入统一日志系统
from tradingagents.utils.logging_init import get_logger
logger = get_logger("default")


def _get_futures_technical_focus(symbol: str) -> dict:
    """
    获取期货品种技术分析重点
    
    Args:
        symbol: 期货代码
        
    Returns:
        dict: 技术分析重点
    """
    # 提取品种代码
    underlying = symbol.upper()
    if underlying.endswith('99'):
        underlying = underlying[:-2]
    elif len(underlying) > 2 and underlying[-2:].isdigit():
        underlying = underlying[:-2]
    elif len(underlying) > 4 and underlying[-4:].isdigit():
        underlying = underlying[:-4]
    
    # 不同期货类型的技术分析重点
    technical_focus = {
        # 金融期货 - 关注资金流向和持仓结构
        'IF': {'volatility': '高', 'key_indicators': ['成交量', '持仓量', 'VIX', '资金流向'], 'trading_pattern': '日内波动大'},
        'IH': {'volatility': '中高', 'key_indicators': ['大单净量', '持仓结构', '期现差', '升贴水'], 'trading_pattern': '跟随大盘'},
        'IC': {'volatility': '高', 'key_indicators': ['小盘股走势', '成长股表现', '风险偏好'], 'trading_pattern': '波动较大'},
        'IM': {'volatility': '中', 'key_indicators': ['中小盘指数', '市场情绪', '流动性'], 'trading_pattern': '相对稳定'},
        'T': {'volatility': '低', 'key_indicators': ['收益率曲线', '央行政策', '通胀预期'], 'trading_pattern': '趋势性强'},
        'TF': {'volatility': '低', 'key_indicators': ['利率走势', '债券供需', '货币政策'], 'trading_pattern': '波动较小'},
        'TS': {'volatility': '低', 'key_indicators': ['短期利率', '资金面', '政策利率'], 'trading_pattern': '高频交易'},
        
        # 贵金属 - 关注避险情绪和美元指数
        'AU': {'volatility': '中', 'key_indicators': ['美元指数', '实际利率', '地缘政治'], 'trading_pattern': '避险属性'},
        'AG': {'volatility': '高', 'key_indicators': ['工业需求', '白银比价', '投机资金'], 'trading_pattern': '波动剧烈'},
        
        # 有色金属 - 关注库存和需求
        'CU': {'volatility': '中高', 'key_indicators': ['库存变化', 'LME价格', '电力需求'], 'trading_pattern': '供需驱动'},
        'AL': {'volatility': '中', 'key_indicators': ['电解铝产能', '库存水平', '成本支撑'], 'trading_pattern': '成本导向'},
        'ZN': {'volatility': '中', 'key_indicators': ['房地产需求', '汽车产量', '进口数据'], 'trading_pattern': '需求主导'},
        'NI': {'volatility': '高', 'key_indicators': ['不锈钢产量', '新能源需求', '印尼供应'], 'trading_pattern': '供应冲击'},
        
        # 黑色系 - 关注钢铁产业链
        'RB': {'volatility': '中高', 'key_indicators': ['钢厂利润', '社会库存', '基建需求'], 'trading_pattern': '季节性强'},
        'HC': {'volatility': '中', 'key_indicators': ['热卷需求', '板材价差', '出口情况'], 'trading_pattern': '跟随螺纹'},
        'I': {'volatility': '高', 'key_indicators': ['港口库存', '钢厂开工', '澳巴发货'], 'trading_pattern': '供应波动'},
        'J': {'volatility': '中高', 'key_indicators': ['钢厂库存', '环保限产', '运输成本'], 'trading_pattern': '政策敏感'},
        'JM': {'volatility': '中', 'key_indicators': ['焦化利润', '煤矿产量', '安检影响'], 'trading_pattern': '成本推动'},
        
        # 能源化工 - 关注原油和下游需求
        'SC': {'volatility': '高', 'key_indicators': ['国际油价', '炼厂开工', '库存变化'], 'trading_pattern': '跟随外盘'},
        'FU': {'volatility': '中高', 'key_indicators': ['船用油需求', '炼厂裂解', '进口政策'], 'trading_pattern': '下游主导'},
        'RU': {'volatility': '中', 'key_indicators': ['轮胎开工', '天然橡胶', '汽车产量'], 'trading_pattern': '季节波动'},
        'L': {'volatility': '中', 'key_indicators': ['石化库存', '下游开工', '检修计划'], 'trading_pattern': '供需平衡'},
        'PP': {'volatility': '中', 'key_indicators': ['装置开工', '利润水平', '期现价差'], 'trading_pattern': '波段操作'},
        'TA': {'volatility': '中高', 'key_indicators': ['PX价格', '聚酯需求', '纺织出口'], 'trading_pattern': '产业链联动'},
        'MA': {'volatility': '中', 'key_indicators': ['甲醇制烯烃', '传统需求', '进口成本'], 'trading_pattern': '需求分化'},
        
        # 农产品 - 关注天气和库存
        'C': {'volatility': '中', 'key_indicators': ['天气炒作', '库存消费', '政策收储'], 'trading_pattern': '季节性明显'},
        'A': {'volatility': '中', 'key_indicators': ['大豆进口', '压榨利润', '库存周期'], 'trading_pattern': '外盘影响'},
        'M': {'volatility': '中高', 'key_indicators': ['生猪存栏', '饲料需求', '豆粕库存'], 'trading_pattern': '下游驱动'},
        'Y': {'volatility': '中', 'key_indicators': ['油脂库存', '棕榈油价', '消费需求'], 'trading_pattern': '油脂联动'},
        'CF': {'volatility': '高', 'key_indicators': ['新疆天气', '纺织订单', '储备棉'], 'trading_pattern': '天气敏感'},
        'SR': {'volatility': '中', 'key_indicators': ['食糖库存', '进口配额', '替代品价格'], 'trading_pattern': '政策影响'},
        'AP': {'volatility': '极高', 'key_indicators': ['天气状况', '库存去化', '消费季节'], 'trading_pattern': '投机性强'},
    }
    
    base_focus = {
        'volatility': '中',
        'key_indicators': ['价格趋势', '成交量', '持仓量', '技术形态'],
        'trading_pattern': '趋势跟随'
    }
    
    return technical_focus.get(underlying, base_focus)


def create_futures_technical_analyst(llm, toolkit):
    @log_analyst_module("futures_technical")
    def futures_technical_analyst_node(state):
        logger.debug(f"📈 [DEBUG] ===== 期货技术分析师节点开始 =====")
        
        current_date = state["trade_date"]
        symbol = state["company_of_interest"]
        # 固定日期是有问题的，改成当前日期往前3个月
        # 默认取当前日期往前90天
        current_date_dt = datetime.strptime(state["trade_date"], '%Y-%m-%d')
        start_date = (current_date_dt - timedelta(days=90)).strftime('%Y-%m-%d')        
        #start_date = '2025-05-28'  #
        
        logger.debug(f"📈 [DEBUG] 输入参数: symbol={symbol}, date={current_date}")
        logger.debug(f"📈 [DEBUG] 当前状态中的消息数量: {len(state.get('messages', []))}")
        logger.debug(f"📈 [DEBUG] 现有期货技术报告: {state.get('futures_technical_report', 'None')}")
        
        # 检查是否为期货代码
        from tradingagents.dataflows.data_source_manager import is_futures_symbol_unified, get_futures_info_unified
        
        if not is_futures_symbol_unified(symbol):
            logger.warning(f"⚠️ [期货技术分析师] {symbol} 不是期货代码，跳过分析")
            return {"futures_technical_report": f"❌ {symbol} 不是期货代码，无法进行期货技术分析"}
        
        logger.info(f"📈 [期货技术分析师] 正在分析期货品种: {symbol}")
        
        # 获取期货基本信息和技术分析重点
        futures_info = get_futures_info_unified(symbol)
        futures_name = futures_info.get('name', f'期货{symbol}')
        technical_focus = _get_futures_technical_focus(symbol)
        
        logger.debug(f"📈 [DEBUG] 期货品种信息: {futures_name}")
        logger.debug(f"📈 [DEBUG] 技术分析重点: {technical_focus}")
        logger.debug(f"📈 [DEBUG] 工具配置检查: online_tools={toolkit.config['online_tools']}")
        
        # 选择工具
        if toolkit.config["online_tools"]:
            # 使用期货数据工具进行技术分析
            logger.info(f"📈 [期货技术分析师] 使用在线期货数据工具")
            tools = [toolkit.get_futures_data_unified]
            
            # 安全地获取工具名称用于调试
            tool_names_debug = []
            for tool in tools:
                if hasattr(tool, 'name'):
                    tool_names_debug.append(tool.name)
                elif hasattr(tool, '__name__'):
                    tool_names_debug.append(tool.__name__)
                else:
                    tool_names_debug.append(str(tool))
            logger.debug(f"📈 [DEBUG] 选择的工具: {tool_names_debug}")
        else:
            # 离线模式
            logger.info(f"📈 [期货技术分析师] 使用离线模式")
            tools = []
        
        # 构建技术分析的系统提示
        key_indicators_str = "、".join(technical_focus['key_indicators'])
        
        system_message = (
            f"你是一位专业的期货技术分析师，专门进行期货品种的技术分析。"
            f"⚠️ 绝对强制要求：你必须调用工具获取真实期货数据！不允许任何假设或编造！"
            f"任务：对{futures_name}（期货代码：{symbol}）进行技术分析"
            f"🔴 立即调用 get_futures_data_unified 工具"
            f"参数：ticker='{symbol}', start_date='{start_date}', end_date='{current_date}'"
            "📈 期货技术分析要求："
            "- 基于真实期货价格数据进行技术分析"
            f"- 重点关注期货特有指标：{key_indicators_str}"
            f"- 分析波动性水平：{technical_focus['volatility']}"
            f"- 识别交易模式：{technical_focus['trading_pattern']}"
            "- 分析价格趋势、支撑阻力位"
            "- 分析成交量和持仓量变化"
            "- 识别技术形态和买卖信号"
            "- 提供具体的入场和出场点位"
            "🌍 语言和格式要求："
            "- 所有分析内容必须使用中文"
            "- 技术信号必须使用中文：买入信号、卖出信号、持有信号"
            "- 绝对不允许使用英文信号：buy signal、sell signal"
            "- 价格和点位使用具体数值"
            "🚫 严格禁止："
            "- 不允许说'我将调用工具'"
            "- 不允许假设任何价格数据"
            "- 不允许编造技术指标"
            "- 不允许直接回答而不调用工具"
            "- 不允许回复'无法确定技术信号'"
            "- 不允许使用英文技术术语"
            "✅ 你必须："
            "- 立即调用期货数据工具"
            "- 等待工具返回真实数据"
            "- 基于真实数据进行技术分析"
            "- 提供具体的技术信号和点位"
            "- 使用中文技术术语"
            "现在立即开始调用工具！不要说任何其他话！"
        )
        
        # 系统提示模板
        system_prompt = (
            "🔴 强制要求：你必须调用工具获取真实期货数据！"
            "🚫 绝对禁止：不允许假设、编造或直接回答任何问题！"
            "✅ 你必须：立即调用提供的工具获取真实数据，然后基于真实数据进行专业的期货技术分析。"
            "可用工具：{tool_names}。\n{system_message}"
            "当前日期：{current_date}。"
            "分析目标：{futures_name}（期货代码：{symbol}）。"
            "技术重点：{key_indicators}。"
            "波动特征：{volatility}，交易模式：{trading_pattern}。"
        )
        
        # 创建提示模板
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="messages"),
        ])
        
        prompt = prompt.partial(system_message=system_message)
        
        # 安全地获取工具名称
        tool_names = []
        for tool in tools:
            if hasattr(tool, 'name'):
                tool_names.append(tool.name)
            elif hasattr(tool, '__name__'):
                tool_names.append(tool.__name__)
            else:
                tool_names.append(str(tool))
        
        prompt = prompt.partial(tool_names=", ".join(tool_names) if tool_names else "无可用工具")
        prompt = prompt.partial(current_date=current_date)
        prompt = prompt.partial(symbol=symbol)
        prompt = prompt.partial(futures_name=futures_name)
        prompt = prompt.partial(key_indicators=key_indicators_str)
        prompt = prompt.partial(volatility=technical_focus['volatility'])
        prompt = prompt.partial(trading_pattern=technical_focus['trading_pattern'])
        
        # 检测阿里百炼模型并创建新实例
        if hasattr(llm, '__class__') and 'DashScope' in llm.__class__.__name__:
            logger.debug(f"📈 [DEBUG] 检测到阿里百炼模型，创建新实例以避免工具缓存")
            from tradingagents.llm_adapters import ChatDashScopeOpenAI
            fresh_llm = ChatDashScopeOpenAI(
                model=llm.model_name,
                temperature=llm.temperature,
                max_tokens=getattr(llm, 'max_tokens', 2000)
            )
        else:
            fresh_llm = llm
        
        logger.debug(f"📈 [DEBUG] 创建LLM链，工具数量: {len(tools)}")
        
        try:
            if tools:
                chain = prompt | fresh_llm.bind_tools(tools)
                logger.debug(f"📈 [DEBUG] ✅ 工具绑定成功，绑定了 {len(tools)} 个工具")
            else:
                chain = prompt | fresh_llm
                logger.debug(f"📈 [DEBUG] ✅ 创建无工具链（离线模式）")
        except Exception as e:
            logger.error(f"📈 [DEBUG] ❌ 工具绑定失败: {e}")
            raise e
        
        logger.debug(f"📈 [DEBUG] 调用LLM链...")
        result = chain.invoke(state["messages"])
        logger.debug(f"📈 [DEBUG] LLM调用完成")
        
        logger.debug(f"📈 [DEBUG] 结果类型: {type(result)}")
        logger.debug(f"📈 [DEBUG] 工具调用数量: {len(result.tool_calls) if hasattr(result, 'tool_calls') else 0}")
        logger.debug(f"📈 [DEBUG] 内容长度: {len(result.content) if hasattr(result, 'content') else 0}")
        
        # 处理期货技术分析报告
        if hasattr(result, 'tool_calls') and len(result.tool_calls) > 0:
            # 有工具调用，记录工具调用信息
            tool_calls_info = []
            for tc in result.tool_calls:
                tool_calls_info.append(tc['name'])
                logger.debug(f"📈 [DEBUG] 工具调用 {len(tool_calls_info)}: {tc}")
            
            logger.info(f"📈 [期货技术分析师] 工具调用: {tool_calls_info}")
            
            # 返回状态，让工具执行
            return {"messages": [result]}
        
        else:
            # 没有工具调用，使用强制工具调用修复
            logger.debug(f"📈 [DEBUG] 检测到模型未调用工具，启用强制工具调用模式")
            
            # 强制调用期货数据工具
            try:
                logger.debug(f"📈 [DEBUG] 强制调用 get_futures_data_unified...")
                
                # 安全地查找期货数据工具
                futures_tool = None
                for tool in tools:
                    tool_name = None
                    if hasattr(tool, 'name'):
                        tool_name = tool.name
                    elif hasattr(tool, '__name__'):
                        tool_name = tool.__name__
                    
                    if tool_name == 'get_futures_data_unified':
                        futures_tool = tool
                        break
                
                if futures_tool:
                    combined_data = futures_tool.invoke({
                        'ticker': symbol,
                        'start_date': start_date,
                        'end_date': current_date
                    })
                    logger.debug(f"📈 [DEBUG] 期货数据获取成功，长度: {len(combined_data)}字符")
                else:
                    combined_data = "期货数据工具不可用"
                    logger.debug(f"📈 [DEBUG] 期货数据工具未找到")
            except Exception as e:
                combined_data = f"期货数据获取失败: {e}"
                logger.debug(f"📈 [DEBUG] 期货数据获取异常: {e}")
            
            # 生成基于真实数据的技术分析报告
            analysis_prompt = f"""基于以下真实期货数据，对{futures_name}（期货代码：{symbol}）进行详细的技术分析：

{combined_data}

请提供：
1. 价格趋势分析（{futures_name}，代码：{symbol}）
2. 关键技术指标分析（{key_indicators_str}）
3. 支撑位和阻力位识别
4. 成交量和持仓量分析（期货特有）
5. 技术形态识别
6. 买卖信号判断和入场出场点位
7. 风险控制建议

技术分析要点：
- 波动性水平：{technical_focus['volatility']}
- 交易模式：{technical_focus['trading_pattern']}
- 重点指标：{key_indicators_str}

要求：
- 基于提供的真实数据进行分析
- 正确使用期货品种名称"{futures_name}"和代码"{symbol}"
- 技术信号使用中文（买入信号/卖出信号/持有信号）
- 提供具体的价格点位
- 分析要详细且专业"""
            
            try:
                # 创建简单的分析链
                analysis_prompt_template = ChatPromptTemplate.from_messages([
                    ("system", "你是专业的期货技术分析师，基于提供的真实数据进行技术分析。"),
                    ("human", "{analysis_request}")
                ])
                
                analysis_chain = analysis_prompt_template | fresh_llm
                analysis_result = analysis_chain.invoke({"analysis_request": analysis_prompt})
                
                if hasattr(analysis_result, 'content'):
                    report = analysis_result.content
                else:
                    report = str(analysis_result)
                
                logger.info(f"📈 [期货技术分析师] 强制工具调用完成，报告长度: {len(report)}")
                
            except Exception as e:
                logger.error(f"❌ [DEBUG] 强制工具调用分析失败: {e}")
                report = f"期货技术分析失败：{str(e)}"
            
            # return {"futures_technical_report": report}
            return {
            "messages": [result],
            "market_report": report,
            }
        logger.debug(f"📈 [DEBUG] 期货技术分析师节点结束"       )
        
        
        # 这里不应该到达，但作为备用
        logger.debug(f"📈 [DEBUG] 返回状态: futures_technical_report长度={len(result.content) if hasattr(result, 'content') else 0}")
        return {"messages": [result]}
    
    return futures_technical_analyst_node