"""
数据工具模块
负责数据解析、转换和文件管理等通用功能
"""

import os
import re
from datetime import datetime
import pandas as pd

# 全局标志：用于控制因子统计表格只打印一次
_factor_summary_printed = False


def parse_stock_info_from_filename(filename):
    """
    从文件名解析股票信息
    输入: "000001.SZ-股票名称-日线后复权及常用指标-20250718.csv"
    输出: ("000001.SZ", "股票名称", "20250718")
    """
    pattern = r"([0-9]{6}\.[A-Z]{2})-(.+?)-日线后复权及常用指标-(\d{8})\.csv"
    match = re.match(pattern, filename)
    if match:
        return match.group(1), match.group(2), match.group(3)
    return None, None, None


def convert_stock_code(original_code):
    """
    转换股票代码格式
    SZ -> XSHE, SH -> XSHG, BJ -> BJSE
    """
    if original_code.endswith(".SZ"):
        return original_code.replace(".SZ", ".XSHE")
    elif original_code.endswith(".SH"):
        return original_code.replace(".SH", ".XSHG")
    elif original_code.endswith(".BJ"):
        return original_code.replace(".BJ", ".BJSE")
    else:
        return None  # 其他格式暂不处理


def get_stock_list_from_csv_folder(csv_folder_path, limit=None):
    """
    从CSV文件夹获取股票列表
    """
    stock_list = []

    for filename in os.listdir(csv_folder_path):
        if not filename.endswith('.csv'):
            continue
        original_code, stock_name, date = parse_stock_info_from_filename(filename)

        if original_code and stock_name:
            # 转换股票代码
            converted_code = convert_stock_code(original_code)

            if converted_code:  # 处理SZ、SH和BJ股票
                stock_list.append(
                    {
                        "original_code": original_code,
                        "converted_code": converted_code,
                        "stock_name": stock_name,
                        "date": date,
                    }
                )

    # 限制处理数量（用于测试）
    if limit:
        stock_list = stock_list[:limit]

    return stock_list


def get_failed_log_path():
    """
    获取失败日志文件路径
    
    Returns:
        str: 失败日志文件的完整路径
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    log_dir = os.path.join(current_dir, "log")
    today = datetime.now().strftime("%Y%m%d")
    return os.path.join(log_dir, f"failed_stocks_{today}.txt")


def get_failed_stocks():
    """
    获取需要重试的失败股票列表

    Returns:
        list: 失败股票信息列表
    """
    failed_log_file = get_failed_log_path()

    if os.path.exists(failed_log_file):
        try:
            failed_stocks = []
            with open(failed_log_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    # 新格式: stock_code|stock_name|error|timestamp
                    parts = line.split("|")
                    if len(parts) >= 2:
                        stock_code = parts[0]
                        stock_name = parts[1]
                        failed_stocks.append(
                            {
                                "converted_code": stock_code,
                                "stock_name": stock_name,
                            }
                        )

            if failed_stocks:
                from loguru import logger

                logger.info(f"从日志文件读取到 {len(failed_stocks)} 只失败股票")
                return failed_stocks
        except Exception as e:
            from loguru import logger

            logger.warning(f"读取失败日志文件出错: {e}")

    # 如果没有找到失败记录，返回空列表
    return []


def analyze_factor_summary(df):
    """
    智能分析 DataFrame 的因子分类
    
    根据列名自动识别因子类型，并返回分类统计
    
    Args:
        df: 因子数据 DataFrame
    
    Returns:
        dict: 因子分类字典
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError(f"参数必须是 pandas DataFrame，而不是 {type(df).__name__}")
    
    columns = df.columns.tolist()
    
    # 定义分类规则（基于列名模式）
    categories = {}
    
    # 1. 基础信息
    basic_info = []
    for col in ["交易日期", "股票代码", "股票简称"]:
        if col in columns:
            basic_info.append(col)
    if basic_info:
        categories["基础信息"] = basic_info
    
    # 2. 后复权技术因子
    adjusted_tech = [col for col in columns if col.endswith("_后复权")]
    if adjusted_tech:
        categories["后复权技术因子"] = adjusted_tech
    
    # 3. 衍生技术因子
    derived_tech = []
    derived_keywords = ["涨跌", "振幅", "成交额", "换手率", "流通股"]
    for col in columns:
        if any(keyword in col for keyword in derived_keywords):
            if col not in adjusted_tech:  # 避免重复
                derived_tech.append(col)
    if derived_tech:
        categories["衍生技术因子"] = derived_tech
    
    # 4. 未复权技术因子
    unadjusted_tech = [col for col in columns if col.endswith("_未复权")]
    if unadjusted_tech:
        categories["未复权技术因子"] = unadjusted_tech
    
    # 5. 资金流因子
    flow_factors = [col for col in columns if "主买" in col or "主卖" in col]
    if flow_factors:
        categories["资金流因子"] = flow_factors
    
    # 6. 基本面因子
    fundamental = []
    fundamental_keywords = [
        "市盈率", "市净率", "市销率", "股息率", "市值", "账面市值比",
        "息税前利润", "息税折旧摊销前利润", "每股息税前利润", "净资产收益率"
    ]
    for col in columns:
        if any(keyword in col for keyword in fundamental_keywords):
            fundamental.append(col)
    if fundamental:
        categories["基本面因子"] = fundamental
    
    # 7. 股东户数因子
    shareholder = [col for col in columns if "股东" in col or "户均" in col]
    if shareholder:
        categories["股东户数因子"] = shareholder
    
    return categories


