"""
期货基本面分析师 - 专门分析期货品种基本面信息
支持商品期货、金融期货的供需分析、宏观因素分析等
"""

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import AIMessage

# 导入分析模块日志装饰器
from tradingagents.utils.tool_logging import log_analyst_module

# 导入统一日志系统
from tradingagents.utils.logging_init import get_logger
logger = get_logger("default")


def _get_futures_name_for_analysis(symbol: str, futures_info: dict) -> str:
    """
    为基本面分析师获取期货品种名称
    
    Args:
        symbol: 期货代码
        futures_info: 期货信息字典
        
    Returns:
        str: 期货品种名称
    """
    try:
        if 'name' in futures_info and futures_info['name']:
            return futures_info['name']
        else:
            # 备用方案：根据代码推断名称
            name_mapping = {
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
            
            # 提取品种代码
            underlying = symbol.upper()
            if underlying.endswith('99'):
                underlying = underlying[:-2]
            elif len(underlying) > 2 and underlying[-2:].isdigit():
                underlying = underlying[:-2]
            elif len(underlying) > 4 and underlying[-4:].isdigit():
                underlying = underlying[:-4]
            
            return name_mapping.get(underlying, f'期货{underlying}')
            
    except Exception as e:
        logger.error(f"❌ [期货基本面分析师] 获取期货名称失败: {e}")
        return f'期货{symbol}'


def _get_futures_category(symbol: str) -> dict:
    """
    获取期货品种分类信息
    
    Args:
        symbol: 期货代码
        
    Returns:
        dict: 分类信息
    """
    # 提取品种代码
    underlying = symbol.upper()
    if underlying.endswith('99'):
        underlying = underlying[:-2]
    elif len(underlying) > 2 and underlying[-2:].isdigit():
        underlying = underlying[:-2]
    elif len(underlying) > 4 and underlying[-4:].isdigit():
        underlying = underlying[:-4]
    
    # 期货分类
    categories = {
        # 金融期货
        'financial': {
            'names': ['IF', 'IH', 'IC', 'IM', 'T', 'TF', 'TS'],
            'category': '金融期货',
            'analysis_focus': ['利率政策', '股市走势', '资金流向', '经济指标']
        },
        
        # 贵金属
        'precious_metals': {
            'names': ['AU', 'AG'],
            'category': '贵金属',
            'analysis_focus': ['通胀预期', '美元指数', '地缘政治', '央行政策']
        },
        
        # 有色金属
        'base_metals': {
            'names': ['CU', 'AL', 'ZN', 'PB', 'NI', 'SN', 'BC'],
            'category': '有色金属',
            'analysis_focus': ['供需平衡', '库存变化', '下游需求', '进出口数据']
        },
        
        # 黑色系
        'ferrous_metals': {
            'names': ['RB', 'HC', 'SS', 'I', 'J', 'JM'],
            'category': '黑色系',
            'analysis_focus': ['钢材需求', '原料供应', '房地产政策', '基建投资']
        },
        
        # 能源化工
        'energy_chemical': {
            'names': ['SC', 'FU', 'LU', 'BU', 'RU', 'L', 'V', 'PP', 'TA', 'MA', 'ZC', 'UR', 'SA', 'PF'],
            'category': '能源化工',
            'analysis_focus': ['原油价格', '产能变化', '环保政策', '下游开工率']
        },
        
        # 农产品
        'agricultural': {
            'names': ['C', 'CS', 'A', 'B', 'M', 'Y', 'P', 'CF', 'SR', 'OI', 'RM', 'AP', 'CJ', 'JD'],
            'category': '农产品',
            'analysis_focus': ['天气因素', '种植面积', '产量预期', '进出口政策']
        },
        
        # 工业品
        'industrial': {
            'names': ['FG', 'SI', 'LC'],
            'category': '工业品',
            'analysis_focus': ['产业政策', '技术进步', '新能源发展', '制造业景气度']
        }
    }
    
    for category_key, category_info in categories.items():
        if underlying in category_info['names']:
            return {
                'category': category_info['category'],
                'analysis_focus': category_info['analysis_focus'],
                'underlying': underlying
            }
    
    # 默认分类
    return {
        'category': '其他期货',
        'analysis_focus': ['供需关系', '库存变化', '政策影响', '宏观经济'],
        'underlying': underlying
    }


def create_futures_fundamentals_analyst(llm, toolkit):
    @log_analyst_module("futures_fundamentals")
    def futures_fundamentals_analyst_node(state):
        logger.debug(f"📊 [DEBUG] ===== 期货基本面分析师节点开始 =====")
        
        current_date = state["trade_date"]
        symbol = state["company_of_interest"]
        start_date = '2025-05-28'
        
        logger.debug(f"📊 [DEBUG] 输入参数: symbol={symbol}, date={current_date}")
        logger.debug(f"📊 [DEBUG] 当前状态中的消息数量: {len(state.get('messages', []))}")
        logger.debug(f"📊 [DEBUG] 现有期货基本面报告: {state.get('futures_fundamentals_report', 'None')}")
        
        # 检查是否为期货代码
        from tradingagents.dataflows.data_source_manager import is_futures_symbol_unified, get_futures_info_unified
        
        if not is_futures_symbol_unified(symbol):
            logger.warning(f"⚠️ [期货基本面分析师] {symbol} 不是期货代码，跳过分析")
            return {"futures_fundamentals_report": f"❌ {symbol} 不是期货代码，无法进行期货基本面分析"}
        
        logger.info(f"📊 [期货基本面分析师] 正在分析期货品种: {symbol}")
        
        # 获取期货基本信息
        futures_info = get_futures_info_unified(symbol)
        futures_name = _get_futures_name_for_analysis(symbol, futures_info)
        category_info = _get_futures_category(symbol)
        
        logger.debug(f"📊 [DEBUG] 期货品种信息: {futures_name} - {category_info['category']}")
        logger.debug(f"📊 [DEBUG] 分析重点: {category_info['analysis_focus']}")
        logger.debug(f"📊 [DEBUG] 工具配置检查: online_tools={toolkit.config['online_tools']}")
        
        # 选择工具
        if toolkit.config["online_tools"]:
            # 使用期货数据工具
            logger.info(f"📊 [期货基本面分析师] 使用在线期货数据工具")
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
            logger.debug(f"📊 [DEBUG] 选择的工具: {tool_names_debug}")
        else:
            # 离线模式：使用缓存数据
            logger.info(f"📊 [期货基本面分析师] 使用离线模式")
            tools = []
        
        # 构建针对期货的分析提示
        analysis_focus_str = "、".join(category_info['analysis_focus'])
        
        system_message = (
            f"你是一位专业的期货基本面分析师，专门分析{category_info['category']}。"
            f"⚠️ 绝对强制要求：你必须调用工具获取真实数据！不允许任何假设或编造！"
            f"任务：分析{futures_name}（期货代码：{symbol}，{category_info['category']}）"
            f"🔴 立即调用 get_futures_data_unified 工具"
            f"参数：ticker='{symbol}', start_date='{start_date}', end_date='{current_date}', curr_date='{current_date}'"
            "📊 期货基本面分析要求："
            "- 基于真实期货数据进行深度基本面分析"
            f"- 重点关注{category_info['category']}的特有因素：{analysis_focus_str}"
            "- 分析供需关系、库存变化、政策影响"
            "- 提供合理的价格区间和趋势判断"
            "- 包含持仓量、成交量等期货特有指标分析"
            "- 考虑宏观经济因素对期货价格的影响"
            "🌍 语言和格式要求："
            "- 所有分析内容必须使用中文"
            "- 投资建议必须使用中文：买入、持有、卖出"
            "- 绝对不允许使用英文：buy、hold、sell"
            "- 价格单位使用人民币（¥）"
            "🚫 严格禁止："
            "- 不允许说'我将调用工具'"
            "- 不允许假设任何数据"
            "- 不允许编造期货信息"
            "- 不允许直接回答而不调用工具"
            "- 不允许回复'无法确定价位'或'需要更多信息'"
            "- 不允许使用英文投资建议（buy/hold/sell）"
            "✅ 你必须："
            "- 立即调用期货数据工具"
            "- 等待工具返回真实数据"
            "- 基于真实数据进行专业分析"
            "- 提供具体的价格区间和投资建议"
            "- 使用中文投资建议（买入/持有/卖出）"
            "现在立即开始调用工具！不要说任何其他话！"
        )
        
        # 系统提示模板
        system_prompt = (
            "🔴 强制要求：你必须调用工具获取真实期货数据！"
            "🚫 绝对禁止：不允许假设、编造或直接回答任何问题！"
            "✅ 你必须：立即调用提供的工具获取真实数据，然后基于真实数据进行专业的期货基本面分析。"
            "可用工具：{tool_names}。\n{system_message}"
            "当前日期：{current_date}。"
            "分析目标：{futures_name}（期货代码：{symbol}，类别：{category}）。"
            "分析重点：{analysis_focus}。"
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
        prompt = prompt.partial(category=category_info['category'])
        prompt = prompt.partial(analysis_focus=analysis_focus_str)
        
        # 检测阿里百炼模型并创建新实例
        if hasattr(llm, '__class__') and 'DashScope' in llm.__class__.__name__:
            logger.debug(f"📊 [DEBUG] 检测到阿里百炤模型，创建新实例以避免工具缓存")
            from tradingagents.llm_adapters import ChatDashScopeOpenAI
            fresh_llm = ChatDashScopeOpenAI(
                model=llm.model_name,
                temperature=llm.temperature,
                max_tokens=getattr(llm, 'max_tokens', 2000)
            )
        else:
            fresh_llm = llm
        
        logger.debug(f"📊 [DEBUG] 创建LLM链，工具数量: {len(tools)}")
        
        try:
            if tools:
                chain = prompt | fresh_llm.bind_tools(tools)
                logger.debug(f"📊 [DEBUG] ✅ 工具绑定成功，绑定了 {len(tools)} 个工具")
            else:
                chain = prompt | fresh_llm
                logger.debug(f"📊 [DEBUG] ✅ 创建无工具链（离线模式）")
        except Exception as e:
            logger.error(f"📊 [DEBUG] ❌ 工具绑定失败: {e}")
            raise e
        
        logger.debug(f"📊 [DEBUG] 调用LLM链...")
        result = chain.invoke(state["messages"])
        logger.debug(f"📊 [DEBUG] LLM调用完成")
        
        logger.debug(f"📊 [DEBUG] 结果类型: {type(result)}")
        logger.debug(f"📊 [DEBUG] 工具调用数量: {len(result.tool_calls) if hasattr(result, 'tool_calls') else 0}")
        logger.debug(f"📊 [DEBUG] 内容长度: {len(result.content) if hasattr(result, 'content') else 0}")
        
        # 处理期货基本面分析报告
        if hasattr(result, 'tool_calls') and len(result.tool_calls) > 0:
            # 有工具调用，记录工具调用信息
            tool_calls_info = []
            for tc in result.tool_calls:
                tool_calls_info.append(tc['name'])
                logger.debug(f"📊 [DEBUG] 工具调用 {len(tool_calls_info)}: {tc}")
            
            logger.info(f"📊 [期货基本面分析师] 工具调用: {tool_calls_info}")
            
            # 返回状态，让工具执行
            return {"messages": [result]}
        
        else:
            # 没有工具调用，使用强制工具调用修复
            logger.debug(f"📊 [DEBUG] 检测到模型未调用工具，启用强制工具调用模式")
            
            # 强制调用期货数据工具
            try:
                logger.debug(f"📊 [DEBUG] 强制调用 get_futures_data_unified...")
                
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
                        'end_date': current_date,
                        'curr_date': current_date
                    })
                    logger.debug(f"📊 [DEBUG] 期货数据获取成功，长度: {len(combined_data)}字符")
                else:
                    combined_data = "期货数据工具不可用"
                    logger.debug(f"📊 [DEBUG] 期货数据工具未找到")
            except Exception as e:
                combined_data = f"期货数据获取失败: {e}"
                logger.debug(f"📊 [DEBUG] 期货数据获取异常: {e}")
            
            # 生成基于真实数据的分析报告
            analysis_prompt = f"""基于以下真实期货数据，对{futures_name}（期货代码：{symbol}，{category_info['category']}）进行详细的基本面分析：

{combined_data}

请提供：
1. 期货品种基本信息分析（{futures_name}，代码：{symbol}）
2. 供需关系分析
3. 库存和持仓量分析
4. 影响价格的关键因素（{analysis_focus_str}）
5. 价格趋势和区间判断
6. 投资建议（买入/持有/卖出）

要求：
- 基于提供的真实数据进行分析
- 重点关注{category_info['category']}的特有因素
- 正确使用期货品种名称"{futures_name}"和代码"{symbol}"
- 价格使用人民币（¥）
- 投资建议使用中文
- 分析要详细且专业"""
            
            try:
                # 创建简单的分析链
                analysis_prompt_template = ChatPromptTemplate.from_messages([
                    ("system", "你是专业的期货基本面分析师，基于提供的真实数据进行分析。"),
                    ("human", "{analysis_request}")
                ])
                
                analysis_chain = analysis_prompt_template | fresh_llm
                analysis_result = analysis_chain.invoke({"analysis_request": analysis_prompt})
                
                if hasattr(analysis_result, 'content'):
                    report = analysis_result.content
                else:
                    report = str(analysis_result)
                
                logger.info(f"📊 [期货基本面分析师] 强制工具调用完成，报告长度: {len(report)}")
                
            except Exception as e:
                logger.error(f"❌ [DEBUG] 强制工具调用分析失败: {e}")
                report = f"期货基本面分析失败：{str(e)}"
            
            return {"futures_fundamentals_report": report}
        
        # 这里不应该到达，但作为备用
        logger.debug(f"📊 [DEBUG] 返回状态: futures_fundamentals_report长度={len(result.content) if hasattr(result, 'content') else 0}")
        return {"messages": [result]}
    
    return futures_fundamentals_analyst_node