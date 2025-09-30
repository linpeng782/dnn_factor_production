"""
因子处理配置模块
统一管理路径配置、YAML配置加载和工具函数
"""

import os
import yaml

# ==================== 路径配置 ====================
# 数据根目录 - 遵循数据和代码分离的开发范式
DATA_ROOT = "/Users/didi/Data"

# 数据路径
RAW_DATA_DIR = os.path.join(DATA_ROOT, "dnn_model", "raw", "日线后复权及常用指标csv")
ENHANCED_DATA_DIR = os.path.join(DATA_ROOT, "dnn_model", "enhanced", "enhanced_factors_csv")
CACHE_DIR = os.path.join(DATA_ROOT, "dnn_model", "cache")
REPORTS_DIR = os.path.join(DATA_ROOT, "dnn_model", "comparison_reports")


# ==================== 配置加载 ====================
def get_config():
    """
    从YAML文件加载配置信息
    
    Returns:
        dict: 配置字典，包含dataset_end_date、test_mode、max_workers等
    """
    config_path = os.path.join(os.path.dirname(__file__), "factor_config.yaml")
    
    try:
        with open(config_path, "r", encoding="utf-8") as file:
            config = yaml.safe_load(file)
        return config
    except Exception as e:
        raise RuntimeError(f"无法加载配置文件: {config_path}, 错误: {e}")


