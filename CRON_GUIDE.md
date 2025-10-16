# 定时任务管理指南（cron 版本）

## 当前配置

- **定时系统**: cron（Mac 和 Linux 通用）
- **执行时间**: 每天晚上 20:30（8:30 PM）
- **执行脚本**: `/Users/didi/dnn_model/factor_engineering/run_daily_factor_processing.sh`
- **日志目录**: `/Users/didi/Data/dnn_model/logs/`

## 常用管理命令

### 1. 查看所有定时任务

```bash
crontab -l
```

输出示例：
```
# 每天晚上20:30执行因子数据处理
30 20 * * * /Users/didi/dnn_model/factor_engineering/run_daily_factor_processing.sh >> /Users/didi/Data/dnn_model/logs/cron.log 2>&1
```

### 2. 编辑定时任务

```bash
crontab -e
```

### 3. 删除所有定时任务

```bash
crontab -r
```

### 4. 手动运行脚本（测试用）

```bash
/Users/didi/dnn_model/factor_engineering/run_daily_factor_processing.sh
```

### 5. 查看 cron 日志

```bash
# Mac 系统日志
tail -f /var/log/system.log | grep cron

# 或查看脚本输出日志
tail -f /Users/didi/Data/dnn_model/logs/cron.log
```

## 修改执行时间

### 编辑 crontab

```bash
crontab -e
```

### cron 时间格式

```
分 时 日 月 周 命令
*  *  *  *  *  command
```

**常用时间设置示例**：

```bash
# 每天晚上20:30
30 20 * * * /path/to/script.sh

# 每天晚上21:00（9:00 PM）
0 21 * * * /path/to/script.sh

# 每天早上6:00
0 6 * * * /path/to/script.sh

# 每天中午12:00
0 12 * * * /path/to/script.sh

# 每周一早上9:00
0 9 * * 1 /path/to/script.sh

# 每月1号凌晨2:00
0 2 1 * * /path/to/script.sh

# 每小时执行一次
0 * * * * /path/to/script.sh
```

### 时间字段说明

```
字段1: 分钟 (0-59)
字段2: 小时 (0-23)
字段3: 日期 (1-31)
字段4: 月份 (1-12)
字段5: 星期 (0-7, 0和7都代表周日)
```

## 查看日志

### 1. 查看最新的任务日志

```bash
ls -lt /Users/didi/Data/dnn_model/logs/daily_job_*.log | head -1
```

### 2. 查看日志内容

```bash
# 查看最新日志
tail -100 /Users/didi/Data/dnn_model/logs/daily_job_*.log

# 实时查看日志（如果任务正在运行）
tail -f /Users/didi/Data/dnn_model/logs/daily_job_*.log
```

### 3. 查看 launchd 系统日志

```bash
# 标准输出
cat /Users/didi/Data/dnn_model/logs/launchd_stdout.log

# 错误输出
cat /Users/didi/Data/dnn_model/logs/launchd_stderr.log
```

## 手动运行脚本

如果需要手动运行（不等定时任务）：

```bash
cd /Users/didi/dnn_model/factor_engineering
./run_daily_factor_processing.sh
```

## 故障排查

### 问题1：任务没有执行

**检查步骤**：
1. 确认任务已加载：`launchctl list | grep com.didi.factor`
2. 检查配置文件语法：`plutil ~/Library/LaunchAgents/com.didi.factor.daily.plist`
3. 查看系统日志：`cat /Users/didi/Data/dnn_model/logs/launchd_stderr.log`

### 问题2：任务执行失败

**检查步骤**：
1. 查看任务日志：`ls -lt /Users/didi/Data/dnn_model/logs/daily_job_*.log | head -1`
2. 手动运行脚本测试：`./run_daily_factor_processing.sh`
3. 检查虚拟环境是否正常：`source ../peterdidi/bin/activate && python --version`

### 问题3：权限问题

```bash
# 确保脚本有执行权限
chmod +x /Users/didi/dnn_model/factor_engineering/run_daily_factor_processing.sh

# 确保日志目录存在
mkdir -p /Users/didi/Data/dnn_model/logs
```

## 临时禁用任务

如果需要临时停止定时任务（比如系统维护）：

### 方法1：注释掉任务

```bash
crontab -e
```

在任务前加 `#` 注释：
```bash
# 30 20 * * * /Users/didi/dnn_model/factor_engineering/run_daily_factor_processing.sh
```

### 方法2：删除所有任务

```bash
# 备份当前任务
crontab -l > ~/crontab_backup.txt

# 删除所有任务
crontab -r

# 需要时恢复
crontab ~/crontab_backup.txt
```

## 系统重启后

cron 任务会在系统重启后自动加载，无需手动操作。

## 注意事项

1. **Mac 必须开机**：定时任务只在 Mac 开机时执行
2. **网络连接**：确保有网络连接（米筐API需要）
3. **磁盘空间**：定期清理旧日志文件
4. **数据备份**：重要数据定期备份

## 日志清理

建议每月清理一次旧日志：

```bash
# 删除30天前的日志
find /Users/didi/Data/dnn_model/logs -name "daily_job_*.log" -mtime +30 -delete
```

## 联系支持

如有问题，请检查：
1. 任务日志文件
2. launchd 系统日志
3. Python 脚本输出
