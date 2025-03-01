import logging
import os
from datetime import datetime


def setup_console_logging(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter(f'%(name)s %(asctime)s %(levelname)s %(message)s', datefmt='%m-%d %H:%M:%S')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)


def setup_file_loging(name: str, log_dir='data/log'):
    # 创建日志目录
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # 创建日志文件名
    log_file = os.path.join(log_dir, f"{datetime.now().strftime('%Y-%m-%d-%H%M%S')}_{name}.log")

    # 设置name对应的日志
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter(f'%(name)s %(asctime)s %(levelname)s %(message)s', datefmt='%m-%d %H:%M:%S')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
