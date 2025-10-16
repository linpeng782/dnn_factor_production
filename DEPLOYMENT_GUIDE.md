# 云平台部署指南

## 📦 部署前准备

### 1. 本地需要推送的文件

```
factor_engineering/
├── *.py                          # 所有Python代码
├── factor_config.yaml            # 配置文件
├── run_daily_factor_processing.sh  # 执行脚本
├── requirements.txt              # 依赖列表
├── README.md                     # 项目说明
├── CRON_GUIDE.md                 # 定时任务指南
├── DEPLOYMENT_GUIDE.md           # 本文档
└── .gitignore                    # Git忽略文件
```

### 2. 不需要推送的文件

```
❌ /Users/didi/Library/LaunchAgents/  # Mac系统配置
❌ peterdidi/                         # 虚拟环境
❌ __pycache__/                       # Python缓存
❌ *.pyc                              # 编译文件
❌ log/*.txt                          # 日志文件
❌ *.log                              # 日志文件
```

---

## 🚀 云服务器部署步骤

### 步骤1: 克隆代码

```bash
# SSH登录云服务器
ssh username@server-ip

# 创建工作目录
mkdir -p /home/username/projects
cd /home/username/projects

# 克隆代码
git clone git@gitlab.company.com:your-username/factor_engineering.git
cd factor_engineering
```

### 步骤2: 创建虚拟环境

```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 验证安装
python -c "import rqdatac; print('✅ 依赖安装成功')"
```

### 步骤3: 配置路径

#### 3.1 修改 `run_daily_factor_processing.sh`

```bash
nano run_daily_factor_processing.sh
```

修改以下变量：
```bash
# 原始（Mac本地）
PROJECT_DIR="/Users/didi/dnn_model/factor_engineering"
VENV_NAME="peterdidi"
LOG_DIR="/Users/didi/Data/dnn_model/logs"

# 修改为（云服务器）
PROJECT_DIR="/home/username/projects/factor_engineering"
VENV_NAME="venv"
LOG_DIR="/data/factor_engineering/logs"
```

#### 3.2 修改 `config.py`

```bash
nano config.py
```

修改数据路径：
```python
# 原始（Mac本地）
DATA_ROOT = "/Users/didi/Data"

# 修改为（云服务器）
DATA_ROOT = "/data"  # 根据实际情况调整
```

#### 3.3 创建必要的目录

```bash
# 创建日志目录
mkdir -p /data/factor_engineering/logs

# 创建数据目录
mkdir -p /data/dnn_model/raw/日线后复权及常用指标csv
mkdir -p /data/dnn_model/enhanced

# 设置权限
chmod 755 run_daily_factor_processing.sh
```

### 步骤4: 配置米筐API（重要）

#### 方式1: 使用环境变量（推荐）

```bash
# 编辑 ~/.bashrc
nano ~/.bashrc

# 添加以下内容
export RQ_USERNAME="your_rq_username"
export RQ_PASSWORD="your_rq_password"

# 保存后重新加载
source ~/.bashrc
```

然后修改 `rq_api.py`:
```python
import os

def init_rq_api(
    username=os.getenv("RQ_USERNAME"),
    password=os.getenv("RQ_PASSWORD")
):
    # ... 其他代码
```

#### 方式2: 直接修改代码（不推荐）

```bash
nano rq_api.py
```

修改账号密码（注意：不要推送到Git）

### 步骤5: 测试运行

```bash
# 手动运行一次测试
./run_daily_factor_processing.sh

# 检查日志
tail -100 /data/factor_engineering/logs/daily_job_*.log
```

### 步骤6: 设置定时任务（Linux cron）

```bash
# 编辑 crontab
crontab -e

# 添加定时任务
# 格式: 分 时 日 月 周 命令
30 20 * * * /home/username/projects/factor_engineering/run_daily_factor_processing.sh >> /data/factor_engineering/logs/cron.log 2>&1
```

**常用时间设置**:
```bash
# 每天晚上20:30
30 20 * * * /path/to/script.sh

# 每天早上6:00
0 6 * * * /path/to/script.sh

# 每周一早上9:00
0 9 * * 1 /path/to/script.sh

# 每月1号凌晨2:00
0 2 1 * * /path/to/script.sh
```

### 步骤7: 验证定时任务

```bash
# 查看已设置的定时任务
crontab -l

# 查看cron服务状态
systemctl status cron  # Ubuntu/Debian
# 或
systemctl status crond  # CentOS/RHEL

# 查看cron日志
tail -f /var/log/cron  # CentOS/RHEL
# 或
tail -f /var/log/syslog | grep CRON  # Ubuntu/Debian
```

---

## 🔍 云服务器 vs 本地 Mac 对比

