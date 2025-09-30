"""
批处理引擎模块
负责股票因子数据的批量处理，支持并行和串行模式
"""

import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from loguru import logger
from factor_utils import *

from data_utils import (
    get_stock_list_from_csv_folder,
    get_failed_stocks,
)
from factor_calculator import generate_factors_for_stock


def test_single_stock(stock_symbol, output_folder_path, end_date="20250718"):
    """
    测试单只股票
    """
    logger.info(f"测试单只股票: {stock_symbol}")
    factors_df = generate_factors_for_stock(stock_symbol, end_date)

    if factors_df is not None:
        # 创建输出文件夹
        output_folder = Path(output_folder_path)
        output_folder.mkdir(exist_ok=True)

        # 获取股票名称
        stock_name = instruments(stock_symbol).symbol

        # 保存CSV文件
        output_filename = (
            f"{stock_symbol}-{stock_name}-日线后复权及常用指标-{end_date}.csv"
        )
        output_path = output_folder / output_filename
        factors_df.to_csv(output_path, encoding="utf-8", index=False)
        logger.success(f"成功保存: {output_filename}")
        logger.info(f"数据形状: {factors_df.shape}")
        logger.info(f"列名: {list(factors_df.columns)}")
        return True
    else:
        logger.error("处理失败")
        return False


def batch_process_stocks_parallel(
    csv_folder_path, output_folder_path, end_date, limit=None, max_workers=4
):
    """
    并行批量处理股票因子数据
    """
    # 获取股票列表
    stock_list = get_stock_list_from_csv_folder(csv_folder_path, limit)

    if not stock_list:
        logger.warning("未找到任何股票CSV文件")
        return

    # 清空旧的失败日志，重新开始记录
    from data_utils import get_failed_log_path

    failed_log_file = get_failed_log_path()
    if failed_log_file.exists():
        failed_log_file.unlink()
        logger.info("已清空旧的失败记录")

    logger.info(f"准备并行处理 {len(stock_list)} 只股票，使用 {max_workers} 个线程")

    # 创建输出文件夹
    output_folder = Path(output_folder_path)
    output_folder.mkdir(exist_ok=True)

    # 删除旧文件
    old_files = list(output_folder.glob("*.csv"))
    if old_files:
        logger.info(f"删除 {len(old_files)} 个旧文件")
        for old_file in old_files:
            old_file.unlink()

    success_count = 0
    failed_count = 0
    failed_stocks_list = []  # 收集失败的股票信息

    # 使用线程池并行处理
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有任务
        future_to_stock = {
            executor.submit(
                generate_factors_for_stock, stock_info["converted_code"], end_date
            ): stock_info
            for stock_info in stock_list
        }

        # 使用tqdm显示进度条
        with tqdm(total=len(stock_list), desc="处理", unit="只") as pbar:
            for future in as_completed(future_to_stock):
                stock_info = future_to_stock[future]
                stock_symbol = stock_info["converted_code"]
                stock_name = stock_info["stock_name"]

                try:
                    factors_df = future.result()

                    if factors_df is not None:
                        # 保存文件
                        output_filename = f"{stock_symbol}-{stock_name}-日线后复权及常用指标-{end_date}.csv"
                        output_path = output_folder / output_filename
                        factors_df.to_csv(output_path, encoding="utf-8", index=False)
                        success_count += 1
                    else:
                        # 返回None说明内部已捕获异常，收集到列表
                        failed_count += 1
                        failed_stocks_list.append(
                            {"stock_code": stock_symbol, "stock_name": stock_name}
                        )

                except Exception as e:
                    # 捕获其他未预期的异常（如文件保存失败等）
                    failed_count += 1
                    failed_stocks_list.append(
                        {"stock_code": stock_symbol, "stock_name": stock_name}
                    )
                    logger.error(f"失败: {stock_symbol} - {type(e).__name__}: {str(e)}")

                pbar.set_postfix({"OK": success_count, "NG": failed_count})
                pbar.update(1)

    # 批量写入失败记录（一次性I/O，提高性能）
    if failed_stocks_list:
        from data_utils import get_failed_log_path
        from datetime import datetime

        failed_log_file = get_failed_log_path()
        with open(failed_log_file, "w", encoding="utf-8") as f:
            for stock in failed_stocks_list:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                log_line = f"{stock['stock_code']}|{stock['stock_name']}|batch_failed||{timestamp}\n"
                f.write(log_line)

    # 输出汇总
    logger.info("=" * 50)
    logger.success("处理完成！")
    logger.info(f"成功: {success_count} 只 ({success_count/len(stock_list)*100:.2f}%)")
    logger.info(f"失败: {failed_count} 只 ({failed_count/len(stock_list)*100:.2f}%)")
    logger.info(f"总计: {len(stock_list)} 只")
    if failed_count > 0:
        logger.warning(f"失败股票已记录到: factor_production/log/failed_stocks_*.txt")
    logger.info("=" * 50)


def retry_failed_stocks(output_folder_path, end_date):
    """
    串行重试处理失败的股票
    """
    failed_stocks = get_failed_stocks()

    if not failed_stocks:
        logger.success("所有股票都已成功处理，无需重试")
        return

    logger.info(f"找到 {len(failed_stocks)} 只失败股票，开始串行重试")

    # 清空失败日志，避免重复累积
    from data_utils import get_failed_log_path

    failed_log_file = get_failed_log_path()
    if failed_log_file.exists():
        failed_log_file.unlink()
        logger.info("已清空旧的失败记录，重新开始记录")

    # 创建输出文件夹
    output_folder = Path(output_folder_path)
    output_folder.mkdir(exist_ok=True)

    success_count = 0
    retry_failed_list = []  # 收集retry失败的股票

    for stock_info in tqdm(failed_stocks, desc="重试", unit="只"):
        stock_symbol = stock_info["converted_code"]
        stock_name = stock_info["stock_name"]

        try:
            factors_df = generate_factors_for_stock(stock_symbol, end_date)

            if factors_df is not None:
                output_filename = (
                    f"{stock_symbol}-{stock_name}-日线后复权及常用指标-{end_date}.csv"
                )
                output_path = output_folder / output_filename
                factors_df.to_csv(output_path, encoding="utf-8", index=False)
                success_count += 1
            else:
                # retry失败，收集到列表
                retry_failed_list.append(
                    {"stock_code": stock_symbol, "stock_name": stock_name}
                )

        except Exception as e:
            # retry异常，收集到列表
            retry_failed_list.append(
                {"stock_code": stock_symbol, "stock_name": stock_name}
            )
            logger.error(f"重试 {stock_symbol} 异常: {type(e).__name__}: {str(e)}")

        time.sleep(1)

    # 批量写入retry失败记录
    if retry_failed_list:
        from data_utils import get_failed_log_path
        from datetime import datetime

        failed_log_file = get_failed_log_path()
        with open(failed_log_file, "w", encoding="utf-8") as f:
            for stock in retry_failed_list:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                log_line = f"{stock['stock_code']}|{stock['stock_name']}|retry_failed||{timestamp}\n"
                f.write(log_line)

    # 输出汇总
    failed_count = len(failed_stocks) - success_count
    logger.info("=" * 50)
    logger.success("重试完成！")
    logger.info(
        f"成功: {success_count} 只，失败: {failed_count} 只，总计: {len(failed_stocks)} 只"
    )
    if failed_count > 0:
        logger.warning("失败股票已记录到: factor_production/log/failed_stocks_*.txt")
    logger.info("=" * 50)
