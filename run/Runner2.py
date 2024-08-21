import asyncio
import re
import time
import traceback
import urllib.parse

from bs4 import BeautifulSoup

from crawl.by_researchgate import ByResearchGate
from crawl.by_sema import BySema
from parse.gpt_do_html import GptDoHtml
from parse.gpt_do_page_text import GptDoPageText
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

        except asyncio.CancelledError as e:
            self.logger.error('任务取消' + '\n' + traceback.format_exc())
            raise
        except Exception as e:
            self.logger.error('未预料的异常' + '\n' + traceback.format_exc())
            raise Exception(f'发生异常，中断爬取 {str(e)}')

        # 不返回结果

    async def fill_pub(self, pub, item):
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
            # 先获取摘要
            succeed = await self.fill_abstract_directly(pub)

            if not succeed:
                succeed = await self.fill_abstract_by_rg(pub)

            if not succeed:
                succeed = await self.fill_abstract_by_sema(pub)

            if not succeed:
                pub['error'] = '摘要无法获取'
                self.record.fail_to_fill(pub)
                return  # 结束后续环节

            # 摘要获取后，再bibtex
            if await self.fill_bibtex(pub, item):
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

    async def fill_abstract_directly(self, pub):
        try:
            page_url = pub['url']
            if await self.crawl.is_page_pdf(page_url):
                raise Crawl.PageIsPdfError()

            keywords = pub['title'].split()
            # 长时间等待
            html_str = await self.crawl.fetch_page(page_url, wait_sec=10, keywords=keywords[:4])

        except (Crawl.CaptchaPageError, Crawl.WaitPageError, Crawl.PageIsPdfError) as e:
            self.logger.error(f'直接爬取摘要失败 {e}')
            return False

        gpt = GptDoPageText(self.logger)
        try:
            pub['abstract'] = await gpt.get_abstract(pub['cut'], html_str)
            self.logger.info(f'直接爬取到摘要 {pub["url"]}')
        except (gpt.GPTQueryError, gpt.GPTAnswerError) as e:
            self.logger.error(f'直接爬取摘要失败 {e}')
            return False

        return True

    async def fill_abstract_by_rg(self, pub):
        # 尝试其他方式获取网页
        # 用reseachgate查询
        rg = ByResearchGate(self.logger, self.crawl)
        try:
            links = await rg.get_links(pub)
        except rg.GetLinkError as e:
            self.logger.error(f'Reseachgate获取其他版本链接失败')
            return False

        gpt = GptDoPageText(self.logger)
        for link in links:
            try:
                self.logger.info(f'尝试Reseachgate的其他版本 {link}')
                html_str = await rg.get_html(link, pub)
                # 测试GPT提取
                pub['abstract'] = await gpt.get_abstract(pub['cut'], html_str)
                self.logger.info(f'成功通过Reseachgate获取到其他版本')
                return True

            except Crawl.PageIsPdfError as e:
                continue
            except (Crawl.WaitPageError, Crawl.CaptchaPageError) as e:
                self.logger.error(str(e))  # 打印原因
                continue
            except (gpt.GPTQueryError, gpt.GPTAnswerError) as e:
                self.logger.error(str(e))
                continue

        self.logger.info(f'Reseachgate爬取摘要失败')
        return False

    async def fill_abstract_by_sema(self, pub):
        sema = BySema(self.logger, self.crawl)
        try:
            paper_html = await sema.get_paper_html(pub)
            self.logger.info(f'成功在Semantic Scholar上找到相同文献 {len(paper_html)}')
        except sema.GetPaperError as e:
            self.logger.error(f'Semantic Scholar获取网页内容失败 {e}')
            return False

        gpt = GptDoHtml(self.logger)
        for html_str in paper_html:
            try:
                pub['abstract'] = await gpt.get_abstract(html_str)
                self.logger.info(f'成功通过Semantic Scholar获取到摘要')
                return True
            except (gpt.GPTQueryError, gpt.GPTAnswerError) as e:
                self.logger.error(str(e))
                continue

        self.logger.error(f'Semantic Scholar爬取摘要失败')
        return False

    async def fill_bibtex(self, pub, item):
        pub['BibTeX'] = {'link': None, 'string': None}
        try:
            # 获取链接
            bib_link = await self.source.get_bibtex_link(pub, item)
            pub['BibTeX']['link'] = bib_link
            # 获取内容
            html_str = await self.crawl.fetch_page(bib_link, wait_sec=1)
            string = html_str
            match = re.search(r'@(\w+)\{(.*\})', string, re.DOTALL)
            if not match:
                self.logger.error('尝试用serpdog爬取BibTeX ' + bib_link)
                # 尝试用serpdog api抓取
                string = await self.source.get_bibtex_string(bib_link, item)
                pub['BibTeX']['string'] = string
            else:
                pub['BibTeX']['string'] = match.group()

            # 成功返回
            return True

        except asyncio.CancelledError:
            raise
        except BySerpdog.SerpdogError as e:
            self.logger.error(e)
            return False
        except Exception as e:
            self.logger.error(traceback.format_exc(chain=False))
            return False
