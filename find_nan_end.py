"""
查找特定列中 NaN 结束的位置

这是一个通用的数据质量检查工具，可以用于任何 DataFrame。

使用方法:
    from find_nan_end import find_nan_end
    
    # 基本用法
    result = find_nan_end(df, '列名')
    
    # 返回值是一个字典，包含统计信息
    print(f"第一个非 NaN 的行号: {result['first_non_nan_index']}")
"""

import pandas as pd
import sys

def find_nan_end(df, column_name):
    """
    查找指定列中 NaN 值结束的位置
    
    Args:
        df: DataFrame
        column_name: 列名
    
    Returns:
        dict: 包含统计信息的字典
    """
    # 类型检查
    if not isinstance(df, pd.DataFrame):
        raise TypeError(f"第一个参数必须是 pandas DataFrame，而不是 {type(df).__name__}")
    
    print("=" * 100)
    print(f"查找列 '{column_name}' 中 NaN 的分布情况")
    print("=" * 100)
    print()
    
    # 检查列是否存在
    if column_name not in df.columns:
        print(f"❌ 错误：列 '{column_name}' 不存在！")
        print(f"可用的列：{list(df.columns)}")
        return None
    
    # 获取该列
    col = df[column_name]
    
    # 统计信息
    total_rows = len(df)
    nan_count = col.isna().sum()
    non_nan_count = col.notna().sum()
    
    print(f"【1. 基本统计】")
    print("-" * 100)
    print(f"总行数: {total_rows}")
    print(f"NaN 数量: {nan_count} ({nan_count/total_rows*100:.2f}%)")
    print(f"非 NaN 数量: {non_nan_count} ({non_nan_count/total_rows*100:.2f}%)")
    print()
    
    # 找到第一个非 NaN 的位置
    first_non_nan_idx = col.first_valid_index()
    
    if first_non_nan_idx is None:
        print("❌ 该列全部都是 NaN！")
        return None
    
    print(f"【2. 第一个非 NaN 值的位置】")
    print("-" * 100)
    print(f"索引位置: {first_non_nan_idx}")
    print(f"行号（从0开始）: {first_non_nan_idx}")
    
    # 显示该行的详细信息
    if "交易日期" in df.columns:
        date_col = "交易日期"
    elif "date" in df.columns:
        date_col = "date"
    else:
        date_col = None
    
    if date_col:
        first_date = df.loc[first_non_nan_idx, date_col]
        print(f"对应日期: {first_date}")
    
    first_value = df.loc[first_non_nan_idx, column_name]
    print(f"第一个非 NaN 值: {first_value}")
    print()
    
    # 显示前后几行的数据
    print(f"【3. 第一个非 NaN 值前后的数据】")
    print("-" * 100)
    
    # 确定显示范围
    start_idx = max(0, first_non_nan_idx - 3)
    end_idx = min(len(df), first_non_nan_idx + 4)
    
    # 选择要显示的列
    display_cols = []
    if date_col:
        display_cols.append(date_col)
    if "股票代码" in df.columns:
        display_cols.append("股票代码")
    elif "order_book_id" in df.columns:
        display_cols.append("order_book_id")
    display_cols.append(column_name)
    
    # 显示数据
    context_df = df.loc[start_idx:end_idx-1, display_cols].copy()
    context_df.insert(0, "行号", range(start_idx, end_idx))
    
    print(context_df.to_string(index=False))
    print()
    
    # 检查是否有中间的 NaN（即非 NaN 之后又出现 NaN）
    print(f"【4. 检查数据完整性】")
    print("-" * 100)
    
    # 从第一个非 NaN 开始，检查后续是否还有 NaN
    remaining_nans = col.loc[first_non_nan_idx:].isna().sum()
    
    if remaining_nans > 0:
        print(f"⚠️  警告：在第一个非 NaN 值之后，还有 {remaining_nans} 个 NaN 值")
        print("这可能表示数据不连续或有缺失")
        
        # 找到这些 NaN 的位置
        nan_indices = col.loc[first_non_nan_idx:][col.loc[first_non_nan_idx:].isna()].index.tolist()
        if len(nan_indices) <= 10:
            print(f"这些 NaN 的行号: {nan_indices}")
        else:
            print(f"前10个 NaN 的行号: {nan_indices[:10]}")
    else:
        print("✅ 数据完整：从第一个非 NaN 值开始，后续没有 NaN")
    
    print()
    print("=" * 100)
    print("查找完成！")
    print("=" * 100)
    
    return {
        "first_non_nan_index": first_non_nan_idx,
        "first_non_nan_value": first_value,
        "total_nans": nan_count,
        "remaining_nans": remaining_nans if remaining_nans > 0 else 0
    }


def check_all_columns_nan(df, columns=None):
    """
    批量检查多个列的 NaN 分布情况
    
    Args:
        df: DataFrame
        columns: 要检查的列名列表，如果为 None 则检查所有列
    
    Returns:
        pd.DataFrame: 包含每列 NaN 统计信息的汇总表
    """
    # 类型检查
    if not isinstance(df, pd.DataFrame):
        raise TypeError(f"第一个参数必须是 pandas DataFrame，而不是 {type(df).__name__}")
    
    if columns is None:
        columns = df.columns.tolist()
    
    results = []
    
    for col in columns:
        if col not in df.columns:
            continue
        
        col_data = df[col]
        total = len(df)
        nan_count = col_data.isna().sum()
        non_nan_count = col_data.notna().sum()
        first_valid_idx = col_data.first_valid_index()
        
        # 获取日期信息（如果有）
        first_date = None
        if first_valid_idx is not None:
            if "交易日期" in df.columns:
                first_date = df.loc[first_valid_idx, "交易日期"]
            elif "date" in df.columns:
                first_date = df.loc[first_valid_idx, "date"]
        
        results.append({
            "列名": col,
            "总行数": total,
            "NaN数量": nan_count,
            "NaN占比(%)": round(nan_count / total * 100, 2),
            "非NaN数量": non_nan_count,
            "第一个非NaN行号": first_valid_idx if first_valid_idx is not None else "全部NaN",
            "第一个非NaN日期": first_date if first_date else "-"
        })
    
    summary_df = pd.DataFrame(results)
    
    # 按 NaN 占比从高到低排序
    summary_df = summary_df.sort_values('NaN占比(%)', ascending=False).reset_index(drop=True)
    
    print("=" * 120)
    print("DataFrame 列的 NaN 分布汇总（按 NaN 占比从高到低排序）")
    print("=" * 120)
    print(summary_df.to_string(index=False))
    print("=" * 120)
    
    return summary_df


if __name__ == "__main__":
    print("=" * 100)
    print("通用数据质量检查工具")
    print("=" * 100)
    print()
    print("【使用方法1：检查单个列】")
    print("-" * 100)
    print("from find_nan_end import find_nan_end")
    print("result = find_nan_end(df, '列名')")
    print()
    print("【使用方法2：批量检查所有列】")
    print("-" * 100)
    print("from find_nan_end import check_all_columns_nan")
    print("summary = check_all_columns_nan(df)")
    print()
    print("【使用方法3：批量检查指定列】")
    print("-" * 100)
    print("from find_nan_end import check_all_columns_nan")
    print("summary = check_all_columns_nan(df, ['列1', '列2', '列3'])")
    print()
    print("=" * 100)
