import asyncio
import time

from parse.gpt_page_text import get_abstract_by_gpt
from record.Record import Record
from crawl.by_serpdog import query_scholar, QueryItem
from crawl.by_nodiver import Crawl


class Runner2:
    def __init__(self, crawl: Crawl, record: Record):
        # 依赖对象
        self.crawl = crawl
        self.record = record

    async def run(self, item: QueryItem):
        # 创建查询
        print('任务查询', item)
        all_pubs = []
        try:
            # for every 10 pubs
            for pubs in query_scholar(item):
                # 爬取网页
                tasks = [self.fetch_page(pub) for pub in pubs]
                print(f'{time.strftime("%H:%M:%S")} 准备异步爬取pubs', len(pubs))
                pubs = await asyncio.gather(*tasks)  # 异步浏览器爬取
                all_pubs.extend(pubs)
        except KeyboardInterrupt:
            raise
        except Exception as e:
            print(f'{time.strftime("%H:%M:%S")} 发生异常，中断爬取')
            print(e)
            if len(all_pubs) == 0:
                return {'error': '查询失败:' + str(e)}  # 返回问题

        # 处理内容
        all_pubs = [pub for pub in all_pubs if pub.get('error') is None]
        print('准备异步请求GPT处理pages', len(all_pubs))
        if len(all_pubs):
            tasks = [self.handle_page(pub) for pub in all_pubs]
            all_pubs = await asyncio.gather(*tasks)
        else:
            return {'error': '查询失败'}

        # 返回结果
        results = [{
            'abstract': pub['abstract'],
            'pub_url': pub['url'],
            'title': pub['title'],
            'author': pub['author'],
            'cited': pub['cited'],
            'BibTeX': pub.get('BibTeX'),
            'error': pub.get('error'),
        } for pub in all_pubs]
        return results

    async def fetch_page(self, pub):
        try:
            html_str = await self.crawl.fetch_page(pub['url'], pub['title'])
            pub['page'] = html_str
        except Exception as e:
            pub['error'] = {'detail': str(e), 'when': '爬取网页'}
        finally:
            return pub

    async def handle_page(self, pub):
        try:
            url = pub['url']
            html_str = pub['page']
            print(f'{time.strftime("%H:%M:%S")} in >', url)

            # 异步请求
            # 访问GPT，提取结果
            abstract = await get_abstract_by_gpt(pub['cut'], html_str)
            pub['abstract'] = abstract

            print(f'{time.strftime("%H:%M:%S")} out >', url)

        except Exception as e:
            pub['abstract'] = None
            pub['error'] = {'detail': str(e), 'when': '处理内容'}

        finally:
            return pub
