import re


# 期货合约代码到名称的映射表
FUTURES_NAME_MAPPING = {
    "A": "黄大豆1号",        "AD": "铝合金",        "AG": "白银",        "AL": "铝",
    "AO": "氧化铝",        "AP": "苹果",        "AU": "黄金",        "B": "黄大豆2号",
    "BB": "胶板",        "BC": "国际铜",        "BR": "顺丁橡胶",        "BU": "沥青",
    "BZ": "纯苯",        "C": "玉米",        "CF": "棉花",        "CJ": "红枣",
    "CS": "淀粉",        "CU": "铜",        "CY": "棉纱",        "EB": "苯乙烯",
    "EC": "欧线集运",        "EG": "乙二醇",        "FB": "纤板",        "FG": "玻璃",
    "FU": "燃料油",        "HC": "热轧卷板",        "I": "铁矿石",        "IC": "中证500股指",
    "IF": "沪深300股指",        "IH": "上证50股指",        "IM": "中证1000股指",        "J": "焦炭",
    "JD": "鸡蛋",        "JM": "焦煤",        "JR": "粳稻",        "L": "聚乙烯LLDPE",
    "LC": "碳酸锂",        "LG": "原木",        "LH": "生猪",        "LR": "晚稻",
    "LU": "低硫燃料油",        "M": "豆粕",        "MA": "甲醇",        "NI": "镍",
    "NR": "20号胶",        "OI": "菜籽油",        "P": "棕榈油",        "PB": "铅",
    "PF": "短纤",        "PG": "液化石油气",        "PK": "花生仁",        "PL": "丙烯",
    "PM": "普麦",        "PP": "聚丙烯",        "PR": "瓶片",        "PS": "多晶硅",
    "PX": "对二甲苯",        "RB": "螺纹钢",        "RI": "早稻",        "RM": "菜籽粕",
    "RR": "粳米",        "RS": "菜籽",        "RU": "橡胶",        "SA": "纯碱",
    "SC": "原油",        "SF": "硅铁",        "SH": "烧碱",        "SI": "工业硅",
    "SM": "锰硅",        "SN": "锡",        "SP": "针叶木浆",        "SR": "白糖",
    "SS": "不锈钢",        "T": "10年期国债",        "TA": "精对苯二甲酸PTA",        "TF": "5年期国债",
    "TL": "30年期国债",        "TS": "2年期国债",        "UR": "尿素",        "V": "聚氯乙稀PVC",
    "WH": "强麦",        "WR": "线材",        "Y": "豆油",        "ZC": "动力煤",
    "ZN": "锌",
}

# 建立反向映射：名称到合约代码
FUTURES_CODE_MAPPING = {v: k for k, v in FUTURES_NAME_MAPPING.items()}


def get_futures_product(symbol: str) -> dict:
    # 提取品种代码
    underlying = symbol.upper()
    if underlying.endswith("99"):
        underlying = underlying[:-2]
    elif re.match(r"^[A-Z]{1,4}\d{3,4}$", underlying):
        m = re.match(r"^([A-Z]{1,4})\d{3,4}$", underlying)
        if m:
            underlying = m.group(1)
    return underlying


def get_futures_name(symbol: str) -> str:
    """
    获取期货合约的中文名称
    根据品种代码返回对应的中文名称
    """
    underlying = get_futures_product(symbol)  # 确保提取品种代码
    return FUTURES_NAME_MAPPING.get(underlying, f"期货{underlying}")


def get_futures_code(name: str) -> str:
    """
    根据期货名称获取合约代码
    
    Args:
        name: 期货名称
        
    Returns:
        str: 合约代码，未找到返回空字符串
    """
    return FUTURES_CODE_MAPPING.get(name, "")
