"""
因子计算模块
负责股票数据获取和因子计算的核心逻辑
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径（用于导入factor_utils）
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from factor_utils import *
from config import get_config


def get_stock_data(stock_symbol, start_date, end_date):
    """
    获取股票的所有原始数据
    """
    # 技术因子数据
    tech_list = ["open", "high", "low", "close", "volume", "total_turnover"]
    # adjust_type="post_volume"这里的成交量是后复权因子调整后的成交量
    daily_tech = get_price(
        stock_symbol,
        start_date,
        end_date,
        fields=tech_list,
        adjust_type="post_volume",
        skip_suspended=False,
    ).sort_index()

    # 换手率数据
    daily_tech["turnover_rate"] = get_turnover_rate(
        stock_symbol, start_date, end_date
    ).today

    # 未复权成交量
    daily_tech["unadjusted_volume"] = (
        get_price(
            stock_symbol,
            start_date,
            end_date,
            fields="volume",
            adjust_type="none",
            skip_suspended=False,
        )
        .sort_index()
        .volume
    )

    # 自由流通股本
    vol_start_date = (
        daily_tech["unadjusted_volume"].index.get_level_values("date").min()
    )
    daily_tech["stock_free_circulation"] = get_shares(
        stock_symbol, vol_start_date, end_date
    ).free_circulation

    # 获取日度资金流入和流出
    capital_flow = get_capital_flow(stock_symbol, start_date, end_date)
    daily_tech["capital_inflow"] = capital_flow.buy_value
    daily_tech["capital_outflow"] = capital_flow.sell_value

    return daily_tech


def generate_factors_for_stock(stock_symbol, end_date):
    """
    为单只股票生成所有因子数据
    """
    try:
        # 获取配置信息
        config = get_config()
        fundamental_factors = config["fundamental_factors"]
        factor_name_mapping = config["factor_name_mapping"]
        decimal_places = config["decimal_places"]
        column_order = config["column_order"]

        # 获取股票基本信息
        start_date = instruments(stock_symbol).listed_date
        stock_name = instruments(stock_symbol).symbol

        # 获取所有原始数据
        daily_tech = get_stock_data(stock_symbol, start_date, end_date)

        # 计算前一日收盘价
        daily_tech["prev_close"] = daily_tech["close"].shift(1)

        # 计算涨跌额
        daily_tech["change_amount"] = daily_tech["close"] - daily_tech["prev_close"]

        # 计算涨跌幅
        daily_tech["change_pct"] = (
            daily_tech["close"] - daily_tech["prev_close"]
        ) / daily_tech["prev_close"]

        # 计算振幅
        daily_tech["amplitude"] = (daily_tech["high"] - daily_tech["low"]) / daily_tech[
            "prev_close"
        ]

        # 计算自由流通股本换手率
        daily_tech["free_turnover"] = (
            daily_tech["unadjusted_volume"] / daily_tech["stock_free_circulation"]
        ) * 100

        # 计算vwap
        daily_tech["vwap"] = daily_tech["total_turnover"] / daily_tech["volume"]

        # 获取基本面因子（使用配置文件中的因子列表）
        daily_fund = get_factor(stock_symbol, fundamental_factors, start_date, end_date)

        # 合并技术因子和基本面因子
        daily_factors = daily_tech.join(daily_fund, how="outer")

        # 添加股票名称列
        daily_factors["stock_name"] = stock_name

        # 调整列顺序：交易日期、股票代码在前，然后是各种因子
        # 首先重置索引为列
        daily_factors = daily_factors.reset_index()

        # 使用配置文件中的列顺序
        daily_factors = daily_factors[column_order]

        # 将列名从英文转换为中文
        daily_factors = daily_factors.rename(columns=factor_name_mapping)

        # 保留指定位数的小数
        daily_factors = daily_factors.round(decimal_places)

        # 将交易日期格式改为YYYYMMDD格式（不带斜杠）
        daily_factors["交易日期"] = daily_factors["交易日期"].dt.strftime("%Y%m%d")

        # 删除第一行数据（因为prev_close计算导致第一行为NaN）
        daily_factors = daily_factors.iloc[1:]

        # 过滤掉停牌的股票
        daily_factors_filtered = daily_factors[daily_factors["换手率(%)"] > 0]

        # 返回过滤后的DataFrame（移除了换手率为0的行）
        return daily_factors_filtered

    except Exception as e:
        from loguru import logger

        # 记录到日志
        error_msg = f"{type(e).__name__} - {str(e)}"
        logger.error(f"处理股票 {stock_symbol} 时出错: {error_msg}")

        # 返回None，让上层决定是否记录到文件
        return None
