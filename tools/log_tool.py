import logging
import os
from datetime import datetime


def create_logger(name: str, log_time: datetime, log_dir='data/log'):
    """创建一个 Logger，并将日志输出到对应的日志文件。"""
    # 创建日志目录
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # 设置日志文件名
    log_file = os.path.join(log_dir, f"{log_time.strftime('%Y-%m-%d-%H%M%S')}_{name}.log")

    # 创建 Logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)  # 设置日志级别为 DEBUG

    # 创建文件处理器
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)  # 设置文件处理器的日志级别为 DEBUG  ~~INFO~~

    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)  # 设置控制台处理器的日志级别为 DEBUG

    # 创建日志格式
    # formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    formatter = logging.Formatter('%(name)s %(asctime)s %(levelname)s %(message)s',
                                  datefmt='%m-%d %H:%M:%S')
    # app 10-04 17:41:08 INFO 新连接 ws://127.0.0.1:8000/query1/pulmonary nodule classification
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    # 添加处理器到 Logger
    if not logger.hasHandlers():
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger


# 使用示例
if __name__ == "__main__":
    # 创建一个 Logger 实例
    app_logger = create_logger("app", datetime.now())
    app_logger.debug("This is a debug message from app logger.")
    app_logger.info("This is an info message from app logger.")

    # 创建另一个 Logger 实例
    error_logger = create_logger("error", datetime.now())
    error_logger.error("This is an error message from error logger.")
    error_logger.critical("This is a critical message from error logger.")
