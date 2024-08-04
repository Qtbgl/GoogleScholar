import asyncio
import re
import time
import traceback

from parse.gpt_page_text import GPTPageParse
from record.Record import Record
from crawl.by_serpdog import BySerpdog, QueryItem
from crawl.by_nodiver import Crawl


class Runner2:
    def __init__(self, crawl: Crawl, record: Record, logger):
        # 依赖对象
        self.crawl = crawl
        self.record = record
        self.logger = logger
        self.source = BySerpdog(logger)

    async def run(self, item: QueryItem):
        # 创建查询
        self.logger.info(f'任务查询 {item}')
        all_pubs = []
        try:
            # for every 10 pubs
            async for pubs in self.source.query_scholar(item):
                # 加入至结果
                all_pubs.extend(pubs)
                # 补充数据任务
                self.logger.info(f'准备异步爬取pubs {len(pubs)}')
                tasks = [self.fill_pub(pub, item) for pub in pubs]  # 假设协程内已处理异常
                await asyncio.gather(*tasks)

        except KeyboardInterrupt:
            raise
        except Exception as e:
            self.logger.error('未预料的异常' + '\n' + traceback.format_exc())
            if len(all_pubs):
                return {'error': f'发生异常 {str(e)}'}
            else:
                return {'error': f'发生异常，中断查询 {str(e)}', 'pubs': all_pubs}

        # 返回结果
        results = [{
            'abstract': pub.get('abstract'),
            'pub_url': pub['url'],
            'title': pub['title'],
            'author': pub['author'],
            'cited': pub['cited'],
            'BibTeX': pub.get('BibTeX'),
            'error': pub.get('error'),
        } for pub in all_pubs]
        return {'pubs': results}

    async def fill_pub(self, pub, item):
        # 爬取bibtex
        try:
            task1 = self.fill_bibtex(pub, item)
            task2 = self.fill_abstract(pub)
            await asyncio.gather(task1, task2)

        except Exception as e:
            # 任何异常取消fill这一篇pub
            self.logger.error(traceback.format_exc())
            pub['error'] = 'Error in fill_pub: ' + str(e)

    async def fill_bibtex(self, pub, item):
        bib_link = await self.source.get_bibtex_link(pub, item)
        try:
            html_str = await self.crawl.fetch_page(bib_link, wait_sec=1)
            string = html_str
            if not re.search(r'@(\w+)\{(.*\})', string, re.DOTALL):
                raise Exception('爬取到的不是BibTeX ' + bib_link)

            pub['BibTeX'] = {'link': bib_link, 'string': string}
        except Exception as e:
            self.logger.error(traceback.format_exc())
            # 不抛出异常
            pub['BibTeX'] = {'link': bib_link, 'string': None}

    async def fill_abstract(self, pub: dict):
        # 先爬取pub的网页
        try:
            keywords = pub['title'].split()
            html_str = await self.crawl.fetch_page(pub['url'], keywords[:4])
            pub['page'] = html_str
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