| 项目 | Mac 本地 | 云服务器 |
|------|----------|----------|
| **定时任务系统** | launchd | cron |
| **配置文件位置** | `~/Library/LaunchAgents/` | `crontab -e` |
| **虚拟环境** | `peterdidi` | `venv` |
| **项目路径** | `/Users/didi/dnn_model/` | `/home/username/projects/` |
| **数据路径** | `/Users/didi/Data/` | `/data/` |
| **日志路径** | `/Users/didi/Data/dnn_model/logs/` | `/data/factor_engineering/logs/` |
| **Python** | 系统自带或Homebrew | 系统自带 |

---

## 📝 配置文件模板

### 云服务器版 `run_daily_factor_processing.sh`

```bash
#!/bin/bash

# 云服务器配置
PROJECT_DIR="/home/username/projects/factor_engineering"
VENV_NAME="venv"
LOG_DIR="/data/factor_engineering/logs"

# 创建日志目录
mkdir -p "$LOG_DIR"

# 生成日志文件名
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="$LOG_DIR/daily_job_$TIMESTAMP.log"

# 记录开始
echo "========================================" | tee -a "$LOG_FILE"
echo "任务开始时间: $(date)" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"

# 进入项目目录
cd "$PROJECT_DIR" || exit 1

# 激活虚拟环境
source "$VENV_NAME/bin/activate" 2>&1 | tee -a "$LOG_FILE"

# 运行脚本
python feval_batch_factor_processing.py 2>&1 | tee -a "$LOG_FILE"

EXIT_CODE=$?

# 记录结束
echo "========================================" | tee -a "$LOG_FILE"
echo "任务结束时间: $(date)" | tee -a "$LOG_FILE"
echo "退出代码: $EXIT_CODE" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"

exit $EXIT_CODE
```

### 云服务器版 `config.py` 修改

```python
# 数据根目录 - 云服务器路径
DATA_ROOT = "/data"

# 数据路径
RAW_DATA_DIR = os.path.join(DATA_ROOT, "dnn_model", "raw", "日线后复权及常用指标csv")
ENHANCED_DATA_DIR = os.path.join(DATA_ROOT, "dnn_model", "enhanced", "enhanced_factors_csv")
CACHE_DIR = os.path.join(DATA_ROOT, "dnn_model", "cache")
REPORTS_DIR = os.path.join(DATA_ROOT, "dnn_model", "comparison_reports")
```

---

## 🔐 安全建议

### 1. 不要在代码中硬编码密码

```python
# ❌ 不推荐
def init_rq_api(username="13522652015", password="123456"):

# ✅ 推荐
import os
def init_rq_api(
    username=os.getenv("RQ_USERNAME"),
    password=os.getenv("RQ_PASSWORD")
):
```

### 2. 使用 .gitignore 保护敏感文件

```gitignore
# 密码配置
secrets.yaml
.env

# 日志文件
*.log
log/*.txt

# 数据文件
*.csv
*.parquet
```

### 3. 设置合适的文件权限

```bash
# 脚本可执行
chmod 755 run_daily_factor_processing.sh

# 配置文件只读
chmod 644 config.py

# 日志目录可写
chmod 755 /data/factor_engineering/logs
```

---

## 🐛 常见问题

### Q1: cron 任务没有执行

**检查步骤**:
```bash
# 1. 确认cron服务运行
systemctl status cron

# 2. 查看cron日志
tail -f /var/log/cron

# 3. 确认脚本权限
ls -l run_daily_factor_processing.sh

# 4. 手动运行测试
./run_daily_factor_processing.sh
```

### Q2: 虚拟环境找不到

**解决方案**:
```bash
# 使用绝对路径
source /home/username/projects/factor_engineering/venv/bin/activate
```

### Q3: 米筐API连接失败

**检查步骤**:
```bash
# 1. 检查网络
ping api.ricequant.com

# 2. 检查环境变量
echo $RQ_USERNAME
echo $RQ_PASSWORD

# 3. 手动测试
python -c "from rqdatac import init; init('user', 'pass')"
```

---

## 📊 监控和维护

### 日志清理脚本

```bash
# 创建清理脚本
cat > /home/username/scripts/cleanup_logs.sh << 'EOF'
#!/bin/bash
# 删除30天前的日志
find /data/factor_engineering/logs -name "*.log" -mtime +30 -delete
echo "日志清理完成: $(date)"
EOF

chmod +x /home/username/scripts/cleanup_logs.sh

# 添加到crontab（每月1号执行）
0 2 1 * * /home/username/scripts/cleanup_logs.sh
```

### 磁盘空间监控

```bash
# 检查磁盘使用
df -h /data

# 检查目录大小
du -sh /data/factor_engineering/*
```

---

## 📞 技术支持

部署遇到问题时，请提供：
1. 云服务器系统版本: `cat /etc/os-release`
2. Python版本: `python --version`
3. 错误日志: 最近的日志文件内容
4. 定时任务配置: `crontab -l`
