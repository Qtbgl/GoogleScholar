class Conn:
    async def __aenter__(self):
        # 建立连接
        print('连接数据库')
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # 关闭数据库
        print('关闭数据库')
