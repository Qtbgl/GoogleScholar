import asyncio
import time
import traceback

from parse.gpt_page_text import GPTPageParse
from record.Record import Record
from crawl.by_scholarly import ByScholarly, QueryItem
from crawl.by_nodiver import Crawl


class Runner1:
    def __init__(self, crawl: Crawl, record: Record, logger):
        # 依赖对象
        self.crawl = crawl
        self.record = record
        self.logger = logger

    async def run(self, item: QueryItem):
        # 创建查询
        self.logger.info(f'任务查询 {item}')
        all_pubs = []
        source = ByScholarly(self.logger)
        try:
            # for every 10 pubs
            for pubs in source.query_scholar(item):
                # 爬取网页
                self.logger.info(f'准备异步爬取pubs {len(pubs)}')
                tasks = [self.fetch_page(pub) for pub in pubs]
                pubs = await asyncio.gather(*tasks)  # 异步浏览器爬取
                all_pubs.extend(pubs)
        except KeyboardInterrupt:
            raise
        except ByScholarly.QueryScholarlyError as e:
            if len(all_pubs) == 0:  # 完全没获取到数据时
                return {'error': str(e)}

        except Exception as e:
            self.logger.error('未预料的异常' + '\n' + traceback.format_exc())
            return {'error': '发生异常，中断爬取', 'pubs': all_pubs}

        # 处理内容
        pubs_to_fill = [pub for pub in all_pubs if pub.get('error') is None]  # 处理一部分
        self.logger.info(f'准备异步请求GPT处理pages {len(pubs_to_fill)}')
        tasks = [self.handle_page(pub) for pub in pubs_to_fill]
        await asyncio.gather(*tasks)  # 假设异常已在协程中处理

        # 返回结果
        results = [{
            'abstract': pub.get('abstract'),
            'author': ' '.join(pub['author']),
            'title': pub['title'],
            'pub_url': pub['url'],
            'num_citations': pub['num_citations'],
            'BibTeX': pub['bibtex'],
            'error': pub.get('error'),
        } for pub in all_pubs]  # 所有已有的结果
        return {'pubs': results}

    async def fetch_page(self, pub):
        try:
            html_str = await self.crawl.fetch_page(pub['url'], pub['title'])
            pub['page'] = html_str
        except Exception as e:
            # 浏览器爬取出错
            self.logger.error(traceback.format_exc())
            pub['error'] = {'when': 'nodriver爬取网页'}  # 标记这个pub
        finally:
            return pub

    async def handle_page(self, pub):
        parse = GPTPageParse(self.logger)
        try:
            url = pub['url']
            html_str = pub['page']
            self.logger.info(f'GPT in > {url}')

            # 异步请求
            # 访问GPT，提取结果
            abstract = await parse.get_abstract(pub['cut'], html_str)
            pub['abstract'] = abstract

            self.logger.info(f'GPT out > {url}')
        except GPTPageParse.GPTQueryError as e:
            pub['error'] = {'when': '处理内容', 'detail': str(e)}
        except GPTPageParse.GPTAnswerError as e:
            pub['error'] = {'when': '处理内容', 'detail': str(e)}
        except Exception as e:
            self.logger.error('未预料的异常' + '\n' + traceback.format_exc())
            pub['error'] = {'when': '处理内容'}

        finally:
            return pub
