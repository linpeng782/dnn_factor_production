# 因子工程 - Factor Engineering

股票因子计算和批量处理系统

## 项目简介

本项目用于批量计算股票的技术因子和基本面因子，支持：
- 51个因子计算（技术因子、基本面因子、资金流因子等）
- 并行批量处理（支持多线程）
- 失败重试机制
- 完整的日志记录

## 目录结构

```
factor_engineering/
├── run_batch_factor_processing.py  # 主程序（命令行参数版本）
├── batch_processor.py              # 批量处理核心逻辑
├── factor_calculator.py            # 因子计算模块
├── rq_api.py                       # 米筐API封装
├── data_utils.py                   # 数据处理工具
├── config.py                       # 配置文件
├── run_daily_factor_processing.sh  # 定时任务脚本
├── crontab.txt                     # cron配置
├── 命令行参数详解.md                # 使用教程
└── log/                            # 日志目录
    ├── factor_*.log                # 运行日志
    ├── failed_stocks_*.txt         # 失败股票列表
    └── failed_summary_*.txt        # 失败汇总报告
```

## 快速开始

### 1. 环境准备

```bash
# 激活虚拟环境
source ../peterdidi/bin/activate

# 安装依赖（如果需要）
pip install -r requirements.txt
```

### 2. 基本使用

```bash
# 处理今天的所有股票
python run_batch_factor_processing.py

# 处理指定日期
python run_batch_factor_processing.py --date 20251015

# 测试模式（只处理10只股票）
python run_batch_factor_processing.py --limit 10

# 测试单只股票
python run_batch_factor_processing.py --mode single --stock 000001.XSHE --stock-name 平安银行

# 重试失败的股票
python run_batch_factor_processing.py --mode retry

# 使用更多线程
python run_batch_factor_processing.py --workers 8
```

### 3. 查看帮助

```bash
python run_batch_factor_processing.py --help
```

## 命令行参数

| 参数 | 说明 | 默认值 | 示例 |
|------|------|--------|------|
| `--date` | 数据日期 | 今天 | `--date 20251015` |
| `--mode` | 运行模式 | `batch` | `--mode single` |
| `--limit` | 限制数量 | `None` | `--limit 50` |
| `--workers` | 线程数 | `4` | `--workers 8` |
| `--stock` | 股票代码 | `000001.XSHE` | `--stock 600519.XSHG` |
| `--stock-name` | 股票名称 | `平安银行` | `--stock-name 贵州茅台` |

## 运行模式

- **`batch`** - 批量处理所有股票（默认）
- **`single`** - 测试单只股票
- **`retry`** - 重试之前失败的股票

## 因子列表

### 基础信息（3个）
- 交易日期、股票代码、股票简称

### 后复权技术因子（7个）
- 开盘价、最高价、最低价、收盘价、昨收价、成交量、成交量加权平均价

### 衍生技术因子（7个）
- 涨跌额、涨跌幅、振幅、成交额、换手率、换手率（自由流通股）、自由流通股本

### 未复权技术因子（6个）
- 成交量、开盘价、最高价、最低价、收盘价、成交量加权平均价

### 资金流因子（2个）
- 日度主买合计金额、日度主卖合计金额

### 基本面因子（21个）
- 市盈率、市净率、市销率、股息率、总市值、流通市值、账面市值比
- 息税前利润、息税折旧摊销前利润、每股息税前利润、净资产收益率等

### 股东户数因子（5个）
- 股东总户数、户均持股数、A股股东户数、A股户均持股数、无限售A股户均持股数

**总计：51个因子**

## 输出说明

### 成功输出
```
/Users/didi/Data/dnn_model/enhanced/enhanced_factors_csv_YYYYMMDD/
├── 000001.XSHE.csv
├── 000002.XSHE.csv
└── ...
```

### 日志文件
```
/Users/didi/dnn_model/factor_engineering/log/
├── factor_YYYYMMDD_HHMMSS.log    # 运行日志
├── failed_stocks_YYYYMMDD.txt    # 失败股票详细列表
└── failed_summary_YYYYMMDD.txt   # 失败汇总报告
```

## 定时任务

### 配置 cron

```bash
# 安装定时任务
crontab crontab.txt

# 查看定时任务
crontab -l

# 编辑定时任务
crontab -e
```

### 默认配置

每天晚上 20:30 自动执行：
```
30 20 * * * /Users/didi/dnn_model/factor_engineering/run_daily_factor_processing.sh
```

## 常见问题

### Q1: 如何查看处理结果？

```bash
# 查看最新日志
tail -100 log/factor_*.log

# 查看失败报告
cat log/failed_summary_*.txt
```

### Q2: 如何处理失败的股票？

```bash
# 1. 先运行批量处理
python run_batch_factor_processing.py --date 20251015

# 2. 查看失败报告
cat log/failed_summary_20251015.txt

# 3. 重试失败的股票
python run_batch_factor_processing.py --date 20251015 --mode retry
```

### Q3: 如何提高处理速度？

```bash
# 使用更多线程（建议 4-8）
python run_batch_factor_processing.py --workers 8
```

### Q4: 如何测试代码？

```bash
# 先测试 1 只股票
python run_batch_factor_processing.py --mode single --stock 000001.XSHE

# 再测试 10 只股票
python run_batch_factor_processing.py --limit 10

# 确认无误后处理全部
python run_batch_factor_processing.py
```

## 性能参考

| 股票数量 | 线程数 | 预计耗时 |
|----------|--------|----------|
| 10 | 4 | ~5秒 |
| 50 | 4 | ~20秒 |
| 100 | 4 | ~40秒 |
| 500 | 4 | ~3分钟 |
| 5000 | 4 | ~30分钟 |
| 5000 | 8 | ~15分钟 |

## 依赖说明

- Python 3.8+
- pandas
- loguru
- tqdm
- rqdatac（米筐数据）

## 注意事项

1. 确保米筐 API 已初始化
2. 线程数不要设置太高（避免 API 限流）
3. 定期清理日志文件
4. 北交所部分股票可能无法获取数据

## 更新日志

### 2025-10-15
- ✅ 添加命令行参数支持
- ✅ 优化日志输出
- ✅ 添加失败重试机制
- ✅ 完善文档

## 作者

Peter Zheng (peterzhenglinpeng@didiglobal.com)

## 许可证

内部项目，仅供公司内部使用
