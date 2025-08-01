import re
def get_futures_product(symbol: str) -> dict:
    # 提取品种代码
    underlying = symbol.upper()
    if underlying.endswith('99'):
        underlying = underlying[:-2]
    elif re.match(r'^[A-Z]{1,4}\d{3,4}$', underlying):
        m = re.match(r'^([A-Z]{1,4})\d{3,4}$', underlying)
        if m:
            underlying = m.group(1)
    return underlying

def get_futures_name(symbol: str) -> str:
    """
    获取期货合约的中文名称
    根据品种代码返回对应的中文名称
    """    

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
        'SI': '工业硅', 'LC': '碳酸锂', 'LH': '生猪'
    }
    
    underlying = get_futures_product(symbol)  # 确保提取品种代码
    
    return name_mapping.get(underlying, f'期货{underlying}')