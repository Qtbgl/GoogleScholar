import asyncio
import os
import pickle
from datetime import datetime

from search_pub import query
from bootstrap import deco_scholarly
from set_logging import setup_console_logging, setup_file_loging

# 先装饰一下原本的scholarly库
deco_scholarly()

# 再设置一下日志
setup_console_logging('CrawlGoogleScholar', level='info')


class Query:
    def __init__(self):
        self.data = []

    async def main(self, **kwargs):
        # 创建日志文件名，在每一次任务上
        log_file = os.path.join('data/log', f"{datetime.now().strftime('%Y-%m-%d-%H%M%S')}.log")
        setup_file_loging('CrawlGoogleScholar', log_file)

        # 进入实际的query
        try:
            async for pub in query(**kwargs):
                self.data.append(pub)
        except Exception as e:
            print(f'query函数出错了 {e}')

        print(f'已获得 {len(self.data)} 篇论文')
        if len(self.data):
            print(f'正在保存 {len(self.data)} 篇文章的结果')
            self.save_data(log_file, kwargs)
            self.save_bibs()

    def save_data(self, log_file, kwargs):
        record = {
            'log_file': log_file,
            'kwargs': kwargs,
            'data': self.data
        }
        with open('data.pkl', 'wb') as f:
            pickle.dump(record, f)

    def save_bibs(self):
        pass
