import asyncio
import traceback

from parse.gpt_do_page_text import GptDoPageText
from record.Record1 import Record1
from crawl.by_scholarly import ByScholarly, QueryItem, QueryScholarlyError
from crawl.by_nodiver import Crawl
from tools.nodriver_tools import wait_for_text


class Runner1:
    def __init__(self, crawl: Crawl, record: Record1, logger):
        # 依赖对象
        self.crawl = crawl
        self.record = record
        self.logger = logger
        self.source = ByScholarly(self.logger)

    async def run(self, item):
        async with self.crawl:
            async with self.record:
                await self.finish(item)

    async def finish(self, item: QueryItem):
        # 创建查询
        self.logger.info(f'任务查询 {item}')
        self.record.set_pages(item.pages)
        try:
            # for every 10 pubs
            async for pubs in self.source.query_scholar(item):
                # 爬取网页
                self.logger.info(f'准备异步爬取pubs {len(pubs)}')
                tasks = [self.fill_pub(pub, item) for pub in pubs]
                await asyncio.gather(*tasks)  # 异步浏览器爬取

        except asyncio.CancelledError as e:
            self.logger.error('任务取消' + '\n' + traceback.format_exc())
            raise
        except QueryScholarlyError as e:
            self.logger.error(e)
            raise e
        except Exception as e:
            self.logger.error('未预料的异常' + '\n' + traceback.format_exc())
            raise Exception(f'发生异常，中断爬取 {e}')

        # 不返回结果

    async def fill_pub(self, pub, item: QueryItem):
        min_cite = item.min_cite
        # 过滤引用数量
        if min_cite is not None and min_cite > 0:
            num_citations = pub.get('num_citations')
            if num_citations is None:
                pub['error'] = f'无引用数量信息'
                self.record.fail_to_fill(pub)
                return
            elif num_citations < min_cite:
                pub['error'] = f'引用数量不足 {pub["num_citations"]} < {min_cite}'
                self.record.fail_to_fill(pub)
                return

        try:
            # 异步执行两个任务
            task_fill_abstract = asyncio.create_task(self.fill_abstract(pub))
            task_fill_bibtex = asyncio.create_task(self.source.fill_bibtex(pub))

            succeed = await task_fill_abstract
            if not succeed:
                pub['abstract'] = None
                # 只记录，不退出

            succeed = await task_fill_bibtex
            if not succeed:
                pub['error'] = 'BibTeX未正常获取'
                self.record.fail_to_fill(pub)
                return

            self.record.success_fill(pub)

        except asyncio.CancelledError:
            raise
        except Exception as e:
            # 所有异常不抛出
            self.logger.error(traceback.format_exc())
            pub['error'] = 'Error in fill_pub: ' + str(e)
            self.record.fail_to_fill(pub)

    async def fill_abstract(self, pub):
        page_url = pub['url']
        if await self.crawl.is_page_pdf(page_url):
            self.logger.error(f'直接爬取摘要失败，网页是pdf')
            return False

        title = pub['title']
        page = await self.crawl.browser.get(page_url, new_tab=True)
        try:
            await page.wait(2)
            text = title[:20]  # 检查存在
            html_str = await wait_for_text(text, page, timeout=30)
        except asyncio.TimeoutError as e:
            self.logger.error(f'直接爬取摘要失败 {e} {page_url}')
            return False
        finally:
            await page.close()

        gpt = GptDoPageText(self.logger)
        try:
            # 访问GPT，提取结果
            pub['abstract'] = await gpt.get_abstract(pub['cut'], html_str)
            self.logger.info(f'直接爬取到摘要 {page_url}')
        except (gpt.GPTQueryError, gpt.GPTAnswerError) as e:
            self.logger.error(f'直接爬取摘要失败 {e} {page_url}')
            return False

        return True