def print_factor_summary_once(df):
    """
    打印因子分类统计表格（只打印一次）
    
    在批处理时，第一次调用会打印表格，后续调用会被忽略。
    根据实际的 DataFrame 自动分析因子分类。
    
    Args:
        df: 因子数据 DataFrame
    """
    global _factor_summary_printed
    
    # 如果已经打印过，直接返回
    if _factor_summary_printed:
        return
    
    # 自动分析因子分类
    categories = analyze_factor_summary(df)
    
    # 打印表格（使用更美观的格式）
    print()
    print("=" * 100)
    print("因子分类统计表")
    print("=" * 100)
    print()
    
    total_count = 0
    for category, fields in categories.items():
        count = len(fields)
        total_count += count
        
        # 打印类别和数量
        print(f"【{category}】 {count}个")
        print("-" * 100)
        
        # 打印因子列表（每行最多显示3个因子，避免过长）
        for i in range(0, len(fields), 3):
            line_factors = fields[i : i + 3]
            print(f"  {', '.join(line_factors)}")
        
        print()
    
    # 打印总计
    print("=" * 100)
    print(f"【总计】 {total_count}个因子")
    print("=" * 100)
    print()
    
    # 标记为已打印
    _factor_summary_printed = True


def reset_factor_summary_flag():
    """
    重置因子统计表格打印标志
    
    用于在新的批处理任务中重新打印表格
    """
    global _factor_summary_printed
    _factor_summary_printed = False


def categorize_error(error_message):
    """
    根据错误信息对错误进行分类
    
    Args:
        error_message: 错误信息字符串
    
    Returns:
        str: 错误类型
    """
    error_str = str(error_message)
    
    if "instruments()" in error_str and "未能找到股票" in error_str:
        return "米筐API的 `instruments()` 函数未能找到股票的基本信息"
    elif "get_capital_flow()" in error_str:
        return "米筐API的 get_capital_flow() 返回 None"
    elif "get_price()" in error_str and "后复权" in error_str:
        return "米筐API的 get_price() 返回空数据(后复权)"
    elif "get_price()" in error_str and "未复权" in error_str:
        return "米筐API的 get_price() 返回空数据(未复权)"
    elif "get_turnover_rate()" in error_str:
        return "米筐API的 get_turnover_rate() 返回 None"
    elif "get_shares()" in error_str:
        return "米筐API的 get_shares() 返回 None"
    elif "get_vwap()" in error_str:
        return "米筐API的 get_vwap() 返回 None"
    elif "get_factor()" in error_str:
        return "米筐API的 get_factor() 返回空数据"
    elif "get_holder_number()" in error_str:
        return "米筐API的 get_holder_number() 返回空数据"
    else:
        return "其他错误"


def get_exchange(stock_code):
    """
    根据股票代码判断交易所
    
    Args:
        stock_code: 股票代码
    
    Returns:
        str: 交易所名称
    """
    if stock_code.endswith('.XSHG'):
        return '上交所'
    elif stock_code.endswith('.XSHE'):
        return '深交所'
    elif stock_code.endswith('.BJSE'):
        return '北交所'
    else:
        return '未知'


