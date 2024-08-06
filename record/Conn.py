class Conn:
    def __init__(self, logger):
        self.logger = logger

    async def __aenter__(self):
        # 建立连接
        # self.logger.info('已连接数据库')
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # 关闭数据库
        # self.logger.info('准备关闭数据库')
        pass
