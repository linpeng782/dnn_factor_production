"""
因子计算模块
负责股票数据获取和因子计算的核心逻辑
"""

import sys
import os
from datetime import datetime
from loguru import logger
import pandas as pd

pd.set_option("display.max_columns", 10)
pd.set_option("display.width", 200)


# 导入米筐API
from rq_api import *
from config import get_config
from data_utils import print_factor_summary_once


def _merge_daily_and_quarterly_factors(daily_factors, quarterly_factors):
    """
    合并日度因子和季度因子数据

    对于季度数据，使用 merge_asof 进行向前填充，确保每个交易日都能获取到
    最新的（但不是未来的）季度数据。

    Args:
        daily_factors: 日度因子DataFrame，索引为 (order_book_id, date)
        quarterly_factors: 季度因子DataFrame，索引为 (order_book_id, date)

    Returns:
        pd.DataFrame: 合并后的DataFrame，索引为 (order_book_id, date)
    """
    # 重置索引，将索引转换为列
    daily_reset = daily_factors.reset_index()
    quarterly_reset = quarterly_factors.reset_index()

    # 确保日期列是datetime类型并排序
    daily_reset["date"] = pd.to_datetime(daily_reset["date"])
    quarterly_reset["date"] = pd.to_datetime(quarterly_reset["date"])
    daily_reset = daily_reset.sort_values("date")
    quarterly_reset = quarterly_reset.sort_values("date")

    # 使用 merge_asof 进行向前填充合并
    # direction='backward' 表示：对于每个交易日，使用最近的、不晚于该日期的季度数据
    merged = pd.merge_asof(
        daily_reset,
        quarterly_reset,
        on="date",
        by="order_book_id",
        direction="backward",
    )

    # 恢复索引
    merged = merged.set_index(["order_book_id", "date"]).drop(columns="end_date")
    return merged


def generate_factors_for_stock(stock_symbol, dataset_end_date):
    """
    为单只股票生成所有因子数据
    """
    try:
        # 获取配置信息
        config = get_config()
        fundamental_factors = config["fundamental_factors"]
        technical_factors = config["technical_factors"]
        flow_factors = config["flow_factors"]
        factor_name_mapping = config["factor_name_mapping"]
        column_order = config["column_order"]
        decimal_places = 4

        # 获取股票基本信息
        stock_instrument = instruments(stock_symbol)
        if stock_instrument is None:
            error_msg = (
                f"米筐API的 `instruments()` 函数未能找到股票 {stock_symbol} 的基本信息"
            )
            logger.warning(error_msg)
            return None, error_msg
        stock_listed_date = stock_instrument.listed_date
        stock_name = stock_instrument.symbol

        # 获取所有后复权技术因子数据
        daily_tech_adjusted = get_technical_factor_adjusted(
            stock_symbol, technical_factors, stock_listed_date, dataset_end_date
        )

        # 获取所有未复权技术因子数据
        daily_tech_unadjusted = get_technical_factor_unadjusted(
            stock_symbol, technical_factors, stock_listed_date, dataset_end_date
        )

        # 获取所有资金流因子数据
        daily_flow = get_flow_factor(
            stock_symbol, flow_factors, stock_listed_date, dataset_end_date
        )

        # 获取基本面因子（使用配置文件中的因子列表），get_factor是米筐的函数
        daily_fundamental = get_factor(
            stock_symbol, fundamental_factors, stock_listed_date, dataset_end_date
        )
        if daily_fundamental is None or daily_fundamental.empty:
            raise ValueError(
                f"米筐API的 get_factor() 返回空数据。"
                f"股票: {stock_symbol}, 日期范围: {stock_listed_date} 至 {dataset_end_date}。"
                f"可能原因: 该股票没有基本面数据。"
            )

        # 获取股东户数因子（季度数据）
        daily_shareholder = get_shareholder_factor(
            stock_symbol, stock_listed_date, dataset_end_date
        )

        # 将日度因子DataFrame放入列表（不包括季度数据）
        factor_dataframes = [
            daily_tech_adjusted,
            daily_tech_unadjusted,
            daily_flow,
            daily_fundamental,
        ]

        # 使用 pd.concat 沿列方向合并所有日度因子DataFrame
        daily_factors = pd.concat(factor_dataframes, axis=1, join="outer")

        # 对于季度数据（股东户数），使用专门的合并函数进行向前填充合并
        daily_factors = _merge_daily_and_quarterly_factors(
            daily_factors, daily_shareholder
        )

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
        # daily_factors = daily_factors.iloc[1:]

        # 过滤掉停牌的股票
        daily_factors_filtered = daily_factors[daily_factors["换手率(%)"] > 0]

        # 打印因子统计表格（只在第一次调用时打印，传入实际的 DataFrame）
        print_factor_summary_once(daily_factors_filtered)

        # 返回过滤后的DataFrame（移除了换手率为0的行）
        return daily_factors_filtered, None

    except Exception as e:
        error_msg = f"{type(e).__name__} - {str(e)}".replace("\n", " ")
        logger.error(f"处理股票 {stock_symbol} 时出错: {error_msg}")
        return None, error_msg


