import asyncio
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
            for pubs in self.source.query_scholar(item):
                # 爬取网页
                self.logger.info(f'准备异步爬取pubs {len(pubs)}')
                tasks = [self.fill_pub(pub, item) for pub in pubs]
                await asyncio.gather(*tasks)  # 异步浏览器爬取

        except asyncio.CancelledError as e:
            self.logger.error('任务取消' + '\n' + traceback.format_exc())
            raise
        except ByScholarly.QueryScholarlyError as e:
            self.logger.error(f'scholarly出问题 {e}')
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
            # 直接获取网页上的摘要
            succeed = await self.fill_abstract(pub)
            if not succeed:
                pub['abstract'] = None
                # 只记录，不退出

            # 暂时直接阻塞地获取bibtex
            if await self.source.fill_bibtex(pub):
                self.record.success_fill(pub)
            else:
                pub['error'] = 'BibTeX未正常获取'
                self.record.fail_to_fill(pub)

        except asyncio.CancelledError:
            raise
        except Exception as e:
            # 所有异常不抛出
            self.logger.error(traceback.format_exc())
            pub['error'] = 'Error in fill_pub: ' + str(e)
            self.record.fail_to_fill(pub)

    async def fill_abstract(self, pub):
        try:
            page_url = pub['url']
            if await self.crawl.is_page_pdf(page_url):
                raise Crawl.PageIsPdfError()

            keywords = pub['title'].split()
            # 暂时等待很长一段时间
            html_str = await self.crawl.fetch_page(page_url, wait_sec=10, keywords=keywords[:4])

        except (Crawl.CaptchaPageError, Crawl.WaitPageError, Crawl.PageIsPdfError) as e:
            self.logger.error(f'直接爬取摘要失败 {e}')
            return False

        gpt = GptDoPageText(self.logger)
        try:
            # 访问GPT，提取结果
            pub['abstract'] = await gpt.get_abstract(pub['cut'], html_str)
            self.logger.info(f'直接爬取到摘要 {pub["url"]}')
        except (gpt.GPTQueryError, gpt.GPTAnswerError) as e:
            self.logger.error(f'直接爬取摘要失败 {e}')
            return False

        return True
