# 定时任务快速参考（cron 版本）

## 🎯 当前设置

```
系统: cron（Mac 和 Linux 通用）
任务: 每天晚上 20:30 自动处理因子数据
状态: ✅ 已启用
```

## 📝 最常用的5个命令

### 1. 查看所有定时任务
```bash
crontab -l
```

### 2. 编辑定时任务
```bash
crontab -e
```

### 3. 查看最新日志
```bash
ls -lt /Users/didi/Data/dnn_model/logs/daily_job_*.log | head -1 | awk '{print $NF}' | xargs tail -50
```

### 4. 手动运行脚本
```bash
cd /Users/didi/dnn_model/factor_engineering
./run_daily_factor_processing.sh
```

### 5. 备份和恢复任务
```bash
# 备份
crontab -l > ~/crontab_backup.txt

## ⏰ 修改执行时间

编辑 crontab：
```bash
crontab -e
```

**cron 时间格式**: `分 时 日 月 周 命令`

**常用示例**：
```bash
# 每天晚上20:30
30 20 * * * /path/to/script.sh

# 每天晚上21:00
0 21 * * * /path/to/script.sh

# 每天早上6:00
0 6 * * * /path/to/script.sh

# 每周一早上9:00
0 9 * * 1 /path/to/script.sh
```

## 📊 查看结果

### 查看处理结果
```bash
ls -lt /Users/didi/Data/dnn_model/enhanced/enhanced_factors_csv_*/
```

### 查看失败股票
```bash
cat /Users/didi/dnn_model/factor_engineering/log/failed_summary_*.txt
```

## 🚨 紧急停止

```bash
# 备份后删除
crontab -l > ~/crontab_backup.txt
crontab -r
```

## 💡 提示

- **定时系统**: cron（Mac 和 Linux 通用）
- **日志位置**: `/Users/didi/Data/dnn_model/logs/`
- **查看任务**: `crontab -l`
- **编辑任务**: `crontab -e`
- **执行脚本**: `/Users/didi/dnn_model/factor_engineering/run_daily_factor_processing.sh`
