#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试内存优化的SVG处理功能
"""

import json
import os
import time
import sys
import shutil

# Fix Windows console encoding
if sys.platform == "win32":
    try:
        import codecs
        if hasattr(sys.stdout, 'buffer'):
            sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer)
            sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer)
    except:
        pass

def test_memory_optimized_svg():
    """测试内存优化的SVG处理"""
    from optimized_strategy_extractor import OptimizedStrategyExtractor
    
    print("🚀 开始测试内存优化的SVG处理")
    print("="*60)
    
    # 测试用例
    strategy = "LC2511"
    target_price = 100000.0
    
    # 创建测试输出目录
    test_output_dir = "test_memory_optimized"
    os.makedirs(test_output_dir, exist_ok=True)
    
    try:
        # 使用headless模式进行测试
        print("🔧 初始化优化提取器（内存模式）")
        
        with OptimizedStrategyExtractor(headless=True, timeout=60) as extractor:
            # 记录开始时间
            start_time = time.time()
            
            results = extractor.extract_precise_strategy_descriptions(
                strategy, target_price, output_dir=test_output_dir
            )
            
            # 记录结束时间
            end_time = time.time()
            
            if results['success']:
                print(f"\n✅ 内存优化提取成功!")
                print(f"⏱️  处理时间: {end_time - start_time:.2f} 秒")
                print(f"策略代码: {results['strategy_code']}")
                print(f"目标价格: {results['target_price']}")
                print(f"精确描述数量: {len(results['precise_descriptions'])}")
                print(f"图表数量: {len(results['svg_files_with_descriptions'])}")
                
                # 检查SVG内容是否在内存中
                memory_svgs = 0
                file_svgs = 0
                for svg_file in results['svg_files_with_descriptions']:
                    if 'enhanced_content' in svg_file and svg_file['enhanced_content']:
                        memory_svgs += 1
                    if svg_file.get('enhanced_file'):
                        file_svgs += 1
                
                print(f"\n📊 SVG存储统计:")
                print(f"  内存中的SVG: {memory_svgs}")
                print(f"  保存为文件的SVG: {file_svgs}")
                
                # 检查生成的HTML文件
                if 'html_file' in results:
                    html_path = results['html_file']
                    if os.path.exists(html_path):
                        html_size = os.path.getsize(html_path)
                        print(f"\n📄 HTML文件:")
                        print(f"  路径: {html_path}")
                        print(f"  大小: {html_size:,} 字节")
                        
                        # 验证HTML中包含SVG内容
                        with open(html_path, 'r', encoding='utf-8') as f:
                            html_content = f.read()
                            svg_count = html_content.count('<svg')
                            print(f"  内嵌SVG数量: {svg_count}")
                
                # 列出生成的所有文件
                print(f"\n📁 输出目录内容:")
                for file in os.listdir(test_output_dir):
                    file_path = os.path.join(test_output_dir, file)
                    if os.path.isfile(file_path):
                        file_size = os.path.getsize(file_path)
                        print(f"  - {file} ({file_size:,} 字节)")
                
                return results
                
            else:
                print(f"\n❌ 内存优化提取失败:")
                for error in results['errors']:
                    print(f"  - {error}")
                return None
                
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        return None
    
    finally:
        # 清理测试目录（可选）
        cleanup = False  # 设置为True以自动清理
        if cleanup and os.path.exists(test_output_dir):
            print(f"\n🧹 清理测试目录: {test_output_dir}")
            shutil.rmtree(test_output_dir)


def compare_with_original():
    """比较内存优化版本与原始版本的差异"""
    print("\n" + "="*60)
    print("📊 比较内存优化版本与原始版本")
    print("="*60)
    
    # 检查是否存在原始版本的结果
    original_result = "optimized_results/optimized_results_IM2509_8000.0.json"
    if os.path.exists(original_result):
        with open(original_result, 'r', encoding='utf-8') as f:
            original_data = json.load(f)
        
        print("原始版本统计:")
        print(f"  - SVG文件数量: {len([f for f in original_data['svg_files_with_descriptions'] if f.get('enhanced_file')])}")
        
        # 计算原始SVG文件的总大小
        total_svg_size = 0
        for svg_file in original_data['svg_files_with_descriptions']:
            if svg_file.get('enhanced_file') and os.path.exists(svg_file['enhanced_file']):
                total_svg_size += os.path.getsize(svg_file['enhanced_file'])
        
        print(f"  - SVG文件总大小: {total_svg_size:,} 字节")
        
        # 检查原始HTML文件
        original_html = "optimized_results/optimized_display_IM2509_8000.0.html"
        if os.path.exists(original_html):
            original_html_size = os.path.getsize(original_html)
            print(f"  - HTML文件大小: {original_html_size:,} 字节")
    else:
        print("未找到原始版本的结果文件")


if __name__ == "__main__":
    # 运行测试
    results = test_memory_optimized_svg()
    
    # 比较版本差异
    compare_with_original()
    
    print("\n🎉 测试完成!")