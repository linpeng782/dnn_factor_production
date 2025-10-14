"""
批处理引擎模块
负责股票因子数据的批量处理，支持并行和串行模式
"""

import time
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from loguru import logger
from factor_utils import *
from data_utils import (
    get_stock_list_from_csv_folder,
    get_failed_stocks,
    get_failed_log_path,
)
from factor_calculator import generate_factors_for_stock


def run_parallel_stock_processing(
    csv_folder_path, output_folder_path, dataset_end_date, limit=None, max_workers=4
):
    """
    【主函数】编排整个并行处理流程。
    """
    # --- 1. 准备阶段 ---
    logger.info("--- 开始准备阶段 ---")
    stock_list = get_stock_list_from_csv_folder(csv_folder_path, limit)
    if not stock_list:
        logger.error("股票列表为空，任务终止。")
        return

    logger.info("准备输出目录...")
    output_folder = Path(output_folder_path)
    output_folder.mkdir(exist_ok=True)
    for old_file in output_folder.glob("*.csv"):
        old_file.unlink()
    logger.warning(f"已清空目录: {output_folder}")

    logger.warning("清理旧的失败日志...")
    failed_log_file = get_failed_log_path()
    if failed_log_file.exists():
        failed_log_file.unlink()

    # --- 2. 执行阶段 ---
    logger.info("--- 进入执行阶段 ---")
    logger.success(f"准备并行处理 {len(stock_list)} 只股票，使用 {max_workers} 个线程")

    success_count, failed_stocks_list = _execute_parallel_processing(
        stock_list, output_folder, dataset_end_date, max_workers
    )

    # --- 3. 收尾阶段 ---
    logger.info("--- 进入收尾阶段 ---")

    if failed_stocks_list:
        logger.warning(
            f"处理完成，有 {len(failed_stocks_list)} 只股票失败，正在记录日志..."
        )
        failed_log_file = get_failed_log_path()
        with open(failed_log_file, "w", encoding="utf-8") as f:
            for stock in failed_stocks_list:
                error_msg = str(stock.get("error", "未知错误")).replace("\n", " ")
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                log_line = f"{stock['stock_code']}|{stock['stock_name']}|{error_msg}|{timestamp}\n"
                f.write(log_line)

    total_count = len(stock_list)
    failed_count = len(failed_stocks_list)
    logger.info("=" * 50)
    logger.info(
        f"成功: {success_count} / {total_count} ({success_count/total_count:.2%})"
    )
    logger.info(
        f"失败: {failed_count} / {total_count} ({failed_count/total_count:.2%})"
    )
    if failed_count > 0:
        logger.warning(f"失败详情已记录到: {get_failed_log_path()}")
    logger.info("=" * 50)


def _execute_parallel_processing(
    stock_list, output_folder, dataset_end_date, max_workers
):
    """【重构后】执行核心的并行处理逻辑，统一调用 _process_single_stock。"""
    success_count = 0
    failed_stocks_list = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_stock = {
            executor.submit(
                _process_single_stock, s, output_folder, dataset_end_date
            ): s
            for s in stock_list
        }

        with tqdm(total=len(stock_list), desc="处理", unit="只") as pbar:
            for future in as_completed(future_to_stock):
                stock_info = future_to_stock[future]
                try:
                    is_success, error_message = future.result()
                    if is_success:
                        success_count += 1
                    else:
                        failed_stocks_list.append(
                            {
                                "stock_code": stock_info["converted_code"],
                                "stock_name": stock_info["stock_name"],
                                "error": error_message,
                            }
                        )
                except Exception as e:
                    # 捕获 future.result() 本身可能抛出的、更深层次的异常
                    logger.error(
                        f"处理 {stock_info['converted_code']} 时发生意外的 Future 异常: {e}"
                    )
                    failed_stocks_list.append(
                        {
                            "stock_code": stock_info["converted_code"],
                            "stock_name": stock_info["stock_name"],
                            "error": str(e),
                        }
                    )

                pbar.update(1)
                pbar.set_postfix(
                    {"成功": success_count, "失败": len(failed_stocks_list)}
                )
    return success_count, failed_stocks_list


def _process_single_stock(stock_info, output_folder, dataset_end_date):
    """【新】处理单只股票的核心逻辑，返回 (is_success, error_message)"""
    stock_symbol = stock_info["converted_code"]
    stock_name = stock_info["stock_name"]

    try:
        factors_df, error_message = generate_factors_for_stock(
            stock_symbol, dataset_end_date
        )

        if error_message is None and factors_df is not None:
            # 成功
            output_filename = f"{stock_symbol}-{stock_name}-日线后复权及常用指标-{dataset_end_date}.csv"
            output_path = output_folder / output_filename
            factors_df.to_csv(output_path, encoding="utf-8", index=False)

            return (True, None)
        else:
            # 已知失败
            return (False, error_message or "因子计算返回None")

    except Exception as e:
        # 未知异常
        logger.error(f"处理 {stock_symbol} 时发生意外: {e}")
        return (False, str(e))


def retry_failed_stocks(output_folder_path, dataset_end_date):
    """【重构后】串行重试处理失败的股票"""
    failed_stocks = get_failed_stocks()
    if not failed_stocks:
        logger.success("所有股票都已成功处理，无需重试")
        return

    logger.info(f"找到 {len(failed_stocks)} 只失败股票，开始串行重试")

    # 准备环境
    failed_log_file = get_failed_log_path()
    if failed_log_file.exists():
        failed_log_file.unlink()
    output_folder = Path(output_folder_path)
    output_folder.mkdir(exist_ok=True)

    success_count = 0
    retry_failed_list = []

    for stock_info in tqdm(failed_stocks, desc="重试", unit="只"):
        is_success, error_message = _process_single_stock(
            stock_info, output_folder, dataset_end_date
        )

        if is_success:
            success_count += 1
        else:
            retry_failed_list.append(
                {
                    "stock_code": stock_info["converted_code"],
                    "stock_name": stock_info["stock_name"],
                    "error": error_message,
                }
            )
        time.sleep(1)  # 保留串行重试的延迟

    # 收尾：记录日志和打印报告
    if retry_failed_list:
        with open(failed_log_file, "a", encoding="utf-8") as f:
            for stock in retry_failed_list:
                error_msg = str(stock.get("error", "未知错误")).replace("\n", " ")
                log_line = f"{stock['stock_code']}|{stock['stock_name']}|{error_msg}|{datetime.now()}\n"
                f.write(log_line)

    failed_count = len(failed_stocks) - success_count
    logger.info("=" * 50)
    logger.success("重试完成！")
    logger.info(
        f"成功: {success_count} 只，失败: {failed_count} 只，总计: {len(failed_stocks)} 只"
    )
    if failed_count > 0:
        logger.warning(f"失败详情已记录到: {get_failed_log_path()}")
    logger.info("=" * 50)
