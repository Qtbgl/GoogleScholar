def display_pub_url(pubs):
    rows = ["#{} {}".format(pub['task_id'], pub['url']) for pub in pubs]
    rows_output = '\n\t'.join(rows)  # 生成输出字符串
    return f'{len(pubs)} pubs: \n\t{rows_output}'


class LoggerAuto:
    def __init__(self, logger, name):
        self.logger = logger
        self.name = name

    def __enter__(self):
        self.logger.debug(f'进入{self.name}')
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        import asyncio
        if exc_type is asyncio.CancelledError:
            self.logger.debug(f'取消{self.name}')
        else:
            self.logger.debug(f'退出{self.name }')