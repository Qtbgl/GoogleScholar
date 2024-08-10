import asyncio
import re
import time
import traceback
import urllib.parse

from bs4 import BeautifulSoup

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
            task1 = self.fill_bibtex(pub, item)
            task2 = self.fill_abstract(pub)
            await asyncio.gather(task1, task2)
            # 成功爬取
            self.record.success_fill(pub)
        except Exception as e:
            # 任何异常取消fill这一篇pub
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
                raise Exception('爬取到的不是BibTeX ' + bib_link)

            pub['BibTeX'] = {'link': bib_link, 'string': match.group()}
        except Exception as e:
            self.logger.error(traceback.format_exc())
            # 不抛出异常
            pub['BibTeX'] = {'link': bib_link, 'string': None}

    async def get_extra_links(self, pub: dict):
        title = pub['title']
        payload = {'q': title, }
        url = 'https://www.researchgate.net/search/publication'  # 需要网络支持
        url = f"{url}?{urllib.parse.urlencode(payload)}"
        kws = ("Discover the world's scientific knowledge",)
        text = await self.crawl.fetch_page(url, wait_sec=5, keywords=kws)

        # scraping
        soup = BeautifulSoup(text, 'html.parser')
        container = soup.find("div", class_="search-indent-container")
        # 文本相似匹配
        links = []
        for a in container.find_all("a", string=lambda s: s and title.lower() in s.lower()):
            # 提取链接 URL
            url = 'https://www.researchgate.net/' + a["href"]
            links.append(url)

        return links

    async def fill_page_try2nd(self, pub):
        # 尝试其他方式获取网页
        try:
            links = await self.get_extra_links(pub)
            assert len(links) > 0
        except Exception as e:
            raise Exception('获取pub其他版本的网页失败')

        flag = False
        for link in links:
            try:
                self.logger.debug(f'{pub["title"]} 尝试其他版本 {link}')
                page_url = link
                if 'pdf' in page_url.lower():
                    raise self.PageIsPdfError()

                kw1 = pub['title'].split()
                kw2 = [s for s in pub['cut'].split() if re.match(r'^[a-zA-Z]+$', s)]
                keywords = kw1[:4] + kw2[:12]  # 用标题和摘要勉强匹配

                html_str = await self.crawl.fetch_page(page_url, keywords)
                pub['page'] = html_str
                flag = True
                break
            except self.PageIsPdfError as e:
                continue
            except Crawl.WaitPageError as e:
                continue
            except Exception as e:
                raise

        if not flag:
            raise Exception('获取pub其他版本的网页失败')

    class PageIsPdfError(Exception):
        pass

    async def fill_abstract(self, pub: dict):
        """
        :param pub:
        :return: 任何一个环节失败，则抛出异常
        """
        # 先爬取pub的网页
        try:
            page_url = pub['url']
            if 'pdf' in page_url.lower():
                raise self.PageIsPdfError()
            keywords = pub['title'].split()
            html_str = await self.crawl.fetch_page(page_url, keywords[:4])
            pub['page'] = html_str
        except Crawl.WaitPageError as e:
            await self.fill_page_try2nd(pub)
        except self.PageIsPdfError as e:
            await self.fill_page_try2nd(pub)
        except Exception as e:
            raise

        # 再访问GPT，提取摘要
        try:
            parse = GPTPageParse(self.logger)
            url = pub['url']
            html_str = pub['page']

            self.logger.info(f'GPT in > {url}')

            abstract = await parse.get_abstract(pub['cut'], html_str)
            pub['abstract'] = abstract

            self.logger.info(f'GPT out > {url}')

        except GPTPageParse.GPTQueryError as e:
            raise
        except GPTPageParse.GPTAnswerError as e:
            raise
        except Exception as e:
            raise
