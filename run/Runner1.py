import asyncio
import traceback
from collections import Counter

from crawl.by_scholarly import QueryScholarlyError, get_bib_link
from run.ScrapePub1 import ScrapePub1
from run.context1 import RunnerConfig
from run.pipline1 import ReadCrawlProgress, LoggingPubCrawl

from tools.bib_tool import add_abstract, del_abstract


class Runner1(ReadCrawlProgress, LoggingPubCrawl):
    def __init__(self, config: RunnerConfig):
        # 依赖对象
        self.config = config
        self.result = CrawlResult()
        self.multi_consumer = 20  # 设置异步爬取数

    async def finish(self):
        logger = self.config.logger
        item = self.config.item

        # 创建查询
        logger.info(f'任务查询 {item}')
        self.result.set_pages(item.pages)
        scraper = ScrapePub1(self.config, self)
        # 一个生产者 + 多个消费者
        tasks = [scraper.producer()] + [scraper.consumer() for i in range(self.multi_consumer)]
        tasks = list(map(asyncio.create_task, tasks))  # debug map只会遍历一次
        try:
            await asyncio.gather(*tasks)
        except QueryScholarlyError as e:
            logger.error(f'scholarly执行异常 {traceback.format_exc()}')
            raise e
        except Exception as e:
            logger.error(f'未知异常 {traceback.format_exc()}')
            raise Exception(f'发生异常，中断爬取 {e}')
        finally:
            # 取消未完成的任务
            for task in tasks:
                task.cancel()
                # 等待所有任务完成取消
            await asyncio.gather(*tasks, return_exceptions=True)
            logger.debug(f'所有任务（生产者，消费者等）已结束')
        # 不返回结果

    def get_progress(self):
        if not self.result.pages:
            return None

        total_expect = 10 * self.result.pages
        all_pubs = self.result.all_pubs
        searched = len(all_pubs)
        status_counter = Counter(pub['crawl_state'] for pub in all_pubs)
        return {
            'total_expect': total_expect,
            'searched': searched,
            'unfilled': status_counter['unfilled'],
            'completed': status_counter['completed'],
            'error_occurred': status_counter['error_occurred'],
        }

    def deliver_pubs(self):
        all_pubs = self.result.all_pubs
        if len(all_pubs) == 0:
            return None

        item = self.config.item
        # 缺省值
        empty_bib = {'link': None, 'string': None}
        results = []
        # 先排序
        all_pubs.sort(key=lambda x: x['task_id'])
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
                obj['bib_link'] = get_bib_link(pub)  # 为以后添加
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

            obj['error'] = '; '.join(pub['error']) if len(pub['error']) else None
            results.append(obj)

        # 所有已有的结果
        return results

    def register_new(self, pub):
        pub['task_id'] = self.result.next_id()
        pub['error'] = []
        pub['crawl_state'] = 'unfilled'
        self.result.all_pubs.append(pub)

    def mark_error(self, pub, error):
        pub['error'].append(error)
        pub['crawl_state'] = 'error_occurred'

    def mark_completed(self, pub):
        pub['crawl_state'] = 'completed'


class CrawlResult:
    def __init__(self):
        self.pages = None
        self.all_pubs = []
        self._i = 0

    def set_pages(self, pages):
        self.pages = pages

    def next_id(self):
        i = self._i
        self._i += 1
        return i
