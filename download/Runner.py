import asyncio
import traceback

from download.by_request import ByRequest
from download.context import Config


class Runner:
    def __init__(self, config: Config):
        # 依赖对象
        self.config = config

    async def finish(self):
        logger = self.config.logger
        logger.info(f'开始下载任务')
        pubs = self.config.pubs
        by = ByRequest(self.config)
        tasks = [by.download_pdf(pub) for pub in pubs]
        tasks = list(map(asyncio.create_task, tasks))
        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            logger.error('未预料的异常' + '\n' + traceback.format_exc())
            raise e

        result = [{
            'url': pub['url'],
            'file_remote': pub.get('file'),  # 文件取回名
            'error': pub.get('error'),
        } for pub in pubs]
        return result
