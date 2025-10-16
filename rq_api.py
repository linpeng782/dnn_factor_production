"""
米筐 API 统一导入模块

将所有米筐API的导入集中在这里，使项目独立于 factor_utils
"""

import warnings
from loguru import logger

# 过滤米筐API的警告信息
warnings.filterwarnings("ignore")

# 导入米筐API
from rqdatac import *
from rqfactor import *
from rqfactor import Factor
from rqfactor.extension import *

# 米筐API初始化标志
_rq_initialized = False


def init_rq_api(username="13522652015", password="123456"):
    """
    初始化米筐API

    Args:
        username: 米筐账号
        password: 米筐密码

    Returns:
        bool: 初始化是否成功
    """
    global _rq_initialized

    if _rq_initialized:
        logger.debug("米筐API已初始化，跳过重复初始化")
        return True

    try:
        init(username, password)
        _rq_initialized = True
        logger.success("米筐API初始化成功")
        return True
    except Exception as e:
        logger.error(f"米筐API初始化失败: {e}")
        return False


def is_initialized():
    """检查米筐API是否已初始化"""
    return _rq_initialized
