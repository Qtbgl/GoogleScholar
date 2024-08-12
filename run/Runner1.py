import asyncio
import re
import time
import traceback

from parse.gpt_do_page_text import GptDoPageText
from record.Record1 import Record1
from crawl.by_scholarly import ByScholarly, QueryItem
from crawl.by_nodiver import Crawl


class Runner1:
    def __init__(self, crawl: Crawl, record: Record1, logger):
        # 依赖对象
        self.crawl = crawl
        self.record = record
        self.logger = logger

    async def run(self, item):
        async with self.crawl:
            async with self.record:
                await self.finish(item)

    async def finish(self, item: QueryItem):
        # 创建查询
        self.logger.info(f'任务查询 {item}')
        self.record.set_pages(item.pages)
        source = ByScholarly(self.logger)
        try:
            # for every 10 pubs
            for pubs in source.query_scholar(item):
                # 爬取网页
                self.logger.info(f'准备异步爬取pubs {len(pubs)}')
                tasks = [self.fetch_page(pub) for pub in pubs]
                await asyncio.gather(*tasks)  # 异步浏览器爬取
        except KeyboardInterrupt:
            raise
        except ByScholarly.QueryScholarlyError as e:
            if len(self.record.cand_pubs):
                pass
            else:
                raise e
        except Exception as e:
            self.logger.error('未预料的异常' + '\n' + traceback.format_exc())
            raise Exception(f'发生异常，中断爬取 {e}')

        # 处理内容
        self.logger.info(f'准备异步请求GPT处理pages {len(self.record.cand_pubs)}')
        tasks = [self.handle_page(pub) for pub in self.record.cand_pubs]
        await asyncio.gather(*tasks)  # 假设异常已在协程中处理

        # 不返回结果

    async def fetch_page(self, pub):
        try:
            keywords = pub['title'].split()
            html_str = await self.crawl.fetch_page(pub['url'], keywords=keywords[:4])
            pub['page'] = html_str
            self.record.success_to_fetch_page(pub)
        except Exception as e:
            # 浏览器爬取出错
            self.logger.error(traceback.format_exc())
            pub['error'] = {'when': 'nodriver爬取网页'}  # 标记这个pub
            self.record.fail_to_fetch_page(pub)

    async def handle_page(self, pub):
        parse = GptDoPageText(self.logger)
        flag = False
        try:
            url = pub['url']
            html_str = pub['page']
            self.logger.info(f'GPT in > {url}')

            # 异步请求
            # 访问GPT，提取结果
            abstract = await parse.get_abstract(pub['cut'], html_str)
            pub['abstract'] = abstract

            self.logger.info(f'GPT out > {url}')

            self.record.success_to_handle_page(pub)
            flag = True
        except GptDoPageText.GPTQueryError as e:
            pub['error'] = {'when': '处理内容', 'detail': str(e)}
        except GptDoPageText.GPTAnswerError as e:
            pub['error'] = {'when': '处理内容', 'detail': str(e)}
        except Exception as e:
            self.logger.error('未预料的异常' + '\n' + traceback.format_exc())
            pub['error'] = {'when': '处理内容'}
        finally:
            if not flag:
                self.record.fail_to_handle_page(pub)
