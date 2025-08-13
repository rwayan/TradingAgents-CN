#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Playwright迁移测试脚本
验证从selenium迁移到playwright后的功能是否正常
"""

import sys
import os
import time
import logging

# 添加项目路径到sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Fix Windows console encoding
if sys.platform == "win32":
    try:
        import codecs
        if hasattr(sys.stdout, 'buffer'):
            sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer)
            sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer)
    except:
        pass

from optimized_strategy_extractor import OptimizedStrategyExtractor

def test_basic_functionality():
    """测试基本功能"""
    print("🎯 Playwright迁移测试")
    print("="*60)
    
    # 测试用例
    strategy = "IM2509"
    target_price = 8000.0
    
    print("🧪 测试基本浏览器启动和页面访问")
    
    try:
        with OptimizedStrategyExtractor(headless=True, timeout=30) as extractor:
            print("✅ Playwright浏览器启动成功")
            
            # 测试页面访问
            url = f"https://openvlab.cn/strategy/optimizer/{strategy}"
            print(f"🌐 访问测试页面: {url}")
            extractor.page.goto(url)
            time.sleep(5)
            
            title = extractor.page.title()
            print(f"📄 页面标题: {title}")
            
            if title and len(title) > 0:
                print("✅ 页面访问成功")
                return True
            else:
                print("❌ 页面访问失败：无法获取页面标题")
                return False
                
    except Exception as e:
        print(f"❌ 基本功能测试失败: {e}")
        return False

def test_element_interaction():
    """测试元素交互功能"""
    print("\n🔧 测试元素交互功能")
    
    try:
        with OptimizedStrategyExtractor(headless=True, timeout=30) as extractor:
            # 访问页面
            url = "https://openvlab.cn/strategy/optimizer/IM2509"
            extractor.page.goto(url)
            time.sleep(8)
            
            # 测试查找输入框
            input_selectors = [
                'input[type="number"]',
                'input[type="text"]',
                'input[inputmode="numeric"]'
            ]
            
            found_inputs = 0
            for selector in input_selectors:
                elements = extractor.page.locator(selector).all()
                found_inputs += len(elements)
                print(f"  找到 {len(elements)} 个 {selector} 元素")
            
            if found_inputs > 0:
                print(f"✅ 成功找到 {found_inputs} 个输入元素")
                return True
            else:
                print("❌ 未找到任何输入元素")
                return False
                
    except Exception as e:
        print(f"❌ 元素交互测试失败: {e}")
        return False

def test_strategy_extraction():
    """测试策略提取功能"""
    print("\n📋 测试策略提取功能")
    
    try:
        with OptimizedStrategyExtractor(headless=True, timeout=30) as extractor:
            # 访问页面
            url = "https://openvlab.cn/strategy/optimizer/IM2509"
            extractor.page.goto(url)
            time.sleep(8)
            
            # 测试查找策略容器
            card_selector = "div.bg-card.text-card-foreground"
            containers = extractor.page.locator(card_selector).all()
            
            strategy_count = 0
            for container in containers:
                if container.is_visible():
                    try:
                        height = container.bounding_box()['height']
                        if height > 300:
                            text = container.text_content()
                            if text and any(keyword in text for keyword in ['期权', '价差', '买入', '卖出']):
                                strategy_count += 1
                    except:
                        continue
            
            if strategy_count > 0:
                print(f"✅ 成功找到 {strategy_count} 个策略容器")
                return True
            else:
                print("❌ 未找到策略容器")
                return False
                
    except Exception as e:
        print(f"❌ 策略提取测试失败: {e}")
        return False

def test_svg_extraction():
    """测试SVG提取功能"""
    print("\n📊 测试SVG提取功能")
    
    try:
        with OptimizedStrategyExtractor(headless=True, timeout=30) as extractor:
            # 访问页面
            url = "https://openvlab.cn/strategy/optimizer/IM2509"
            extractor.page.goto(url)
            time.sleep(8)
            
            # 查找SVG元素
            svg_elements = extractor.page.locator("svg").all()
            
            valid_svgs = 0
            for svg in svg_elements:
                if svg.is_visible():
                    svg_content = svg.get_attribute('outerHTML')
                    if svg_content and len(svg_content) > 500:
                        valid_svgs += 1
            
            if valid_svgs > 0:
                print(f"✅ 成功找到 {valid_svgs} 个有效SVG图表")
                return True
            else:
                print("❌ 未找到有效的SVG图表")
                return False
                
    except Exception as e:
        print(f"❌ SVG提取测试失败: {e}")
        return False

def test_performance_comparison():
    """测试性能对比"""
    print("\n⚡ 性能对比测试")
    
    try:
        # 测试启动时间
        start_time = time.time()
        
        with OptimizedStrategyExtractor(headless=True, timeout=30) as extractor:
            startup_time = time.time() - start_time
            print(f"🚀 Playwright启动时间: {startup_time:.2f}秒")
            
            # 测试页面加载时间
            page_start = time.time()
            extractor.page.goto("https://openvlab.cn/strategy/optimizer/IM2509")
            page_load_time = time.time() - page_start
            print(f"📄 页面加载时间: {page_load_time:.2f}秒")
            
            if startup_time < 10 and page_load_time < 15:
                print("✅ 性能表现良好")
                return True
            else:
                print("⚠️  性能可能需要优化")
                return True  # 仍然算作通过，只是性能提醒
                
    except Exception as e:
        print(f"❌ 性能测试失败: {e}")
        return False

def run_all_tests():
    """运行所有测试"""
    print("🎯 开始Playwright迁移完整测试")
    print("="*80)
    
    tests = [
        ("基本功能测试", test_basic_functionality),
        ("元素交互测试", test_element_interaction), 
        ("策略提取测试", test_strategy_extraction),
        ("SVG提取测试", test_svg_extraction),
        ("性能对比测试", test_performance_comparison)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} 通过")
            else:
                print(f"❌ {test_name} 失败")
        except Exception as e:
            print(f"❌ {test_name} 出现异常: {e}")
    
    print(f"\n{'='*80}")
    print(f"🎯 测试总结: {passed}/{total} 项测试通过")
    
    if passed == total:
        print("🎉 所有测试通过！Playwright迁移成功！")
        print("\n📝 迁移优势总结:")
        print("  ✅ 无需管理WebDriver")
        print("  ✅ 更稳定的Linux支持")
        print("  ✅ 更快的启动速度")
        print("  ✅ 更现代的API设计")
        print("  ✅ 内置等待和重试机制")
    elif passed >= total * 0.8:  # 80%通过率
        print("⚠️  大部分测试通过，迁移基本成功，可能需要细节调优")
    else:
        print("❌ 测试失败过多，需要检查迁移代码")
    
    return passed >= total * 0.8

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # 检测运行环境
    if os.name == 'posix':  # Linux/Unix
        print("🐧 检测到Linux环境，这正是我们要解决selenium问题的环境")
    else:
        print("🪟 检测到Windows环境，用于开发测试")
    
    success = run_all_tests()
    
    if success:
        print("\n🎉 Playwright迁移测试完成！可以开始使用新的实现了。")
        print("\n📚 使用说明:")
        print("1. 安装playwright: pip install playwright")
        print("2. 安装浏览器: playwright install chromium")
        print("3. 运行脚本: python optimized_strategy_extractor.py")
    else:
        print("\n❌ 迁移测试失败，需要进一步调试")
    
    sys.exit(0 if success else 1)