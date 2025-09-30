import os
import sys
from datetime import datetime

# 添加项目根目录到sys.path（必须在导入其他模块之前）
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入配置
from config import get_config
from batch_processor import (
    batch_process_stocks_parallel,
    retry_failed_stocks,
    test_single_stock,
)


# 主执行函数
if __name__ == "__main__":
    # 获取配置信息
    config = get_config()

    # 从配置中获取参数
    dataset_end_date = config["dataset_end_date"]
    test_mode = config["test_mode"]
    max_workers = config["max_workers"]

    DATA_PATH = "/Users/didi/DATA/dnn_model"
    data_dir = os.path.join(DATA_PATH, "raw", "日线后复权及常用指标csv")
    timestamp = datetime.now().strftime("%Y%m%d")
    save_dir = os.path.join(DATA_PATH, "enhanced", "enhanced_factors_csv_" + timestamp)

    # 确保输出目录存在
    os.makedirs(save_dir, exist_ok=True)

    print(f"淘宝数据路径: {data_dir}")
    print(f"因子数据保存路径: {save_dir}")
    print(f"数据下载结束日期: {dataset_end_date}")
    print(f"因子数据保存时间戳: {timestamp}")

    # 执行相应的测试模式
    if test_mode == "single":
        # 测试单只股票
        stock_code = "000001.XSHE"
        test_single_stock(stock_code, save_dir, dataset_end_date)

    elif test_mode == "batch":
        # 选择并行或串行处理

        limit = None  # 处理所有股票
        print(f"并行批量测试所有股票")
        batch_process_stocks_parallel(
            data_dir,
            save_dir,
            dataset_end_date,
            limit,
            max_workers=max_workers,
        )

    elif test_mode == "retry_failed":
        # 串行重试失败的股票
        print(f"串行重试处理失败的股票")
        retry_failed_stocks(save_dir, dataset_end_date)
