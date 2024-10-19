import asyncio
import traceback

from crawl.by_scholarly import query_scholar
from run.FillPub1 import FillPub1
from run.context1 import RunnerConfig
from run.pipline1 import WriteResult
from data import api_config

from tools.log_display_tool import display_pub_url


class ScrapePub1:
    def __init__(self, config: RunnerConfig, writer: WriteResult):
        self.config = config
        self.writer = writer
        self._pub_queue = asyncio.Queue()  # 等待填充队列
        self.fill_pub = FillPub1(config, writer)

    async def producer(self):
        logger = self.config.logger
        item = self.config.item
        queue = self._pub_queue
        try:
            async for pubs in query_scholar(item):
                for pub in pubs:
                    self.writer.register_new(pub)  # 加入到结果集中
                    await queue.put(pub)
                logger.debug(f'新搜索到的文献 {display_pub_url(pubs)}')

            await queue.put(None)  # 放入特殊标记，表示结束
        except asyncio.CancelledError:
            logger.debug(f'生产者传递取消异常')
            raise

    async def consumer(self):
        logger = self.config.logger
        queue = self._pub_queue
        try:
            while True:
                pub = await queue.get()  # 等待元素
                if pub is None:
                    queue.put_nowait(None)  # 放回特殊标记
                    break

                await self.process_pub(pub)
                queue.task_done()  # 本次处理周期结束
        except asyncio.CancelledError:
            logger.debug(f'消费者传递取消异常')
            raise

    async def process_pub(self, pub):
        logger = self.config.logger
        item = self.config.item
        min_cite = item.min_cite

        # 过滤引用数量
        if min_cite is not None and min_cite > 0:
            if pub.get('num_citations', 0) < min_cite:
                self.writer.mark_error(pub, '引用数量过滤')
                return

        # 创建任务
        tasks = [asyncio.create_task(self.fill_pub.fill_abstract(pub))]
        if not item.ignore_bibtex:
            tasks.append(asyncio.create_task(self.fill_pub.fill_bibtex(pub)))

        try:
            # 等待所有任务完成
            await asyncio.gather(*tasks)
        finally:
            for task in tasks:
                task.cancel()
            # 等待所有任务完成取消
            await asyncio.gather(*tasks, return_exceptions=True)
            logger.debug(f'退出文献填充任务 #{pub["task_id"]}')
