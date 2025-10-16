#!/bin/bash

#############################################
# 每日因子数据处理脚本
# 功能：自动处理股票因子数据
#############################################

# 配置部分
PROJECT_DIR="/Users/didi/dnn_model/factor_engineering"
VENV_NAME="peterdidi"
LOG_DIR="/Users/didi/Data/dnn_model/logs"

# 创建日志目录
mkdir -p "$LOG_DIR"

# 生成日志文件名（带时间戳）
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="$LOG_DIR/daily_job_$TIMESTAMP.log"

# 记录开始时间
echo "========================================" | tee -a "$LOG_FILE"
echo "任务开始时间: $(date)" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"

# 进入项目目录
cd "$PROJECT_DIR" || exit 1
echo "当前目录: $(pwd)" | tee -a "$LOG_FILE"

# 激活虚拟环境
echo "激活虚拟环境: $VENV_NAME" | tee -a "$LOG_FILE"
source "../$VENV_NAME/bin/activate" 2>&1 | tee -a "$LOG_FILE"

if [ $? -ne 0 ]; then
    echo "错误: 无法激活虚拟环境" | tee -a "$LOG_FILE"
    exit 1
fi

# 运行因子处理脚本
echo "开始处理因子数据..." | tee -a "$LOG_FILE"

# 使用今天的日期作为数据截止日期
TODAY=$(date +"%Y%m%d")
echo "数据截止日期: $TODAY" | tee -a "$LOG_FILE"

# 运行批处理程序（处理所有股票）
python run_batch_factor_processing.py --date "$TODAY" 2>&1 | tee -a "$LOG_FILE"

EXIT_CODE=$?

# 记录结束时间
echo "========================================" | tee -a "$LOG_FILE"
echo "任务结束时间: $(date)" | tee -a "$LOG_FILE"
echo "退出代码: $EXIT_CODE" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"

# 发送通知（可选）
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ 任务成功完成" | tee -a "$LOG_FILE"
    # Mac 系统通知
    osascript -e 'display notification "因子数据处理完成" with title "定时任务成功"'
else
    echo "❌ 任务失败" | tee -a "$LOG_FILE"
    # Mac 系统通知
    osascript -e 'display notification "因子数据处理失败，请检查日志" with title "定时任务失败"'
fi

exit $EXIT_CODE
