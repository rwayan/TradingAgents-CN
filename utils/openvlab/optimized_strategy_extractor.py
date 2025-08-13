#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
优化的策略描述提取器
基于DOM结构分析，精确提取"策略名称 + 具体动作"格式的描述
"""

import time
import logging
import sys
import os
import re
import json
from typing import Optional, Dict, List

# Fix Windows console encoding
if sys.platform == "win32":
    try:
        import codecs
        if hasattr(sys.stdout, 'buffer'):
            sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer)
            sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer)
    except:
        pass

from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext
import asyncio

class OptimizedStrategyExtractor:
    """优化的策略描述提取器"""
    
    def __init__(self, headless: bool = True, timeout: int = 60):
        self.timeout = timeout * 1000  # Playwright uses milliseconds
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self._setup_browser(headless)
    
    def _setup_browser(self, headless: bool):
        """设置Playwright浏览器 - 支持Linux无图形界面"""
        try:
            logging.info("设置Playwright浏览器（优化版）...")
            
            self.playwright = sync_playwright().start()
            
            # 启动浏览器
            self.browser = self.playwright.chromium.launch(
                headless=headless,
                args=[
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                    "--disable-extensions",
                    "--disable-plugins",
                    "--disable-images",
                    "--disable-web-security",
                    "--allow-running-insecure-content",
                    "--disable-features=VizDisplayCompositor",
                    "--disable-background-timer-throttling",
                    "--disable-backgrounding-occluded-windows",
                    "--disable-renderer-backgrounding",
                    "--memory-pressure-off",
                    "--max_old_space_size=4096"
                ]
            )
            
            # 创建浏览器上下文
            self.context = self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            )
            
            # 创建新页面
            self.page = self.context.new_page()
            
            # 设置默认超时
            self.page.set_default_timeout(self.timeout)
            
            logging.info("Playwright浏览器设置成功")
            
        except Exception as e:
            raise Exception(f"无法初始化Playwright浏览器: {e}")
    
    def extract_precise_strategy_descriptions(self, strategy_code: str, target_price: float, 
                                            output_dir: str = "optimized_results", save_svg_files: bool = False) -> Dict:
        """
        提取精确的策略描述（策略名称 + 具体动作格式）
        
        Args:
            strategy_code: 策略代码
            target_price: 目标价格
            output_dir: 输出目录
            
        Returns:
            包含精确策略描述和SVG的结果字典
        """
        print(f"🎯 开始优化的策略提取流程")
        print(f"策略: {strategy_code}, 目标价格: {target_price}")
        
        os.makedirs(output_dir, exist_ok=True)
        
        results = {
            'strategy_code': strategy_code,
            'target_price': target_price,
            'success': False,
            'precise_descriptions': [],
            'svg_files_with_descriptions': [],
            'errors': []
        }
        
        try:
            # 步骤1: 访问页面
            url = f"https://openvlab.cn/strategy/optimizer/{strategy_code}"
            print(f"🌐 访问页面: {url}")
            self.page.goto(url)
            time.sleep(8)
            
            # 步骤2: 设置目标价格
            print(f"🎯 设置目标价格: {target_price}")
            self._set_target_price(target_price)
            time.sleep(5)
            
            # 步骤3: 提取精确策略描述
            print("📋 提取精确策略描述")
            precise_descriptions = self._extract_precise_descriptions()
            results['precise_descriptions'] = precise_descriptions
            
            if not precise_descriptions:
                results['errors'].append("未找到任何精确的策略描述")
                return results
            
            print(f"✅ 找到 {len(precise_descriptions)} 个精确策略描述")
            for i, desc in enumerate(precise_descriptions):
                print(f"  {i+1}. {desc['strategy_name']} {desc['action_description']}")
            
            # 步骤4: 获取SVG并匹配描述
            print("📊 获取SVG图表并匹配描述")
            time.sleep(5)  # 额外等待SVG加载
            svg_files = self._get_svgs_with_matched_descriptions(precise_descriptions, strategy_code, target_price, output_dir, save_svg_files)
            results['svg_files_with_descriptions'] = svg_files
            
            # 步骤4.5: 找出E值最高的策略
            print("\n📊 计算推荐策略（E值最高）")
            best_strategy = None
            max_e_value = -float('inf')
            
            for desc in results['precise_descriptions']:
                e_value = desc.get('financial_info', {}).get('e_value')
                if e_value is not None and e_value > max_e_value:
                    max_e_value = e_value
                    best_strategy = desc
            
            if best_strategy:
                results['best_strategy'] = best_strategy
                results['max_e_value'] = max_e_value
                print(f"🏆 推荐策略: {best_strategy['full_description']}")
                print(f"   E值: {max_e_value:.4f}")
                print(f"   {best_strategy['financial_info']['summary']}")
            else:
                print("⚠️  未能计算出推荐策略（E值数据不足）")
            
            # 步骤5: 生成报告
            print("📄 生成优化报告")
            report_file = self._create_optimized_report(results, output_dir)
            results['report_file'] = report_file
            
            # 步骤6: 创建HTML展示
            print("🌐 创建HTML展示页面")
            html_file = self._create_optimized_html_page(results, output_dir)
            results['html_file'] = html_file
            
            # 步骤7: 保存完整结果
            summary_file = f"{output_dir}/optimized_results_{strategy_code}_{target_price}.json"
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            results['summary_file'] = summary_file
            
            results['success'] = True
            
            print(f"✅ 优化流程成功完成!")
            print(f"📄 结果摘要: {summary_file}")
            print(f"📋 详细报告: {report_file}")
            print(f"🌐 HTML展示: {html_file}")
            
            return results
            
        except Exception as e:
            error_msg = f"优化流程执行失败: {str(e)}"
            print(f"❌ {error_msg}")
            results['errors'].append(error_msg)
            return results
    
    def _set_target_price(self, target_price: float):
        """设置目标价格（强化版本）"""
        try:
            print(f"开始设置目标价格: {target_price}")
            
            # 方法1: 查找所有可能的价格输入框
            input_selectors = [
                'input[type="number"]',
                'input[type="text"]',
                'input[inputmode="numeric"]',
                'input[inputmode="decimal"]',
                'input[pattern*="[0-9]"]'
            ]
            
            input_element = None
            for selector in input_selectors:
                try:
                    elements = self.page.locator(selector).all()
                    print(f"找到 {len(elements)} 个 {selector} 元素")
                    
                    for i, element in enumerate(elements):
                        if element.is_visible() and element.is_enabled():
                            current_value = element.get_attribute('value') or ''
                            placeholder = element.get_attribute('placeholder') or ''
                            print(f"  元素 {i+1}: 当前值='{current_value}', 占位符='{placeholder}'")
                            
                            # 判断是否为价格输入框
                            if current_value and any(c.isdigit() for c in current_value):
                                try:
                                    current_num = float(current_value.replace(',', ''))
                                    # 如果当前值在合理的期货价格范围内（比如5000-10000）
                                    if 5000 <= current_num <= 15000:
                                        input_element = element
                                        print(f"  选择价格输入框: 当前值={current_value}")
                                        break
                                except:
                                    pass
                            
                            # 如果没找到，选择第一个有数字的输入框
                            if not input_element and current_value and any(c.isdigit() for c in current_value):
                                input_element = element
                                print(f"  回退选择输入框: 当前值={current_value}")
                    
                    if input_element:
                        break
                except Exception as e:
                    print(f"查找 {selector} 时出错: {e}")
                    continue
            
            if input_element:
                print(f"找到价格输入框，开始设置价格...")
                
                # 多次尝试设置价格
                for attempt in range(3):
                    try:
                        print(f"  尝试 {attempt + 1}: 清空并输入价格")
                        
                        # 清空现有值
                        input_element.clear()
                        time.sleep(0.5)
                        
                        # 输入新价格
                        input_element.fill(str(int(target_price)))
                        time.sleep(0.5)
                        
                        # 触发Tab和Enter键
                        input_element.press('Tab')
                        time.sleep(0.5)
                        input_element.press('Enter')
                        time.sleep(0.5)
                        
                        # JavaScript事件触发
                        self.page.evaluate("""
                            (element) => {
                                if (element && element.dispatchEvent) {
                                    element.dispatchEvent(new Event('input', {bubbles: true}));
                                    element.dispatchEvent(new Event('change', {bubbles: true}));
                                    element.dispatchEvent(new Event('blur', {bubbles: true}));
                                }
                            }
                        """, input_element)
                        time.sleep(1)
                        
                        # 检查是否设置成功
                        new_value = input_element.get_attribute('value') or ''
                        print(f"  设置后的值: {new_value}")
                        
                        if str(int(target_price)) in new_value:
                            print(f"价格设置成功: {new_value}")
                            time.sleep(3)  # 等待页面更新
                            return
                        
                    except Exception as e:
                        print(f"  尝试 {attempt + 1} 失败: {e}")
                        time.sleep(1)
                
                print("多次尝试后价格设置可能未完全生效")
                time.sleep(5)  # 额外等待时间
                
            else:
                print("未找到价格输入框，使用默认价格")
                
        except Exception as e:
            print(f"设置价格时出现问题: {e}")
            time.sleep(3)
    
    def _extract_precise_descriptions(self) -> List[Dict]:
        """基于DOM结构提取精确的策略描述（包含财务信息）"""
        precise_descriptions = []
        
        try:
            # 根据之前分析的结果，查找策略卡片容器
            card_selector = "div.bg-card.text-card-foreground"
            
            # 尝试不同的选择器来找到策略容器
            container_selectors = [
                card_selector,
                "div[class*='bg-card']",
                "div[class*='shadow-sm']",
                "div[class*='rounded-xl']"
            ]
            
            strategy_containers = []
            for selector in container_selectors:
                try:
                    elements = self.page.locator(selector).all()
                    for element in elements:
                        if element.is_visible():  # 策略卡片通常比较大
                            bbox = element.bounding_box()
                            if bbox and bbox['height'] > 300:
                                text = element.inner_text().strip()
                                if text and any(keyword in text for keyword in ['期权', '价差', '买入', '卖出']):
                                    strategy_containers.append(element)
                    if strategy_containers:
                        break
                except Exception as e:
                    continue
            
            print(f"找到 {len(strategy_containers)} 个策略容器")
            
            # 从每个策略容器中提取完整策略信息（包含财务数据）
            for i, container in enumerate(strategy_containers):
                try:
                    container_text = container.inner_text().strip()
                    lines = [line.strip() for line in container_text.split('\n') if line.strip()]
                    
                    if len(lines) >= 2:
                        # 第一行：策略名称（如"买入看涨期权"）
                        strategy_name = lines[0]
                        
                        # 第二行：具体动作（如"买入1手 6500C"或"持有标的, 卖出1手 7100C"）
                        action_description = lines[1]
                        
                        # 验证是否符合预期格式
                        if (self._is_valid_strategy_name(strategy_name) and 
                            self._is_valid_action_description(action_description)):
                            
                            # 提取完整的财务信息（基于DOM结构）
                            financial_info = self._extract_financial_info(container)
                            
                            precise_desc = {
                                'index': i + 1,
                                'strategy_name': strategy_name,
                                'action_description': action_description,
                                'financial_info': financial_info,
                                'full_description': f"{strategy_name} {action_description}",
                                'complete_info': f"{strategy_name} {action_description} | {financial_info['summary']}",
                                'source': 'strategy_container'
                            }
                            precise_descriptions.append(precise_desc)
                            
                            print(f"✅ 提取到完整策略信息:")
                            print(f"   策略: {strategy_name} {action_description}")
                            print(f"   财务: {financial_info['summary']}")
                        
                except Exception as e:
                    print(f"处理容器 {i+1} 时出现错误: {e}")
                    continue
            
            return precise_descriptions
            
        except Exception as e:
            print(f"❌ 提取精确描述时出现错误: {e}")
            return []
    
    def _is_valid_strategy_name(self, name: str) -> bool:
        """验证策略名称是否有效"""
        # 策略名称应该以"期权"或"价差"结尾，长度适中
        return (len(name) > 2 and len(name) < 30 and
                (name.endswith('期权') or name.endswith('价差')))
    
    def _is_valid_action_description(self, action: str) -> bool:
        """验证动作描述是否有效"""
        # 动作描述应该包含关键词且格式合理
        keywords = ['买入', '卖出', '持有标的']
        has_action = any(keyword in action for keyword in keywords)
        has_quantity = '手' in action
        has_option_code = bool(re.search(r'\d+[CP]', action))
        
        return has_action and (has_quantity or '持有标的' in action) and len(action) < 50
    
    def _extract_financial_info(self, container_element) -> dict:
        """直接从grid grid-cols-3 gap-1 rounded容器提取财务信息"""
        financial_info = {
            'max_loss': None,           # 最大亏损
            'expected_profit': None,    # 预期利润  
            'win_rate': None,          # 胜率
            'max_loss_value': None,    # 最大亏损数值（用于计算）
            'expected_profit_value': None,  # 预期利润数值（用于计算）
            'win_rate_value': None,    # 胜率数值（用于计算）
            'e_value': None,           # E值（期望收益率）
            'other_metrics': [],       # 其他财务指标
            'summary': ''              # 财务摘要
        }
        
        try:
            # 直接查找 grid grid-cols-3 gap-1 rounded 容器
            grid_selector = "div.grid.grid-cols-3.gap-1.rounded"
            
            financial_grids = container_element.locator(grid_selector).all()
            
            if financial_grids:
                for grid in financial_grids:
                    if grid.is_visible():
                        print(f"找到财务grid容器")
                        
                        # 获取grid中的所有直接子元素（应该是3列）
                        grid_cells = grid.locator("div").all()
                        
                        print(f"Grid包含 {len(grid_cells)} 个单元格")
                        
                        # 提取每个单元格的文本
                        cell_texts = []
                        for i, cell in enumerate(grid_cells):
                            if cell.is_visible():
                                cell_text = cell.inner_text().strip()
                                if cell_text:
                                    cell_texts.append(cell_text)
                                    print(f"  单元格{i+1}: {cell_text}")
                        
                        # 从单元格文本中直接提取财务数据
                        # grid是3x3布局，我们需要找到纯净的数值
                        for cell_text in cell_texts:
                            # 查找包含￥符号但不包含中文标签的单元格（纯数值）
                            if '￥' in cell_text and not any(label in cell_text for label in ['最大', '预期', '利润', '亏损']):
                                # 提取数值
                                value_str = cell_text.replace('￥', '').replace(',', '').strip()
                                try:
                                    value = float(value_str)
                                except:
                                    value = None
                                
                                if '-' in cell_text and not financial_info['max_loss']:
                                    # 负数金额是最大亏损
                                    financial_info['max_loss'] = cell_text
                                    financial_info['max_loss_value'] = abs(value) if value else None
                                elif '-' not in cell_text and not financial_info['expected_profit']:
                                    # 正数金额是预期利润
                                    financial_info['expected_profit'] = cell_text
                                    financial_info['expected_profit_value'] = value
                            
                            # 查找包含%符号但不包含中文标签的单元格（纯百分比）
                            elif '%' in cell_text and not any(label in cell_text for label in ['胜率', '成功率']) and not financial_info['win_rate']:
                                financial_info['win_rate'] = cell_text
                                # 提取百分比数值
                                try:
                                    win_rate_str = cell_text.replace('%', '').strip()
                                    financial_info['win_rate_value'] = float(win_rate_str) / 100.0
                                except:
                                    financial_info['win_rate_value'] = None
                        
                        # 如果找到了财务信息，跳出循环
                        if any([financial_info['max_loss'], financial_info['expected_profit'], financial_info['win_rate']]):
                            break
            
            # 如果没找到grid，回退到全文搜索
            if not any([financial_info['max_loss'], financial_info['expected_profit'], financial_info['win_rate']]):
                print("未找到财务grid，使用全文搜索")
                container_text = container_element.inner_text().strip()
                lines = container_text.split('\n')
                
                for line in lines:
                    line = line.strip()
                    if line:
                        # 简单的文本匹配
                        if '￥' in line:
                            if '-' in line and '亏损' in line and not financial_info['max_loss']:
                                financial_info['max_loss'] = line
                            elif '利润' in line and not financial_info['expected_profit']:
                                financial_info['expected_profit'] = line
                        elif '%' in line and ('胜率' in line or '成功率' in line) and not financial_info['win_rate']:
                            financial_info['win_rate'] = line
            
            # 构建财务摘要
            summary_parts = []
            if financial_info['max_loss']:
                summary_parts.append(f"最大亏损{financial_info['max_loss']}")
            if financial_info['expected_profit']:
                summary_parts.append(f"预期利润{financial_info['expected_profit']}")
            if financial_info['win_rate']:
                summary_parts.append(f"胜率{financial_info['win_rate']}")
            
            financial_info['summary'] = ' | '.join(summary_parts) if summary_parts else '财务信息待提取'
            
            # 计算E值（期望收益率）
            # E = 胜率 * 预期盈利 / abs(最大亏损)
            if (financial_info['win_rate_value'] is not None and 
                financial_info['expected_profit_value'] is not None and 
                financial_info['max_loss_value'] is not None and 
                financial_info['max_loss_value'] > 0):
                
                e_value = (financial_info['win_rate_value'] * financial_info['expected_profit_value']) / financial_info['max_loss_value']
                financial_info['e_value'] = round(e_value, 4)
                print(f"  E值计算: {financial_info['win_rate_value']:.2%} * {financial_info['expected_profit_value']:,.0f} / {financial_info['max_loss_value']:,.0f} = {e_value:.4f}")
            else:
                print(f"  E值计算失败: 缺少必要数据")
            
            return financial_info
            
        except Exception as e:
            print(f"提取财务信息时出现错误: {e}")
            financial_info['summary'] = '财务信息提取失败'
            return financial_info
    
    def _get_svgs_with_matched_descriptions(self, descriptions: List[Dict], strategy_code: str, 
                                          target_price: float, output_dir: str, save_svg_files: bool = False) -> List[Dict]:
        """获取SVG并匹配精确描述（基于策略容器结构）"""
        svg_files = []
        
        try:
            # 不再全局搜索SVG，而是从每个策略容器中提取SVG
            print(f"从策略容器中提取SVG图表")
            
            card_selector = "div.bg-card.text-card-foreground"
            strategy_containers = self.page.locator(card_selector).all()
            
            for i, container in enumerate(strategy_containers):
                if container.is_visible():
                    bbox = container.bounding_box()
                    if bbox and bbox['height'] > 300:
                        try:
                            # 在策略容器中查找SVG（在 div.flex-1.min-h-0 里面）
                            svg_container_selector = "div.flex-1.min-h-0"
                            svg_containers = container.locator(svg_container_selector).all()
                            
                            svg_found = False
                            for svg_container in svg_containers:
                                if svg_container.is_visible():
                                    # 在SVG容器中查找实际的SVG元素
                                    svg_elements = svg_container.locator("svg").all()
                                    
                                    for svg_element in svg_elements:
                                        if svg_element.is_visible():
                                            svg_content = svg_element.evaluate("el => el.outerHTML")
                                        
                                        if self._is_strategy_chart_svg(svg_content):
                                            print(f"在容器 {i+1} 中找到策略SVG")
                                            
                                            # 匹配对应的策略描述
                                            matched_description = None
                                            if i < len(descriptions):
                                                matched_description = descriptions[i]
                                            else:
                                                # 如果描述数量不足，创建默认描述
                                                matched_description = {
                                                    'index': i + 1,
                                                    'strategy_name': f'期权策略{i+1}',
                                                    'action_description': '策略操作',
                                                    'full_description': f'期权策略{i+1} 策略操作',
                                                    'financial_info': {'summary': '财务信息待提取'},
                                                    'source': 'default'
                                                }
                                            
                                            # 添加策略描述和财务信息到SVG
                                            enhanced_content = self._add_optimized_strategy_title_to_svg(
                                                svg_content, matched_description, strategy_code, target_price
                                            )
                                            
                                            # 可选：保存SVG文件作为备份
                                            enhanced_filename = None
                                            
                                            if save_svg_files:
                                                enhanced_filename = f"{output_dir}/{strategy_code}_{target_price}_chart_{i+1}_enhanced.svg"
                                                with open(enhanced_filename, 'w', encoding='utf-8') as f:
                                                    f.write(enhanced_content)
                                                print(f"保存增强SVG文件 {i+1}: {enhanced_filename}")
                                            
                                            file_info = {
                                                'index': i + 1,
                                                'enhanced_content': enhanced_content,  # 直接保存SVG内容
                                                'enhanced_file': enhanced_filename,  # 可能为None
                                                'matched_description': matched_description,
                                                'size': len(svg_content),
                                                'contains_target_price': str(int(target_price)) in svg_content,
                                                'container_index': i
                                            }
                                            
                                            svg_files.append(file_info)
                                            
                                            print(f"提取增强SVG {i+1}: {matched_description['full_description']}")
                                            if matched_description.get('financial_info'):
                                                print(f"  财务信息: {matched_description['financial_info'].get('summary', '')}")
                                            
                                            svg_found = True
                                            break
                                
                                if svg_found:
                                    break
                            
                            if not svg_found:
                                print(f"容器 {i+1} 中未找到SVG")
                                
                        except Exception as e:
                            print(f"处理容器 {i+1} 的SVG时出现错误: {e}")
                            continue
            
            print(f"总共提取到 {len(svg_files)} 个SVG图表")
            
            return svg_files
            
        except Exception as e:
            print(f"获取SVG时出现错误: {e}")
            return []
    
    def _is_strategy_chart_svg(self, svg_content: str) -> bool:
        """判断是否为策略图表SVG（宽松验证）"""
        if not svg_content or len(svg_content) < 500:  # 降低最小长度要求
            return False
        
        if '<svg' not in svg_content:
            return False
        
        # 检查是否包含图表特征（更宽松的判断）
        chart_indicators = [
            'width=',  # SVG必须有宽度
            'height=', # SVG必须有高度
            'path',    # 图表路径
            'line',    # 图表线条
            'linearGradient', # 渐变
            'rect'     # 图表元素
        ]
        
        # 只要包含基本的SVG图表元素就认为是策略图表
        count = sum(1 for indicator in chart_indicators if indicator in svg_content)
        return count >= 3  # 至少包含3个图表特征
    
    def _add_optimized_strategy_title_to_svg(self, svg_content: str, description: Dict, 
                                           strategy_code: str, target_price: float) -> str:
        """为SVG添加优化的策略标题（包含财务信息，解决重叠问题）"""
        try:
            # 修复SVG显示问题
            fixed_content = self._fix_svg_display_issues(svg_content)
            
            # 构建主标题文本（策略名称 + 动作）
            main_title = description['full_description']
            
            # 构建财务信息副标题
            financial_info = description.get('financial_info', {})
            financial_summary = financial_info.get('summary', '')
            
            # 提取原始SVG的宽度和高度
            import re
            width_match = re.search(r'width="(\d+)"', fixed_content)
            height_match = re.search(r'height="(\d+)"', fixed_content)
            viewbox_match = re.search(r'viewBox="([^"]+)"', fixed_content)
            
            if width_match and height_match:
                original_width = int(width_match.group(1))
                original_height = int(height_match.group(1))
                
                # 根据是否有财务信息决定新的高度和偏移
                if financial_summary and financial_summary != '财务信息待提取':
                    # 有财务信息：增加90像素容纳两行标题
                    new_height = original_height + 90
                    chart_offset = 50  # 图表向下偏移50像素
                    
                    # 主标题和财务信息副标题
                    title_elements = f'''<text x="{original_width//2}" y="20" text-anchor="middle" font-size="12" font-weight="bold" class="strategy-title-text">{main_title}</text>
<text x="{original_width//2}" y="35" text-anchor="middle" font-size="10" fill="#059669">{financial_summary}</text>'''
                else:
                    # 无财务信息：增加70像素
                    new_height = original_height + 70
                    chart_offset = 45  # 图表向下偏移45像素
                    
                    # 只有主标题
                    title_elements = f'''<text x="{original_width//2}" y="25" text-anchor="middle" font-size="12" font-weight="bold" class="strategy-title-text">{main_title}</text>'''
                
                # 更新SVG尺寸和viewBox
                enhanced_content = fixed_content.replace(f'height="{original_height}"', f'height="{new_height}"')
                
                # 更新viewBox - 保持宽度不变，只增加高度
                if viewbox_match:
                    old_viewbox = viewbox_match.group(1)
                    viewbox_parts = old_viewbox.split()
                    if len(viewbox_parts) == 4:
                        # viewBox="x y width height"
                        new_viewbox = f"{viewbox_parts[0]} {viewbox_parts[1]} {viewbox_parts[2]} {new_height}"
                        enhanced_content = enhanced_content.replace(f'viewBox="{old_viewbox}"', f'viewBox="{new_viewbox}"')
                
                # 包装整个图表内容到一个transform组中
                defs_end = enhanced_content.find('</defs>') + len('</defs>')
                svg_end = enhanced_content.rfind('</svg>')
                
                # 提取图表内容部分
                chart_content = enhanced_content[defs_end:svg_end].strip()
                
                # 重新构建SVG，标题在顶部，图表内容向下偏移
                enhanced_content = (
                    enhanced_content[:defs_end] + '\n' +
                    title_elements + '\n' +
                    f'<g transform="translate(0,{chart_offset})">' + '\n' +
                    chart_content + '\n' +
                    '</g>' + '\n' +
                    '</svg>'
                )
                
                return enhanced_content
            else:
                print("无法解析SVG尺寸，使用原始内容")
                return fixed_content
            
        except Exception as e:
            print(f"添加优化标题时出现问题: {e}")
            # 如果出现错误，至少返回修复后的内容
            return self._fix_svg_display_issues(svg_content)
    
    def _fix_svg_display_issues(self, svg_content: str) -> str:
        """修复SVG显示问题"""
        fixed_content = svg_content
        
        # 修复1: 替换动态占位符
        fixed_content = re.sub(r'«[^»]*»', 'static', fixed_content)
        
        # 修复2: 添加命名空间
        if 'xmlns=' not in fixed_content:
            fixed_content = fixed_content.replace('<svg', '<svg xmlns="http://www.w3.org/2000/svg"', 1)
        
        # 修复3: 转换CSS类为内联样式
        css_mappings = {
            'class="text-xs fill-current"': 'fill="currentColor" font-size="10px"',
            'class="text-[10px] fill-primary"': 'fill="#007bff" font-size="10px"',
            'class="text-[10px] fill-orange-500"': 'fill="#f97316" font-size="10px"',
            'class="text-xs fill-blue-500"': 'fill="#fb923c" font-size="10px"',
            'class="text-[10px] fill-blue-500"': 'fill="#fb923c" font-size="10px"',
            'class="stroke-primary stroke-0.5"': 'stroke="#007bff" stroke-width="0.5"',
            'class="stroke-current"': 'stroke="currentColor"',
            'class="stroke-orange-500 stroke-0.5"': 'stroke="#f97316" stroke-width="0.5"',
            'class="stroke-blue-500 stroke-0.5"': 'stroke="#fb923c" stroke-width="0.5"'
        }
        
        for old_class, inline_style in css_mappings.items():
            fixed_content = fixed_content.replace(old_class, inline_style)
        
        return fixed_content
    
    def _create_optimized_report(self, results: Dict, output_dir: str) -> str:
        """创建优化的报告"""
        report_content = f"""# {results['strategy_code']} 策略分析优化报告

