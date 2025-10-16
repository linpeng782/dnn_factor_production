"""
批处理引擎模块
负责股票因子数据的批量处理，支持并行和串行模式
"""

import time
import os
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from loguru import logger
from rq_api import init_rq_api
from data_utils import (
    get_stock_list_from_csv_folder,
    get_failed_stocks,
    get_failed_log_path,
    write_failure_logs,
)
from factor_calculator import generate_factors_for_stock

# 常量定义
RETRY_SLEEP_SECONDS = 1  # 串行重试时的延迟秒数


def run_parallel_stock_processing(
    csv_folder_path, output_folder_path, dataset_end_date, limit=None, max_workers=4
):
    """
    【主函数】编排整个并行处理流程。
    """
    # --- 1. 准备阶段 ---
    logger.info("--- 开始准备阶段 ---")
    
    # 初始化米筐API
    logger.info("初始化米筐API...")
    if not init_rq_api():
        logger.error("米筐API初始化失败，任务终止")
        return
    
    stock_list = get_stock_list_from_csv_folder(csv_folder_path, limit)
    if not stock_list:
        logger.error("股票列表为空，任务终止。")
        return

    logger.info("准备输出目录...")
    os.makedirs(output_folder_path, exist_ok=True)

    # 删除旧的CSV文件
    for filename in os.listdir(output_folder_path):
        if filename.endswith(".csv"):
            file_path = os.path.join(output_folder_path, filename)
            os.remove(file_path)
    logger.warning(f"已清空目录: {output_folder_path}")

    logger.warning("清理旧的失败日志...")
    failed_log_file = get_failed_log_path()
    if os.path.exists(failed_log_file):
        os.remove(failed_log_file)

    # --- 2. 执行阶段 ---
    logger.success("--- 进入执行阶段 ---")
    logger.success(f"准备并行处理 {len(stock_list)} 只股票，使用 {max_workers} 个线程")

    success_count, failed_stocks_list = _execute_parallel_processing(
        stock_list, output_folder_path, dataset_end_date, max_workers
    )

    # --- 3. 收尾阶段 ---
    logger.success("--- 进入收尾阶段 ---")

    total_count = len(stock_list)
    failed_count = len(failed_stocks_list)

    if failed_count > 0:
        logger.warning(f"处理完成，有 {failed_count} 只股票失败，正在生成分析报告...")

        # 写入汇总报告
        log_dir = os.path.dirname(get_failed_log_path())
        summary_file = write_failure_logs(failed_stocks_list, log_dir, total_count)

        logger.warning(f"汇总报告: {summary_file}")

    logger.info("=" * 50)
    logger.success(
        f"成功: {success_count} / {total_count} ({success_count/total_count:.2%})"
    )
    logger.warning(
        f"失败: {failed_count} / {total_count} ({failed_count/total_count:.2%})"
    )
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
            output_path = os.path.join(output_folder, output_filename)
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
    if os.path.exists(failed_log_file):
        os.remove(failed_log_file)
    os.makedirs(output_folder_path, exist_ok=True)

    success_count = 0
    failed_stocks_list = []

    for stock_info in tqdm(failed_stocks, desc="重试", unit="只"):
        is_success, error_message = _process_single_stock(
            stock_info, output_folder_path, dataset_end_date
        )

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
        time.sleep(RETRY_SLEEP_SECONDS)

    # 收尾：记录汇总报告
    failed_count = len(failed_stocks_list)
    if failed_count > 0:
        log_dir = os.path.dirname(failed_log_file)
        summary_file = write_failure_logs(
            failed_stocks_list, log_dir, len(failed_stocks)
        )
        logger.warning(f"汇总报告: {summary_file}")

    logger.info("=" * 50)
    logger.success("重试完成！")
    logger.info(
        f"成功: {success_count} 只，失败: {failed_count} 只，总计: {len(failed_stocks)} 只"
    )
    logger.info("=" * 50)
