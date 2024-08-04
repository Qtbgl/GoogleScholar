import asyncio
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

    async def run(self, item: QueryItem):
        # 创建查询
        self.logger.info(f'任务查询 {item}')
        all_pubs = []
        source = BySerpdog(self.logger)
        try:
            # for every 10 pubs
            for pubs in source.query_scholar(item):
                # 加入至结果
                all_pubs.extend(pubs)
                # 补充数据任务
                tasks = [self.fill_pub(pub, item, source) for pub in pubs]  # 假设协程内已处理异常
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

    async def fill_pub(self, pub, item, source: BySerpdog):
        # 爬取bibtex
        try:
            task1 = source.fill_bibtex(pub, item)
            task2 = self.fill_abstract(pub)
            await asyncio.gather(task1, task2)

        except Exception as e:
            # 任何异常取消fill这一篇pub
            self.logger.error(traceback.format_exc())
            pub['error'] = 'Error in fill_pub: ' + str(e)

    async def fill_abstract(self, pub: dict):
        # 先爬取pub的网页
        try:
            html_str = await self.crawl.fetch_page(pub['url'], pub['title'])
            pub['page'] = html_str
        except Exception as e:
            raise Exception('nodriver爬取网页出错') from e  # 让日志打印e

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
