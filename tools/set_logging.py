import logging


def setup_console_logging(name, level='debug'):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)  # 同名的logger均设置

    console_handler = logging.StreamHandler()
    console_handler.setLevel({'info': logging.INFO, 'debug': logging.DEBUG}[level.lower()])

    formatter = logging.Formatter(f'%(name)s %(asctime)s %(levelname)s %(message)s', datefmt='%m-%d %H:%M:%S')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)


def setup_file_loging(name: str, log_file):
    # # 创建日志目录
    # if not os.path.exists(log_dir):
    #     os.makedirs(log_dir)

    # 设置name对应的日志
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)  # 同名的logger均设置

    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter(f'%(name)s %(asctime)s %(levelname)s %(message)s', datefmt='%m-%d %H:%M:%S')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)


def remove_log_handler(name):
    logger = logging.getLogger(name)

    # 遍历并移除所有处理器
    for handler in logger.handlers[:]:  # 使用切片以避免修改列表时出错
        logger.removeHandler(handler)
        handler.close()  # 关闭处理器以释放资源
