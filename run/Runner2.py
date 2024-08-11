import asyncio
import re
import time
import traceback
import urllib.parse

from bs4 import BeautifulSoup

from crawl.by_researchgate import ByResearchGate
from parse.gpt_page_text import GPTPageParse
from record.Record2 import Record2
from crawl.by_serpdog import BySerpdog, QueryItem
from crawl.by_nodiver import Crawl


class Runner2:
    def __init__(self, crawl: Crawl, record: Record2, logger):
        # 依赖对象
        self.crawl = crawl
        self.record = record
        self.logger = logger
        self.source = BySerpdog(logger)

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
                # 补充数据任务
                self.logger.info(f'准备异步爬取pubs {len(pubs)}')
                tasks = [self.fill_pub(pub, item) for pub in pubs]  # 假设协程内已处理异常
                await asyncio.gather(*tasks)

        except KeyboardInterrupt:
            raise
        except Exception as e:
            self.logger.error('未预料的异常' + '\n' + traceback.format_exc())
            raise Exception(f'发生异常，中断爬取 {str(e)}')

        # 不返回结果

    async def fill_pub(self, pub, item):
        # 爬取bibtex
        try:
            await self.fill_abstract(pub)
            # 摘要获取后，再bibtex
            await self.fill_bibtex(pub, item)
            # 成功爬取
            self.record.success_fill(pub)
        except self.QuitFillPubError as e:
            # 取消fill这一篇pub
            self.logger.error(str(e))
            pub['error'] = 'Error in fill_pub: ' + str(e)
            self.record.fail_to_fill(pub)
        except Exception as e:
            # 所有异常不抛出
            self.logger.error(traceback.format_exc())
            pub['error'] = 'Error in fill_pub: ' + str(e)
            self.record.fail_to_fill(pub)

    async def fill_bibtex(self, pub, item):
        bib_link = await self.source.get_bibtex_link(pub, item)
        try:
            html_str = await self.crawl.fetch_page(bib_link, wait_sec=1)
            string = html_str
            match = re.search(r'@(\w+)\{(.*\})', string, re.DOTALL)
            if not match:
                self.logger.error('尝试用serpdog爬取BibTeX ' + bib_link)
                # 尝试用serpdog api抓取
                string = await self.source.get_bibtex_string(bib_link, item)
                pub['BibTeX'] = {'link': bib_link, 'string': string}
            else:
                pub['BibTeX'] = {'link': bib_link, 'string': match.group()}

        except Exception as e:
            self.logger.error(traceback.format_exc())
            pub['BibTeX'] = {'link': bib_link, 'string': None}
            raise self.QuitFillPubError(f'BibTeX未正常获取 {str(e)}')

    class QuitFillPubError(Exception):
        pass

    async def fill_abstract(self, pub: dict):
        """
        :param pub:
        :return: 任何一个环节失败，则抛出异常
        """
        # 先爬取pub的网页
        try:
            page_url = pub['url']
            if await self.crawl.is_page_pdf(page_url):
                raise Crawl.PageIsPdfError()

            keywords = pub['title'].split()
            # 长时间等待
            html_str = await self.crawl.fetch_page(page_url, wait_sec=10, keywords=keywords[:4])
            pub['page'] = html_str
        except (Crawl.CaptchaPageError, Crawl.WaitPageError, Crawl.PageIsPdfError) as e:
            self.logger.error(f'直接爬取网页失败 {e}')
            try:
                # 尝试其他方式获取网页
                rg = ByResearchGate(self.logger, self.crawl)
                await rg.fill_page(pub)

            except ByResearchGate.FillPageError as e:  # 针对特定的异常
                raise self.QuitFillPubError(e)

        # 再访问GPT，提取摘要
        try:
            parse = GPTPageParse(self.logger)
            url = pub['url']
            html_str = pub['page']

            self.logger.info(f'GPT in > {url}')

            abstract = await parse.get_abstract(pub['cut'], html_str)
            pub['abstract'] = abstract

            self.logger.info(f'GPT out > {url}')

        except (GPTPageParse.GPTQueryError, GPTPageParse.GPTAnswerError) as e:
            raise self.QuitFillPubError(e)
