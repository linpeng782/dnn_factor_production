# 使用说明

## 快速开始

### 方式1：使用命令行参数（推荐）

```bash
# 激活虚拟环境
source ../peterdidi/bin/activate

# 处理所有股票（使用今天的日期）
python run_batch_factor_processing.py --date today

# 处理所有股票（指定日期）
python run_batch_factor_processing.py --date 20251015

# 测试模式（只处理50只股票）
python run_batch_factor_processing.py --date 20251015 --limit 50

# 测试单只股票
python run_batch_factor_processing.py --date 20251015 --mode single --stock 000001.XSHE

# 重试失败的股票
python run_batch_factor_processing.py --date 20251015 --mode retry

# 使用8个线程加速处理
python run_batch_factor_processing.py --date 20251015 --workers 8
```

### 方式2：使用Shell脚本（定时任务使用）

```bash
# 手动运行
./run_daily_factor_processing.sh

# 脚本会自动使用当天日期
```

### 方式3：使用旧版脚本（不推荐）

```bash
# 需要手动修改代码中的参数
python feval_batch_factor_processing.py
```

---

## 命令行参数详解

### 必需参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `--date` | 数据截止日期 | `--date 20251015` 或 `--date today` |

### 可选参数

| 参数 | 说明 | 默认值 | 示例 |
|------|------|--------|------|
| `--mode` | 运行模式 | `batch` | `--mode single` |
| `--limit` | 限制处理数量 | `None`（全部） | `--limit 50` |
| `--workers` | 线程数 | `4` | `--workers 8` |
| `--stock` | 股票代码（单只模式） | `000001.XSHE` | `--stock 600000.XSHG` |
| `--data-dir` | 原始数据目录 | 配置文件路径 | `--data-dir /path/to/data` |
| `--output-dir` | 输出目录 | 配置文件路径 | `--output-dir /path/to/output` |

### 运行模式说明

| 模式 | 说明 | 使用场景 |
|------|------|----------|
| `batch` | 批量处理 | 正式运行，处理所有股票 |
| `single` | 单只股票 | 测试和调试 |
| `retry` | 重试失败 | 处理之前失败的股票 |

---

## 常用场景

### 场景1：日常生产运行

```bash
# 每天定时运行（通过cron）
# crontab已配置为每天20:30自动执行
crontab -l
```

### 场景2：手动补充数据

```bash
# 补充某一天的数据
python run_batch_factor_processing.py --date 20251010

# 补充多天的数据（使用循环）
for date in 20251010 20251011 20251012; do
    python run_batch_factor_processing.py --date $date
done
```

### 场景3：开发测试

```bash
# 测试10只股票
python run_batch_factor_processing.py --date today --limit 10

# 测试单只股票
python run_batch_factor_processing.py --date today --mode single --stock 000001.XSHE

# 测试平安银行
python run_batch_factor_processing.py --date today --mode single --stock 000001.XSHE
```

### 场景4：处理失败重试

```bash
# 1. 先运行批量处理
python run_batch_factor_processing.py --date 20251015

# 2. 查看失败日志
cat log/failed_summary_*.txt

# 3. 重试失败的股票
python run_batch_factor_processing.py --date 20251015 --mode retry
```

### 场景5：性能优化

```bash
# 使用更多线程（适合高性能服务器）
python run_batch_factor_processing.py --date today --workers 16

# 使用更少线程（避免API限流）
python run_batch_factor_processing.py --date today --workers 2
```

---

## 输出说明

### 成功输出

```
/Users/didi/Data/dnn_model/enhanced/enhanced_factors_csv_20251015/
├── 000001.XSHE.csv
├── 000002.XSHE.csv
├── 600000.XSHG.csv
└── ...
```

### 日志文件

```
/Users/didi/Data/dnn_model/logs/
├── daily_job_20251015_203000.log    # 任务日志
└── cron.log                          # cron输出日志

/Users/didi/dnn_model/factor_engineering/log/
├── failed_stocks_20251015.txt        # 失败股票详细日志
└── failed_summary_20251015.txt       # 失败股票汇总报告
```

### 查看结果

```bash
# 查看处理结果
ls -lh /Users/didi/Data/dnn_model/enhanced/enhanced_factors_csv_20251015/

# 查看失败股票
cat /Users/didi/dnn_model/factor_engineering/log/failed_summary_*.txt

# 查看最新日志
tail -100 /Users/didi/Data/dnn_model/logs/daily_job_*.log
```

---

## 性能参考

| 股票数量 | 线程数 | 预计耗时 |
|----------|--------|----------|
| 10 | 4 | ~5秒 |
| 50 | 4 | ~20秒 |
| 100 | 4 | ~40秒 |
| 500 | 4 | ~3分钟 |
| 5000 | 4 | ~30分钟 |
| 5000 | 8 | ~15分钟 |

**注意**：
- 实际耗时取决于网络速度和API响应时间
- 线程数过多可能导致API限流
- 建议线程数设置为 4-8

---

## 故障排查

### 问题1：命令找不到

```bash
# 确保在正确的目录
cd /Users/didi/dnn_model/factor_engineering

# 确保虚拟环境已激活
source ../peterdidi/bin/activate

# 确认Python版本
python --version
```

### 问题2：日期格式错误

```bash
# ❌ 错误
python run_batch_factor_processing.py --date 2025-10-15

# ✅ 正确
python run_batch_factor_processing.py --date 20251015
```

### 问题3：米筐API连接失败

```bash
# 检查网络
ping api.ricequant.com

# 检查API初始化
python -c "from rq_api import init_rq_api; init_rq_api()"
```

### 问题4：权限问题

```bash
# 确保脚本有执行权限
chmod +x run_daily_factor_processing.sh

# 确保日志目录存在
mkdir -p /Users/didi/Data/dnn_model/logs
```

---

## 最佳实践

### 1. 开发阶段

```bash
# 先测试少量股票
python run_batch_factor_processing.py --date today --limit 10

# 确认无误后再处理全部
python run_batch_factor_processing.py --date today
```

### 2. 生产环境

```bash
# 使用定时任务自动运行
crontab -l

# 定期检查日志
tail -f /Users/didi/Data/dnn_model/logs/cron.log
```

### 3. 数据质量检查

```bash
# 处理完成后检查
python find_nan_end.py

# 查看失败报告
cat log/failed_summary_*.txt
```

---

## 文件对比

| 文件 | 用途 | 推荐度 |
|------|------|--------|
| `run_batch_factor_processing.py` | 命令行参数版本 | ⭐⭐⭐⭐⭐ 推荐 |
| `run_daily_factor_processing.sh` | Shell脚本（定时任务） | ⭐⭐⭐⭐⭐ 推荐 |
| `feval_batch_factor_processing.py` | 旧版本（硬编码参数） | ⭐⭐ 不推荐 |

---

## 云服务器部署

```bash
# 1. 克隆代码
git clone git@gitlab.company.com:your-username/factor_engineering.git

# 2. 修改路径（如果需要）
nano run_daily_factor_processing.sh
nano crontab.txt

# 3. 安装定时任务
crontab crontab.txt

# 4. 验证
crontab -l
```

详见 [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