## 基本信息
- 策略代码: {results['strategy_code']}
- 目标价格: {results['target_price']}
- 图表数量: {len(results['svg_files_with_descriptions'])}
- 精确描述数量: {len(results['precise_descriptions'])}

## 🏆 推荐策略（E值最高）

"""
        # 添加推荐策略信息
        if results.get('best_strategy'):
            best = results['best_strategy']
            best_financial = best.get('financial_info', {})
            report_content += f"### {best['strategy_name']}\n"
            report_content += f"- 具体动作: {best['action_description']}\n"
            report_content += f"- **E值: {results['max_e_value']:.4f}** （期望收益率）\n"
            report_content += f"- 财务信息: {best_financial['summary']}\n"
            report_content += f"- E值计算: {best_financial['win_rate']} × {best_financial['expected_profit']} ÷ abs({best_financial['max_loss']}) = {results['max_e_value']:.4f}\n\n"
        else:
            report_content += "未能计算出推荐策略（E值数据不足）\n\n"
        
        report_content += "## E值排名（从高到低）\n\n"
        
        # 对策略按E值排序
        sorted_strategies = sorted(
            results['precise_descriptions'], 
            key=lambda x: x.get('financial_info', {}).get('e_value') or -float('inf'), 
            reverse=True
        )
        
        for i, desc in enumerate(sorted_strategies):
            e_value = desc.get('financial_info', {}).get('e_value')
            if e_value is not None:
                report_content += f"{i+1}. {desc['full_description']} - **E值: {e_value:.4f}**\n"
                report_content += f"   {desc['financial_info']['summary']}\n\n"
        
        report_content += "\n## 精确策略描述\n\n"
        
        # 添加精确策略描述
        for i, desc in enumerate(results['precise_descriptions']):
            report_content += f"### 策略 {i+1}: {desc['strategy_name']}\n"
            report_content += f"- 具体动作: {desc['action_description']}\n"
            report_content += f"- 完整描述: {desc['full_description']}\n"
            
            # 添加财务信息
            financial_info = desc.get('financial_info', {})
            if financial_info and financial_info.get('summary'):
                report_content += f"- 财务信息: {financial_info['summary']}\n"
                if financial_info.get('max_loss'):
                    report_content += f"  - 最大亏损: {financial_info['max_loss']}\n"
                if financial_info.get('expected_profit'):
                    report_content += f"  - 预期利润: {financial_info['expected_profit']}\n"
                if financial_info.get('win_rate'):
                    report_content += f"  - 胜率: {financial_info['win_rate']}\n"
                if financial_info.get('other_metrics'):
                    report_content += f"  - 其他指标: {', '.join(financial_info['other_metrics'])}\n"
                if financial_info.get('e_value') is not None:
                    report_content += f"  - **E值: {financial_info['e_value']:.4f}**\n"
            
            report_content += f"- 来源: {desc['source']}\n\n"
        
        report_content += "\n## SVG图表与策略描述对应\n\n"
        
        # 添加每个SVG的匹配信息
        for svg_file in results['svg_files_with_descriptions']:
            matched_desc = svg_file['matched_description']
            report_content += f"### 图表 {svg_file['index']}\n"
            report_content += f"- 增强文件: `{os.path.basename(svg_file['enhanced_file']) if svg_file.get('enhanced_file') else '内存中'}`\n"
            report_content += f"- 策略名称: {matched_desc['strategy_name']}\n"
            report_content += f"- 具体动作: {matched_desc['action_description']}\n"
            report_content += f"- 完整描述: {matched_desc['full_description']}\n"
            report_content += f"- 包含目标价格: {'是' if svg_file['contains_target_price'] else '否'}\n\n"
        
        report_content += f"""
