# 从 launchd 迁移到 cron

## 为什么迁移？

✅ **统一性**: Mac 和 Linux 云服务器使用相同的定时任务系统  
✅ **简单性**: cron 配置更简单，一行命令搞定  
✅ **通用性**: 所有 Unix/Linux 系统都支持 cron  
✅ **可移植性**: 配置可以直接复制到云服务器

## 已完成的迁移

### 1. 卸载 launchd
```bash
✅ launchctl unload ~/Library/LaunchAgents/com.didi.factor.daily.plist
✅ 删除配置文件
```

### 2. 设置 cron
```bash
✅ 添加定时任务: 每天晚上 20:30
✅ 配置日志输出
```

### 3. 更新文档
```bash
✅ CRON_GUIDE.md - 完整管理指南
✅ QUICK_REFERENCE.md - 快速参考
✅ DEPLOYMENT_GUIDE.md - 部署指南
```

## 当前配置

```bash
# 查看当前定时任务
$ crontab -l

# 每天晚上20:30执行因子数据处理
30 20 * * * /Users/didi/dnn_model/factor_engineering/run_daily_factor_processing.sh >> /Users/didi/Data/dnn_model/logs/cron.log 2>&1
```

## 优势对比

| 特性 | launchd | cron |
|------|---------|------|
| **Mac 支持** | ✅ | ✅ |
| **Linux 支持** | ❌ | ✅ |
| **配置复杂度** | 高（XML文件） | 低（一行命令） |
| **学习成本** | 高 | 低 |
| **可移植性** | 差 | 好 |
| **文档资源** | 少 | 多 |

## 现在的工作流程

### 本地 Mac
```bash
# 1. 查看任务
crontab -l

# 2. 编辑任务
crontab -e

# 3. 手动运行
./run_daily_factor_processing.sh
```

### 云服务器（完全相同！）
```bash
# 1. 查看任务
crontab -l

# 2. 编辑任务
crontab -e

# 3. 手动运行
./run_daily_factor_processing.sh
```

## 下一步

现在本地和云服务器使用相同的定时任务系统，部署时只需：

1. 克隆代码
2. 修改路径配置
3. 复制 crontab 配置（一行命令）

✅ 完成！
