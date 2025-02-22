import asyncio
import traceback

from spider import AsyncSpider
from urllib.parse import urlparse

from crawl.by_scholarly import fill_bibtex
from llm.AskGpt import AskGpt
from llm.process_html_for_gpt import process_html
from run.context1 import RunnerConfig
from run.pipline1 import LoggingPubCrawl
from data import api_config


class QuitAbstract(Exception):
    pass


class FillPub1:
    def __init__(self, config: RunnerConfig, writer: LoggingPubCrawl):
        self.config = config
        self.writer = writer

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
            self.writer.mark_error(pub, f'爬取摘要失败: {e}')
            # 吸收此类型异常
        except asyncio.CancelledError:
            logger.debug(f'取消摘要任务 #{task_id}')
            self.writer.mark_error(pub, f'取消摘要任务 #{task_id}')
            raise
        except Exception as e:
            logger.error(f'摘要任务失败 {type(e)} {e} #{task_id}')
            raise

    async def _scrape_url(self, url, max_tries=2):
        logger = self.config.logger
        spider = self.config.spider

        for i in range(max_tries):
            params = {'proxy_enabled': True, "store_data": False, 'metadata': False, 'request': 'smart'}
            async for data in spider.scrape_url(url, params):
                if isinstance(data, list) and len(data):
                    item = data[0]
                    if item['error']:  # 具体区分spider的错误
                        raise QuitAbstract(f"spider接口访问出错 {item['error']}")
                    elif not (200 <= item['status'] < 300):
                        raise QuitAbstract(f"spider接口爬取{item['status']} {item['url']}")

                    return item
                else:
                    logger.error(f'spider.scrape_url返回结果异常 尝试{i} {data}')

        raise QuitAbstract(f'spider.scrape_url返回结果异常 {url}')

    async def _fill_abstract(self, pub):
        """
        等待时间: spider未知
        GPT询问时间: 不超过60s
        """
        logger = self.config.logger
        page_url = pub['url']
        if not page_url:
            raise QuitAbstract('缺少网页地址')

        ps = urlparse(page_url)
        if 'pdf' in ps.path.lower():
            raise QuitAbstract('网页是pdf请直接下载')
        if 'sciencedirect.com' in ps.netloc:
            raise QuitAbstract('sciencedirect网站反爬')
        if 'ieee.org' in ps.netloc:
            raise QuitAbstract('ieee网站需要浏览器上加载')

        # title = pub['title']
        cut = pub['cut']
        # spider-cloud请求超时处理
        try:
            item = await self._scrape_url(page_url, 2)
        except asyncio.TimeoutError as e:
            raise QuitAbstract(f'spider-cloud请求超时 {e}')

        try:
            html_str = item['content']
            gpt = AskGpt(timeout=60)
            # 访问GPT，提取结果
            web_txt = process_html(html_str)
            # 限制token
            max_len = 2 * 64000  # 最长支持128000个token，每个token > 2字符
            if len(web_txt) > max_len:
                logger.debug(f'截断web_txt {len(web_txt)} 太长的部分 #{pub["task_id"]}')
                web_txt = web_txt[:max_len] + ' ...'

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
            self.writer.mark_error(pub, f'取消bibtex任务 #{task_id}')
            raise
        except Exception as e:
            logger.error(f'bibtex获取失败 #{task_id} {e}')
            self.writer.mark_error(pub, f'bibtex获取失败: {e}')
            # 不抛出