def analyze_failures(failed_stocks_list, total_stocks=None):
    """
    分析失败股票列表，生成汇总报告
    
    Args:
        failed_stocks_list: 失败股票列表，每项包含 stock_code, stock_name, error
        total_stocks: 总股票数量（可选）
    
    Returns:
        str: 格式化的汇总报告文本
    """
    from collections import defaultdict
    
    if not failed_stocks_list:
        return "没有失败的股票"
    
    # 按错误类型分类
    error_categories = defaultdict(list)
    for stock in failed_stocks_list:
        error_type = categorize_error(stock['error'])
        error_categories[error_type].append(stock)
    
    # 按交易所分类
    exchange_stocks = defaultdict(list)
    for stock in failed_stocks_list:
        exchange = get_exchange(stock['stock_code'])
        exchange_stocks[exchange].append(stock)
    
    # 生成报告
    lines = []
    lines.append("=" * 100)
    lines.append("失败股票汇总报告")
    lines.append("=" * 100)
    lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 添加统计信息
    if total_stocks is not None:
        success_count = total_stocks - len(failed_stocks_list)
        failure_rate = len(failed_stocks_list) / total_stocks * 100 if total_stocks > 0 else 0
        lines.append(f"总股票数: {total_stocks} 只")
        lines.append(f"成功数量: {success_count} 只")
        lines.append(f"失败数量: {len(failed_stocks_list)} 只")
        lines.append(f"失败占比: {failure_rate:.2f}%")
    else:
        lines.append(f"失败总数: {len(failed_stocks_list)} 只")
    
    lines.append("")
    
    # 按错误类型统计
    lines.append("-" * 100)
    lines.append("【按错误类型分类】")
    lines.append("-" * 100)
    
    for error_type in sorted(error_categories.keys()):
        stocks = error_categories[error_type]
        lines.append(f"\n{error_type}: {len(stocks)} 只")
        
        # 统计交易所分布
        exchange_count = defaultdict(int)
        for stock in stocks:
            exchange = get_exchange(stock['stock_code'])
            exchange_count[exchange] += 1
        
        exchange_summary = ', '.join([f"{ex}: {cnt}只" for ex, cnt in sorted(exchange_count.items())])
        lines.append(f"  交易所分布: {exchange_summary}")
        
        # 列出前5只股票
        examples = ', '.join([f"{s['stock_code']}({s['stock_name']})" for s in stocks[:5]])
        lines.append(f"  示例: {examples}")
        if len(stocks) > 5:
            lines.append(f"  ... 还有 {len(stocks) - 5} 只")
    
    # 按交易所统计
    lines.append("")
    lines.append("-" * 100)
    lines.append("【按交易所分类】")
    lines.append("-" * 100)
    
    for exchange in ['上交所', '深交所', '北交所', '未知']:
        if exchange in exchange_stocks:
            stocks = exchange_stocks[exchange]
            lines.append(f"\n{exchange}: {len(stocks)} 只")
            
            # 统计错误类型分布
            error_dist = defaultdict(int)
            for stock in stocks:
                error_type = categorize_error(stock['error'])
                error_dist[error_type] += 1
            
            for error_type, count in sorted(error_dist.items(), key=lambda x: -x[1]):
                lines.append(f"  - {error_type}: {count}只")
    
    lines.append("")
    lines.append("=" * 100)
    
    return "\n".join(lines)


def write_failure_logs(failed_stocks_list, log_dir, total_stocks=None):
    """
    写入失败汇总报告
    
    Args:
        failed_stocks_list: 失败股票列表
        log_dir: 日志目录路径
        total_stocks: 总股票数量（可选）
    
    Returns:
        str: 汇总报告路径
    """
    os.makedirs(log_dir, exist_ok=True)
    
    today = datetime.now().strftime("%Y%m%d")
    
    # 生成并写入汇总报告
    summary_report = analyze_failures(failed_stocks_list, total_stocks)
    summary_file = os.path.join(log_dir, f"failed_summary_{today}.txt")
    with open(summary_file, "w", encoding="utf-8") as f:
        f.write(summary_report)
    
    # 打印到控制台
    print("\n" + summary_report)
    
    return summary_file
