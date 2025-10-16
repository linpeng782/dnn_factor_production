#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
每日因子处理任务 - 支持命令行参数
"""

import os
import sys
import argparse
from datetime import datetime, timedelta
from loguru import logger

# 添加项目根目录到sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入配置和处理模块
from config import RAW_DATA_DIR, ENHANCED_DATA_DIR, DATA_ROOT
from batch_processor import (
    run_parallel_stock_processing,
    retry_failed_stocks,
    _process_single_stock,
)


def get_today_date():
    """获取今天的日期 (YYYYMMDD格式)"""
    return datetime.now().strftime("%Y%m%d")


def setup_logging():
    """配置日志"""
    log_dir = os.path.join(DATA_ROOT, "dnn_model", "logs")
    os.makedirs(log_dir, exist_ok=True)

    log_file = os.path.join(
        log_dir, f"factor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    )
    logger.add(log_file, rotation="500 MB", retention="30 days", encoding="utf-8")
    return log_file


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="每日因子处理")
    parser.add_argument("--date", default=None, help="数据日期(YYYYMMDD)，默认今天")
    parser.add_argument(
        "--mode",
        default="batch",
        choices=["batch", "single", "retry"],
        help="运行模式: batch=批量处理, single=单股测试, retry=重试失败",
    )
    parser.add_argument("--limit", type=int, default=None, help="限制股票数量")
    parser.add_argument("--workers", type=int, default=4, help="线程数")
    parser.add_argument("--stock", default="000001.XSHE", help="单股模式: 股票代码")
    parser.add_argument("--stock-name", default="平安银行", help="单股模式: 股票名称")

    args = parser.parse_args()

    log_file = setup_logging()
    dataset_end_date = args.date if args.date else get_today_date()
    data_dir = RAW_DATA_DIR
    save_dir = f"{ENHANCED_DATA_DIR}_{dataset_end_date}"
    os.makedirs(save_dir, exist_ok=True)

    logger.info(f"开始处理 {dataset_end_date} 的数据")
    logger.info(f"运行模式: {args.mode}")
    logger.warning(f"日志文件: {log_file}")

    try:
        # 执行相应的测试模式
        if args.mode == "single":
            # 测试单只股票
            logger.success("测试单只股票")
            stock_info = {"converted_code": args.stock, "stock_name": args.stock_name}
            is_success, error_message = _process_single_stock(
                stock_info, save_dir, dataset_end_date
            )
            if is_success:
                logger.success(f"✅ 股票 {args.stock}({args.stock_name}) 处理成功")
            else:
                logger.error(
                    f"❌ 股票 {args.stock}({args.stock_name}) 处理失败: {error_message}"
                )

        elif args.mode == "batch":
            # 并行批量测试所有股票
            logger.success("并行批量处理所有股票")
            run_parallel_stock_processing(
                data_dir,
                save_dir,
                dataset_end_date,
                limit=args.limit,
                max_workers=args.workers,
            )

        elif args.mode == "retry":
            # 串行重试失败的股票
            logger.success("串行重试处理失败的股票")
            retry_failed_stocks(save_dir, dataset_end_date)

    except Exception as e:
        logger.error(f"处理失败: {e}")
        raise
