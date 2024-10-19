import asyncio
import traceback

from spider import AsyncSpider

from crawl.by_scholarly import fill_bibtex
from llm.AskGpt import AskGpt
from llm.gpt_do_page_text import process_html
from run.pipline1 import RunnerConfig, WriteResult
from data import api_config


class QuitAbstract(Exception):
    pass


class FillPub1:
    def __init__(self, config: RunnerConfig, writer: WriteResult):
        self.config = config
        self.writer = writer
        self.spider = AsyncSpider(api_key=api_config.spider_api_key)

    async def fill_abstract(self, pub):
        """
        限制异步访问数量
        """
        logger = self.config.logger
        task_id = pub['task_id']
        logger.debug(f'进入摘要任务 #{task_id}')
        try:
            await self._fill_abstract(pub)
            logger.debug(f'摘要任务成功 #{task_id}')
        except QuitAbstract as e:
            logger.error(f'摘要任务失败 {e} #{task_id}')
            self.writer.mark_error(pub, '爬取摘要失败')
            # 吸收此类型异常
        except asyncio.CancelledError:
            logger.debug(f'取消摘要任务 #{task_id}')
            raise
        except Exception as e:
            logger.error(f'摘要任务失败 {type(e)} {e} #{task_id}')
            raise

    async def _fill_abstract(self, pub):
        """
        等待时间: spider未知
        GPT询问时间: 不超过60s
        """
        logger = self.config.logger
        page_url = pub['url']

        if 'pdf' in page_url.lower():
            raise QuitAbstract('网页是pdf')

        title = pub['title']
        cut = pub['cut']
        item = None
        async for data in self.spider.scrape_url(page_url):
            item = data[0]
            if item['error'] or item['status'] != 200:
                raise QuitAbstract(f"spider爬取失败: {item['status']}, {item['error']}")

        try:
            html_str = item['content']
            gpt = AskGpt(timeout=60)
            # 访问GPT，提取结果
            web_txt = process_html(html_str)
            query_txt = '\n'.join([
                '以下是一段不完整的摘要：', str(cut),
                '以下是该文章/出版物的网页内容：', web_txt,
                '请从上面的网页内容中找出完整的摘要，直接以英文输出摘要'
            ])
            pub['abstract'] = await gpt.ask_gpt(query_txt)
        except (AskGpt.GPTQueryError, AskGpt.GPTAnswerError) as e:
            raise QuitAbstract(e)

    async def fill_bibtex(self, pub):
        """
        爬取时间: spider未知
        """
        logger = self.config.logger
        task_id = pub['task_id']
        logger.debug(f'进入bibtex任务 #{task_id}')
        try:
            await fill_bibtex(pub)
            logger.debug(f'bibtex任务成功 #{task_id}')
        except asyncio.CancelledError:
            logger.info(f'取消bibtex任务 #{task_id}')
            raise
        except Exception as e:
            logger.error(f'bibtex获取失败 {e}')
            self.writer.mark_error(pub, 'bibtex获取失败')
            # 不抛出