## 优化改进

### 1. 精确描述提取
- ✅ 基于DOM结构分析，只提取"策略名称 + 具体动作"格式的描述
- ✅ 排除了冗余的数据和说明文字
- ✅ 确保每个描述都符合用户要求的标准格式

### 2. 内存优化
- ✅ SVG内容直接保存在内存中，无需中间文件
- ✅ 可选择性保存SVG文件作为备份
- ✅ 减少磁盘I/O操作，提高处理效率

### 3. 技术特点
- ✅ 支持Linux无图形界面环境
- ✅ 基于结构化DOM分析的精确匹配
- ✅ 优化的SVG标题布局和样式

生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        # 保存报告
        report_file = f"{output_dir}/optimized_strategy_report_{results['strategy_code']}_{results['target_price']}.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        return report_file
    
    def _create_optimized_html_page(self, results: Dict, output_dir: str) -> str:
        """创建优化的HTML展示页面"""
        html_content = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{results['strategy_code']} 策略图表优化展示 - 目标价格 {results['target_price']}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 20px; background: #f8fafc; }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        .header {{ text-align: center; margin-bottom: 30px; padding: 25px; background: white; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .header h1 {{ color: #1e293b; margin-bottom: 10px; }}
        .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }}
        .summary-card {{ background: white; padding: 20px; text-align: center; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .summary-number {{ font-size: 24px; font-weight: bold; color: #0f172a; }}
        .summary-label {{ color: #64748b; margin-top: 5px; }}
        .strategy-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(420px, 1fr)); gap: 25px; margin: 30px 0; }}
        .strategy-item {{ background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.1);  border: 1px solid #f59e0b;}}
        .strategy-item.best-strategy {{ 
            border: 3px solid #f59e0b; 
            box-shadow: 0 4px 20px rgba(245, 158, 11, 0.3);
            position: relative;
            overflow: visible;  /* 允许徽章显示在容器外 */
            margin-top: 0px;   /* 为徽章留出空间 */
        }}
        .best-strategy-badge {{ 
            position: absolute; 
            top: -12px;  /* 调整位置，使其不会被截断 */
            right: 20px; 
            background: #f59e0b; 
            color: white; 
            padding: 6px 14px; 
            border-radius: 16px; 
            font-weight: bold; 
            font-size: 13px;
            display: flex;
            align-items: center;
            gap: 5px;
            box-shadow: 0 2px 8px rgba(245, 158, 11, 0.3);
            z-index: 1;
        }}
        .strategy-header {{ background: #fff7ed; color: #475569; padding: 20px; }}
        .best-strategy .strategy-header {{ background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%); color: #92400e; }}
        .strategy-title {{ font-size: 18px; font-weight: bold; margin-bottom: 8px; }}
        .strategy-desc {{ opacity: 0.9; font-size: 14px; line-height: 1.4; margin-bottom: 8px; }}
        .financial-info {{ background: rgba(255,255,255,0.15); padding: 8px 12px; border-radius: 6px; font-size: 13px; margin-top: 8px; border-left: 3px solid; color: #059669; }}
        .best-strategy .financial-info {{ background: rgba(255,255,255,0.15); padding: 8px 12px; border-radius: 6px; font-size: 13px; margin-top: 8px; border-left: 3px solid ; color: #92400e; font-weight: bold;}}
        .e-value-display {{ 
            background: rgba(255,255,255,0.25); 
            padding: 6px 10px; 
            border-radius: 4px; 
            font-size: 14px; 
            margin-top: 6px; 
            border-left: 3px solid #fff; 
            font-weight: bold;
            color: #059669; 
        }}
        .best-strategy .e-value-display {{color: #92400e;    font-weight: bold;}}
        .svg-container {{ padding: 20px; text-align: center; }}
        .svg-container svg {{ max-width: 100%; height: auto; border: 1px solid #e2e8f0; border-radius: 8px; }}
        /* SVG内文字颜色统一 */
        .strategy-item .strategy-title-text {{ fill: #1e293b; }}  /* 普通策略SVG标题颜色 */
        .best-strategy .strategy-title-text {{ fill: #92400e; }}  /* 推荐策略SVG标题颜色 */
        .descriptions-section {{ background: white; padding: 25px; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin: 30px 0; }}
        .description-item {{ background: #fff7ed; padding: 15px; border-radius: 8px; margin: 10px 0; border-left: 4px solid #fb923c; }}
        .description-item.best-strategy {{ 
            background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);  /* 金黄色渐变背景 */
            border-left: 4px solid #f59e0b;  /* 橙色边框 */
            box-shadow: 0 4px 15px rgba(245, 158, 11, 0.2);  /* 橙色阴影 */
            position: relative;
            transform: scale(1.02);  /* 稍微放大 */
            margin: 15px 0;
        }}
        .best-strategy .description-strategy {{
            color: #92400e;  /* 深橙色文字 */
            font-size: 17px;  /* 稍大的字体 */
        }}
        .best-strategy .description-financial {{
            background: rgba(245, 158, 11, 0.15);  /* 橙色背景 */
            border-left-color: #f59e0b;  /* 橙色边框 */
            color: #92400e;  /* 深橙色文字 */
            font-weight: 600;
        }}
        .description-strategy {{ font-size: 16px; font-weight: bold; color: #1e293b; }}
        .description-action {{ color: #475569; margin-top: 5px; }}
        .description-financial {{ color: #059669; font-size: 14px; margin-top: 8px; padding: 8px; background: rgba(5, 150, 105, 0.1); border-radius: 4px; border-left: 3px solid #059669; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 {results['strategy_code']} 策略分析优化展示</h1>
            <p>目标价格: <strong>{results['target_price']}</strong> | 精确匹配策略描述与SVG图表</p>
        </div>
        
        <div class="summary">
            <div class="summary-card">
                <div class="summary-number">{len(results['svg_files_with_descriptions'])}</div>
                <div class="summary-label">策略图表</div>
            </div>
            <div class="summary-card">
                <div class="summary-number">{len(results['precise_descriptions'])}</div>
                <div class="summary-label">精确描述</div>
            </div>
            <div class="summary-card">
                <div class="summary-number">{results['target_price']}</div>
                <div class="summary-label">目标价格</div>
            </div>
            <div class="summary-card">
                <div class="summary-number">优化版本</div>
                <div class="summary-label">文件类型</div>
            </div>
        </div>
        
        <div class="strategy-grid">'''
        
        # 为每个SVG添加展示卡片
        best_strategy_index = results.get('best_strategy', {}).get('index')
        
        for svg_file in results['svg_files_with_descriptions']:
            matched_desc = svg_file['matched_description']
            financial_info = matched_desc.get('financial_info', {})
            
            # 检查是否是推荐策略
            is_best = matched_desc.get('index') == best_strategy_index
            strategy_class = 'strategy-item best-strategy' if is_best else 'strategy-item'
            
            # 构建财务信息显示
            financial_display = ""
            if financial_info and financial_info.get('summary') and financial_info['summary'] != '财务信息待提取':
                financial_display = f'<div class="financial-info">{financial_info["summary"]}</div>'
            
            # 构建E值显示
            e_value_display = ""
            if financial_info.get('e_value') is not None:
                e_value_display = f'<div class="e-value-display">E值: {financial_info["e_value"]:.4f}</div>'
            
            # 读取SVG文件内容
            try:
                # 优先使用内存中的SVG内容
                if 'enhanced_content' in svg_file and svg_file['enhanced_content']:
                    svg_embed = svg_file['enhanced_content']
                # 如果没有内存内容，尝试从文件读取（向后兼容）
                elif svg_file.get('enhanced_file'):
                    with open(svg_file['enhanced_file'], 'r', encoding='utf-8') as f:
                        svg_content = f.read()
                        svg_embed = svg_content
                else:
                    # 如果都没有，使用默认的object标签
                    svg_embed = f'''<object data="unavailable.svg" type="image/svg+xml" width="100%" height="290">
                        <img src="unavailable.svg" alt="策略SVG" width="100%">
                    </object>'''
            except Exception as e:
                print(f"获取SVG内容失败: {e}")
                # 如果读取失败，使用原来的object标签作为后备
                svg_embed = f'''<object data="{os.path.basename(svg_file.get('enhanced_file', 'unavailable.svg'))}" type="image/svg+xml" width="100%" height="290">
                        <img src="{os.path.basename(svg_file.get('enhanced_file', 'unavailable.svg'))}" alt="策略SVG" width="100%">
                    </object>'''
            
            html_content += f'''
            <div class="{strategy_class}">
                {f'<div class="best-strategy-badge">🏆 推荐策略</div>' if is_best else ''}
                <div class="strategy-header">
                    <div class="strategy-title">策略图表 {svg_file['index']}</div>
                    <div class="strategy-desc">{matched_desc['strategy_name']} - {matched_desc['action_description']}</div>
                    {financial_display}
                    {e_value_display}
                </div>
                <div class="svg-container">
                    {svg_embed}
                </div>
            </div>'''
        
        html_content += f'''
        </div>
        
        <div class="descriptions-section">
            <h3>📋 精确策略描述详情</h3>
            <p>以下是基于DOM结构分析提取的精确策略描述（策略名称 + 具体动作格式）：</p>'''
        
        # 添加策略描述详情
        best_strategy_index = results.get('best_strategy', {}).get('index')
        
        for i, desc in enumerate(results['precise_descriptions']):
            financial_info = desc.get('financial_info', {})
            
            # 检查是否是推荐策略
            is_best = desc.get('index') == best_strategy_index
            desc_class = 'description-item best-strategy' if is_best else 'description-item'
            
            financial_text = ""
            if financial_info and financial_info.get('summary') and financial_info['summary'] != '财务信息待提取':
                financial_text = f'<div class="description-financial">{financial_info["summary"]}'
                if financial_info.get('e_value') is not None:
                    financial_text += f' | E值: {financial_info["e_value"]:.4f}'
                financial_text += '</div>'
            
            html_content += f'''
            <div class="{desc_class}">
                <div class="description-strategy">{desc['strategy_name']} {f'🏆 <span style="color: #f59e0b; font-weight: bold;">推荐策略</span>' if is_best else ''}</div>
                <div class="description-action">{desc['action_description']}</div>
                {financial_text}
            </div>'''
        
        html_content += f'''
        </div>
        
        <div class="header">
            <h3>🎉 优化改进说明（内嵌SVG版本）</h3>
            <p><strong>SVG内嵌:</strong> 所有SVG图表内容已直接嵌入HTML文件中，无需外部文件依赖</p>
            <p><strong>独立部署:</strong> 单个HTML文件包含所有内容，便于在Web项目TAB中展示</p>
            <p><strong>精确提取:</strong> 基于DOM结构分析，只提取"策略名称 + 具体动作"标准格式</p>
            <p><strong>布局优化:</strong> 调整标题位置，避免与图表内容重叠</p>
            <p style="margin-top: 20px; color: #6b7280;">生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    </div>
</body>
</html>'''
        
        # 保存HTML文件
        html_file = f"{output_dir}/embedded_svg_display_{results['strategy_code']}_{results['target_price']}.html"
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return html_file
    
    def close(self):
        """关闭Playwright浏览器"""
        try:
            if self.page:
                self.page.close()
            if self.context:
                self.context.close()
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
        except Exception as e:
            print(f"关闭浏览器时出现错误: {e}")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

def test_optimized_extractor():
    """测试优化的策略提取器"""
    print("🎯 优化策略提取器测试")
    print("="*60)
    
    # 测试用例
    strategy = "au2510"
    target_price = 770.0
    
    # 测试内存模式（不保存SVG文件）
    print("🪟 测试优化提取器（内存模式）")
    
    with OptimizedStrategyExtractor(headless=True, timeout=60) as extractor:
        results = extractor.extract_precise_strategy_descriptions(
            strategy, target_price, save_svg_files=False  # 不保存SVG文件
        )
        
        if results['success']:
            print(f"\n🎉 优化提取流程成功!")
            print(f"策略代码: {results['strategy_code']}")
            print(f"目标价格: {results['target_price']}")
            print(f"精确描述数量: {len(results['precise_descriptions'])}")
            print(f"图表数量: {len(results['svg_files_with_descriptions'])}")
            
            # 检查是否保存了SVG文件
            svg_files_saved = sum(1 for svg in results['svg_files_with_descriptions'] if svg.get('enhanced_file'))
            print(f"保存的SVG文件数: {svg_files_saved}")
            
            print(f"\n📋 精确描述概览:")
            for desc in results['precise_descriptions']:
                print(f"  • {desc['full_description']}")
            
            print(f"\n📄 生成文件:")
            print(f"  结果摘要: {results.get('summary_file', '未生成')}")
            print(f"  详细报告: {results.get('report_file', '未生成')}")
            print(f"  HTML展示: {results.get('html_file', '未生成')}")
            
            return results
            
        else:
            print(f"\n❌ 优化提取失败:")
            for error in results['errors']:
                print(f"  - {error}")
            return None

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # 检测运行环境
    if os.name == 'posix':  # Linux/Unix
        print("🐧 检测到Linux环境，使用headless模式")
    else:
        print("🪟 检测到Windows环境")
    
    test_optimized_extractor()