def get_technical_factor_adjusted(
    stock_symbol, technical_factors, start_date, end_date
):
    """
    获取股票的所有原始数据
    """
    # 后复权技术因子数据,获取open,high,low,close,volume,total_turnover
    # adjust_type="post_volume"这里的成交量是后复权因子调整后的成交量
    daily_tech = get_price(
        stock_symbol,
        start_date,
        end_date,
        fields=technical_factors,
        adjust_type="post_volume",
        skip_suspended=False,
    )

    # 检查 API 返回结果
    if daily_tech is None or daily_tech.empty:
        raise ValueError(
            f"米筐API的 get_price() 返回空数据（后复权）。"
            f"股票: {stock_symbol}, 日期范围: {start_date} 至 {end_date}。"
            f"可能原因: 该股票在此期间没有交易数据，或已退市。"
        )

    daily_tech = daily_tech.sort_index()

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

    # 计算vwap
    daily_tech["vwap_adjusted"] = daily_tech["total_turnover"] / daily_tech["volume"]

    # 换手率数据
    turnover_data = get_turnover_rate(stock_symbol, start_date, end_date)
    if turnover_data is None:
        raise ValueError(
            f"米筐API的 get_turnover_rate() 返回 None。"
            f"股票: {stock_symbol}, 日期范围: {start_date} 至 {end_date}。"
            f"可能原因: 该股票没有换手率数据。"
        )
    daily_tech["turnover_rate"] = turnover_data.today

    # 1. 定义旧名称到新名称的映射
    rename_map = {
        "open": "open_adjusted",
        "high": "high_adjusted",
        "low": "low_adjusted",
        "close": "close_adjusted",
        "prev_close": "prev_close_adjusted",
        "volume": "volume_adjusted",
    }

    # 2. 执行重命名
    daily_tech = daily_tech.rename(columns=rename_map)

    return daily_tech


