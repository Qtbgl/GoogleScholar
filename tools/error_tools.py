import asyncio


class LoggerAuto:
    def __init__(self, logger, name):
        self.logger = logger
        self.name = name

    def __enter__(self):
        self.logger.debug(f'进入{self.name}')
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is asyncio.CancelledError:
            self.logger.debug(f'取消{self.name}')
        else:
            self.logger.debug(f'退出{self.name }')
