"""
日志工具模块

提供统一的日志配置和获取功能
"""

import logging
from typing import Optional


# 日志格式常量
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def get_logger(name: str, level: Optional[int] = None) -> logging.Logger:
    """
    获取配置好的日志器

    Args:
        name: 日志器名称（通常使用 __name__）
        level: 日志级别（可选，默认使用全局配置）

    Returns:
        配置好的Logger实例

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("这是一条日志消息")
    """
    logger = logging.getLogger(name)

    # 如果指定了级别，则设置
    if level is not None:
        logger.setLevel(level)

    # 如果logger还没有handler，添加一个
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT)
        )
        logger.addHandler(handler)

    return logger


def setup_logging(level: int = logging.INFO) -> None:
    """
    配置全局日志

    Args:
        level: 日志级别（默认INFO）

    Example:
        >>> import logging
        >>> setup_logging(logging.DEBUG)  # 设置为DEBUG级别
    """
    logging.basicConfig(
        level=level,
        format=LOG_FORMAT,
        datefmt=LOG_DATE_FORMAT
    )