def get_technical_factor_unadjusted(
    stock_symbol, technical_factors, start_date, end_date
):
    """
    获取股票的未复权技术因子

    Args:
        stock_symbol: 股票代码
        technical_factors: 技术因子列表
        start_date: 开始日期
        end_date: 结束日期

    Returns:
        pd.DataFrame: 未复权技术因子数据
    """
    # 创建副本，避免修改原始列表
    technical_factors_copy = [f for f in technical_factors if f != "total_turnover"]

    # 未复权技术因子数据,获取open,high,low,close,volume
    daily_tech = get_price(
        stock_symbol,
        start_date,
        end_date,
        fields=technical_factors_copy,
        adjust_type="none",
        skip_suspended=False,
    )

    # 检查 API 返回结果
    if daily_tech is None or daily_tech.empty:
        raise ValueError(
            f"米筐API的 get_price() 返回空数据（未复权）。"
            f"股票: {stock_symbol}, 日期范围: {start_date} 至 {end_date}。"
            f"可能原因: 该股票在此期间没有交易数据，或已退市。"
        )

    daily_tech = daily_tech.sort_index()

    # 自由流通股本
    vol_start_date = daily_tech["volume"].index.get_level_values("date").min()
    shares_data = get_shares(stock_symbol, vol_start_date, end_date)
    if shares_data is None:
        raise ValueError(
            f"米筐API的 get_shares() 返回 None。"
            f"股票: {stock_symbol}, 日期范围: {vol_start_date} 至 {end_date}。"
            f"可能原因: 该股票没有股本数据。"
        )
    daily_tech["stock_free_circulation"] = shares_data.free_circulation

    # 计算自由流通股本换手率
    daily_tech["free_turnover"] = (
        daily_tech["volume"] / daily_tech["stock_free_circulation"]
    ) * 100

    # 计算vwap
    vwap_data = get_vwap(stock_symbol, start_date, end_date)
    if vwap_data is None:
        raise ValueError(
            f"米筐API的 get_vwap() 返回 None。"
            f"股票: {stock_symbol}, 日期范围: {start_date} 至 {end_date}。"
            f"可能原因: 该股票没有VWAP数据。"
        )
    daily_tech["vwap_unadjusted"] = vwap_data

    # 1. 定义旧名称到新名称的映射
    rename_map = {
        "open": "open_unadjusted",
        "high": "high_unadjusted",
        "low": "low_unadjusted",
        "close": "close_unadjusted",
        "volume": "volume_unadjusted",
    }

    # 2. 执行重命名
    daily_tech = daily_tech.rename(columns=rename_map)

    return daily_tech


def get_flow_factor(stock_symbol, flow_factors, start_date, end_date):
    """
    获取股票的资金流入和流出
    """
    capital_flow = get_capital_flow(stock_symbol, start_date, end_date)

    # 检查 API 返回结果
    if capital_flow is None:
        raise ValueError(
            f"米筐API的 get_capital_flow() 返回 None。"
            f"股票: {stock_symbol}, 日期范围: {start_date} 至 {end_date}。"
            f"可能原因: 该股票在此期间没有资金流数据，或API调用失败。"
        )

    capital_flow = capital_flow.loc[:, flow_factors]
    return capital_flow

def get_shareholder_factor(stock_symbol, start_date, end_date):
    """
    获取股票的股东户数因子

    注意：
    - 原始数据是2层索引 (order_book_id, end_date)
    - 我们使用 info_date（发布日期）作为时间索引，因为这是数据真正可用的时间点
    - 如果同一天发布了多个报告期的数据，我们保留 end_date 最大的那条（最新报告期）
    """
    shareholder_factor = get_holder_number(stock_symbol, start_date, end_date)

    # 检查 API 返回结果
    if shareholder_factor is None or shareholder_factor.empty:
        raise ValueError(
            f"米筐API的 get_holder_number() 返回空数据。"
            f"股票: {stock_symbol}, 日期范围: {start_date} 至 {end_date}。"
            f"可能原因: 该股票没有股东户数数据。"
        )

    # 重置索引，将所有索引层级转换为列
    shareholder_factor = shareholder_factor.reset_index()

    # 处理同一天发布多个报告期数据的情况
    # 对于同一个 (order_book_id, info_date)，保留 end_date 最大的那条记录
    shareholder_factor = shareholder_factor.sort_values("end_date", ascending=False)
    shareholder_factor = shareholder_factor.drop_duplicates(
        subset=["order_book_id", "info_date"], keep="first"
    )

    # 使用 info_date（发布日期）作为时间索引，并重命名为 date
    shareholder_factor = shareholder_factor.rename(columns={"info_date": "date"})

    # 按照 date 升序排序，这对于后续的 merge_asof 操作是必需的
    shareholder_factor = shareholder_factor.sort_values(["order_book_id", "date"])

    # 重新设置索引为 (order_book_id, date)
    shareholder_factor = shareholder_factor.set_index(["order_book_id", "date"])

    # end_date 作为普通列保留，它表示数据所属的报告期
    # 这个信息在某些分析中可能有用

    return shareholder_factor
