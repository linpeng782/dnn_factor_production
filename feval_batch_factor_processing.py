import os
import sys
from datetime import datetime
from loguru import logger

# 添加项目根目录到sys.path（必须在导入其他模块之前）
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入配置
from config import RAW_DATA_DIR, ENHANCED_DATA_DIR
from batch_processor import (
    run_parallel_stock_processing,
    retry_failed_stocks,
    _process_single_stock,  # 仅用于单股票测试
)


# 主执行函数
if __name__ == "__main__":

    # 从配置中获取参数
    dataset_end_date = "20251015"
    test_mode = "batch"
    test_limit = None

    data_dir = RAW_DATA_DIR
    save_dir = f"{ENHANCED_DATA_DIR}_{dataset_end_date}"

    # 确保输出目录存在
    os.makedirs(save_dir, exist_ok=True)

    logger.info(f"数据源路径: {data_dir}")
    logger.info(f"因子数据保存路径: {save_dir}")
    logger.info(f"数据下载结束日期: {dataset_end_date}")

    # 执行相应的测试模式
    if test_mode == "single":
        # 测试单只股票
        logger.success("测试单只股票")
        stock_info = {"converted_code": "000001.XSHE", "stock_name": "平安银行"}
        is_success, error_message = _process_single_stock(
            stock_info, save_dir, dataset_end_date
        )

    elif test_mode == "batch":
        # 并行批量测试所有股票

        logger.success(f"并行批量测试所有股票")
        run_parallel_stock_processing(
            data_dir,
            save_dir,
            dataset_end_date,
            test_limit,
        )

    elif test_mode == "retry_failed":
        # 串行重试失败的股票
        logger.success(f"串行重试处理失败的股票")
        retry_failed_stocks(save_dir, dataset_end_date)
