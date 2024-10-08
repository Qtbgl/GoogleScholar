import asyncio
import json
import traceback

from crawl.by_scholarly import query_scholar, fill_bibtex
from run.pipline1 import RunnerConfig, WriteResult
from data import api_config

from tools.pub_log_tool import display_pub_url


class ScrapePub1:
    def __init__(self, config: RunnerConfig, writer: WriteResult):
        self.config = config
        self.writer = writer
        self._pubs_queue = asyncio.Queue(maxsize=1)  # 缓存队列，提取准备下一次的文献
        self._bibtex_lock = asyncio.Semaphore(5)  # 请求锁，限制访问量

    async def producer(self):
        logger = self.config.logger
        item = self.config.item
        queue = self._pubs_queue

        async for pubs in query_scholar(item):
            for pub in pubs:
                self.writer.register_new(pub)  # 加入到结果集中
            logger.debug(f'新加入结果集 {display_pub_url(pubs)}')
            await queue.put(pubs)

        await queue.put(None)  # 放入特殊标记，表示结束

    async def consumer(self):
        logger = self.config.logger
        websocket = self.config.websocket
        queue = self._pubs_queue
        try:
            while True:
                pubs = await queue.get()
                if pubs is None:  # 检查特殊标记
                    logger.info(f'consumer已完成所有pubs的处理')
                    break

                await self.process_pubs(pubs)  # 异步浏览器爬取
                queue.task_done()  # 本次处理周期结束
        finally:
            # 所有任务都结束时
            if not websocket.closed:
                await websocket.close()

    async def process_pubs(self, pubs):
        logger = self.config.logger
        item = self.config.item
        min_cite = item.min_cite

        # 过滤引用数量
        if min_cite is not None and min_cite > 0:
            pubs_to_fill = []
            for pub in pubs:
                if pub.get('num_citations', 0) < min_cite:
                    self.writer.mark_error(pub, '引用数量过滤')
                else:
                    pubs_to_fill.append(pub)
            pubs = pubs_to_fill

        # 创建任务
        tasks = [asyncio.create_task(self.send_to_fill_abstract(pubs))]
        if not item.ignore_bibtex:
            for pub in pubs:
                tasks.append(asyncio.create_task(self.fill_bibtex(pub)))

        try:
            logger.debug(f'process_pubs 创建异步任务 {len(tasks)}')
            # 等待所有任务完成
            await asyncio.gather(*tasks)
        finally:
            for task in tasks:
                task.cancel()
            # 等待所有任务完成取消
            await asyncio.gather(*tasks, return_exceptions=True)

    async def send_to_fill_abstract(self, pubs):
        logger = self.config.logger
        websocket = self.config.websocket

        logger.info(f'准备调用子结点处理 {len(pubs)}')
        await websocket.send(json.dumps({'pubs': pubs}))

        message = await websocket.recv()
        obj = json.loads(message)
        if 'error' in obj:
            logger.error(f'子结点出错 {obj["error"]}')
            for pub in pubs:
                self.writer.mark_error(pub, '爬取摘要失败')
        else:
            logger.info(f'子结点处理完成')
            result = {pub['task_id']: pub for pub in obj['pubs']}
            for pub in pubs:
                pub['abstract'] = result[pub['task_id']].get('abstract')
                if not pub['abstract']:
                    self.writer.mark_error(pub, '爬取摘要失败')

    async def fill_bibtex(self, pub, tries=0):
        """
        scholarly每次爬取时间: 不超过60s
        总时间: <= 递归尝试 x min + 排队访问时间 (10/n -1)* x min
        """
        using_proxy = api_config.scholarly_use_proxy
        logger = self.config.logger
        succeed = False
        async with self._bibtex_lock:
            try:
                await asyncio.wait_for(fill_bibtex(pub), timeout=60)  # debug 防止一直等下去
                logger.debug(f'bibtex任务成功 #{pub["task_id"]}')
                succeed = True
            except asyncio.TimeoutError as e:
                logger.debug(f'bibtex获取超时,已尝试{tries + 1} #{pub["task_id"]}')
            except asyncio.CancelledError:
                logger.info(f'取消bibtex任务 #{pub["task_id"]}')
                raise

        if not succeed:
            if tries <= 0 and using_proxy:  # 最多尝试两次
                await self.fill_bibtex(pub, tries + 1)
            else:
                self.writer.mark_error(pub, 'bibtex获取失败')  # 确保只mark一次
