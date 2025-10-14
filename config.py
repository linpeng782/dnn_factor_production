"""
因子处理配置模块
统一管理路径配置、YAML配置加载和工具函数
"""

import os

# ==================== 路径配置 ====================
# 数据根目录 - 遵循数据和代码分离的开发范式
DATA_ROOT = "/Users/didi/Data"

# 数据路径
RAW_DATA_DIR = os.path.join(DATA_ROOT, "dnn_model", "raw", "日线后复权及常用指标csv")
ENHANCED_DATA_DIR = os.path.join(
    DATA_ROOT, "dnn_model", "enhanced", "enhanced_factors_csv"
)
CACHE_DIR = os.path.join(DATA_ROOT, "dnn_model", "cache")
REPORTS_DIR = os.path.join(DATA_ROOT, "dnn_model", "comparison_reports")

# ==================== 统一配置字典 ====================
_CONFIG_DATA = {
    "factor_name_mapping": {
        "date": "交易日期",
        "order_book_id": "股票代码",
        "stock_name": "股票简称",
        "open": "开盘价",
        "high": "最高价",
        "low": "最低价",
        "close": "收盘价",
        "prev_close": "昨收价",
        "change_amount": "涨跌额",
        "change_pct": "涨跌幅",
        "amplitude": "振幅",
        "total_turnover": "成交额",
        "unadjusted_volume": "未复权成交量",
        "volume": "后复权成交量",
        "vwap": "成交量加权平均价格(vwap)",
        "turnover_rate": "换手率(%)",
        "free_turnover": "换手率(自由流通股)",
        "stock_free_circulation": "自由流通股本",
        "capital_inflow": "日度主买合计金额",
        "capital_outflow": "日度主卖合计金额",
        "pe_ratio_lyr": "市盈率_最近年报",
        "pe_ratio_ttm": "市盈率_TTM",
        "pb_ratio_lyr": "市净率_最近年报",
        "pb_ratio_ttm": "市净率_TTM",
        "pb_ratio_lf": "市净率_最新财报",
        "ps_ratio_lyr": "市销率_最近年报",
        "ps_ratio_ttm": "市销率_TTM",
        "dividend_yield_ttm": "股息率_TTM",
        "market_cap_3": "总市值",
        "market_cap_2": "流通市值",
        "book_to_market_ratio_lyr": "账面市值比_最近年报",
        "book_to_market_ratio_ttm": "账面市值比_TTM",
        "book_to_market_ratio_lf": "账面市值比_最新财报",
        "ebit_lyr": "息税前利润_最近年报",
        "ebit_ttm": "息税前利润_TTM",
        "ebitda_lyr": "息税折旧摊销前利润_最近年报",
        "ebitda_ttm": "息税折旧摊销前利润_TTM",
        "ebit_per_share_lyr": "每股息税前利润_最近年报",
        "ebit_per_share_ttm": "每股息税前利润_TTM",
        "return_on_equity_lyr": "净资产收益率_最近年报",
        "return_on_equity_ttm": "净资产收益率_TTM",
    },
    "fundamental_factors": [
        "pe_ratio_lyr",
        "pe_ratio_ttm",
        "pb_ratio_lyr",
        "pb_ratio_ttm",
        "pb_ratio_lf",
        "ps_ratio_lyr",
        "ps_ratio_ttm",
        "dividend_yield_ttm",
        "market_cap_3",
        "market_cap_2",
        "book_to_market_ratio_lyr",
        "book_to_market_ratio_ttm",
        "book_to_market_ratio_lf",
        "ebit_lyr",
        "ebit_ttm",
        "ebitda_lyr",
        "ebitda_ttm",
        "ebit_per_share_lyr",
        "ebit_per_share_ttm",
        "return_on_equity_lyr",
        "return_on_equity_ttm",
    ],
    "technical_factors": [
        "open",
        "high",
        "low",
        "close",
        "volume",
        "total_turnover",
    ],
    "flow_factors": [
        "capital_inflow",
        "capital_outflow",
    ],
    "column_order": [
        "date",
        "order_book_id",
        "stock_name",
        "open",
        "high",
        "low",
        "close",
        "prev_close",
        "change_amount",
        "change_pct",
        "amplitude",
        "total_turnover",
        "unadjusted_volume",
        "volume",
        "vwap",
        "turnover_rate",
        "free_turnover",
        "stock_free_circulation",
        "pe_ratio_lyr",
        "pe_ratio_ttm",
        "pb_ratio_lyr",
        "pb_ratio_ttm",
        "pb_ratio_lf",
        "ps_ratio_lyr",
        "ps_ratio_ttm",
        "dividend_yield_ttm",
        "market_cap_3",
        "market_cap_2",
        "book_to_market_ratio_lyr",
        "book_to_market_ratio_ttm",
        "book_to_market_ratio_lf",
        "ebit_lyr",
        "ebit_ttm",
        "ebitda_lyr",
        "ebitda_ttm",
        "ebit_per_share_lyr",
        "ebit_per_share_ttm",
        "return_on_equity_lyr",
        "return_on_equity_ttm",
        "capital_inflow",
        "capital_outflow",
    ],
}


# ==================== 配置加载 ====================
def get_config():
    """
    返回统一的配置字典

    Returns:
        dict: 配置字典
    """
    return _CONFIG_DATA.copy()  # 返回副本以防止外部修改
