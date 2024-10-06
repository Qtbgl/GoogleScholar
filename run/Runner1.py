import asyncio
import traceback

from crawl.by_scholarly import QueryScholarlyError, get_bib_link
from run.ScrapePub1 import ScrapePub1
from run.pipline1 import ReadResult, RunnerConfig, WriteResult

from tools.bib_tools import add_abstract, del_abstract


class Result:
    def __init__(self):
        self.pages = None
        self.all_pubs = []
        self._i = None

    def set_pages(self, pages):
        self.pages = pages

    def next_id(self):
        i = self._i
        self._i += 1
        return i


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
        scraper = ScrapePub1(self.config, self)
        tasks = [asyncio.create_task(scraper.producer()), asyncio.create_task(scraper.consumer())]
        try:
            await asyncio.gather(*tasks)
        except QueryScholarlyError as e:
            logger.error(f'scholarly异常 {traceback.format_exc()}')
            raise e
        except Exception as e:
            logger.error(f'未知异常 {e}')
            raise Exception(f'发生异常，中断爬取 {e}')
        finally:
            # 取消未完成的任务
            for task in tasks:
                task.cancel()
                # 等待所有任务完成取消
            await asyncio.gather(*tasks, return_exceptions=True)
        # 不返回结果

    def get_progress(self):
        if not self.result.pages:
            return 0.0

        total = 10 * self.result.pages
        registered = len(self.result.all_pubs)
        return registered / total

    def deliver_pubs(self):
        all_pubs = self.result.all_pubs
        if len(all_pubs) == 0:
            return None

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

            obj['error'] = '; '.join(pub['error']) if len(pub['error']) else None
            results.append(obj)

        # 所有已有的结果
        return results

    def register_new(self, pub):
        pub['task_id'] = self.result.next_id()
        pub['error'] = []
        self.result.all_pubs.append(pub)

    def mark_error(self, pub, error):
        pub['error'].append(error)
