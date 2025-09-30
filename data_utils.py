"""
数据工具模块
负责数据解析、转换和文件管理等通用功能
"""

import os
import re
from pathlib import Path
from datetime import datetime


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
    csv_folder = Path(csv_folder_path)
    stock_list = []

    for csv_file in csv_folder.glob("*.csv"):
        original_code, stock_name, date = parse_stock_info_from_filename(csv_file.name)

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
        Path: 失败日志文件的完整路径
    """
    log_dir = Path(__file__).parent / "log"
    today = datetime.now().strftime("%Y%m%d")
    return log_dir / f"failed_stocks_{today}.txt"


def get_failed_stocks():
    """
    获取需要重试的失败股票列表
    从TXT日志读取失败股票

    Returns:
        list: 失败股票信息列表
    """
    failed_log_file = get_failed_log_path()

    if failed_log_file.exists():
        try:
            failed_stocks = []
            with open(failed_log_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue

                    # 解析格式：股票代码|股票名称|错误类型|错误信息|时间戳
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
