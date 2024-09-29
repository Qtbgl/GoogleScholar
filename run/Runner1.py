import asyncio
import traceback

from crawl.by_scholarly import query_scholar, QueryScholarlyError, get_bib_link
from run.FillPub1 import FillPub1
from run.pipline1 import ReadResult, RunnerConfig, WriteResult

from tools.bib_tools import add_abstract, del_abstract


class Result:
    def __init__(self):
        self.pages = None
        self.fail_pubs = []
        self.filled_pubs = []

    def set_pages(self, pages):
        self.pages = pages


class Runner1(ReadResult, WriteResult):
    def __init__(self, config: RunnerConfig):
        # 依赖对象
        self.config = config
        self.result = Result()

    async def finish(self):
        logger = self.config.logger
        item = self.config.item

        # 创建查询
        logger.info(f'任务查询 {item}')
        self.result.set_pages(item.pages)
        dealer = FillPub1(self.config, self)

        try:
            # for every 10 pubs
            async for pubs in query_scholar(item):
                # 爬取网页
                logger.info(f'准备异步爬取pubs {len(pubs)}')
                tasks = [dealer.fill_pub(pub) for pub in pubs]
                await asyncio.gather(*tasks)  # 异步浏览器爬取

        except QueryScholarlyError as e:
            logger.error(e)
            raise e
        except Exception as e:
            raise Exception(f'发生异常，中断爬取 {e}')

        # 不返回结果

    def get_progress(self):
        if not self.result.pages:
            return 0.0

        total = 10 * self.result.pages
        done = len(self.result.filled_pubs) + len(self.result.fail_pubs)
        return done / total

    def deliver_pubs(self):
        all_pubs = self.result.filled_pubs + self.result.fail_pubs
        item = self.config.item
        # 缺省值
        empty_bib = {'link': None, 'string': None}
        results = []
        # 所有已有的结果
        for pub in all_pubs:
            abstract = pub.get('abstract')
            obj = {
                'title': pub['title'],
                'author': pub['author'],
                'pub_year': pub['pub_year'],
                'pub_url': pub['url'],
                'abstract': abstract,
                'eprint_url': pub.get('eprint_url'),
                'num_citations': pub.get('num_citations', None),
            }
            # 加入bib
            if item.ignore_bibtex:
                obj['bib_link'] = get_bib_link(pub['raw_pub'])  # 为以后添加
            else:
                bib_link = pub.get('BibTeX', empty_bib).get('link')
                bib_raw = pub.get('BibTeX', empty_bib).get('string')
                # bib加入摘要
                if bib_raw and abstract:
                    bib_str = add_abstract(bib_raw, abstract)
                elif bib_raw and not abstract:
                    bib_str = del_abstract(bib_raw)
                else:
                    bib_str = None

                obj['bib_link'] = bib_link
                obj['bib_raw'] = bib_raw
                obj['bib'] = bib_str

            obj['error'] = pub.get('error')
            results.append(obj)

        # 所有已有的结果
        return results

    def fail_to_fill(self, pub, error):
        if pub.get('error'):
            if isinstance(pub['error'], list):
                pub['error'] = [error] + pub['error']  # 连接
            else:
                pub['error'] = [error, pub['error']]
        else:
            pub['error'] = error

        self.result.fail_pubs.append(pub)

    def success_fill(self, pub):
        self.result.filled_pubs.append(pub)
