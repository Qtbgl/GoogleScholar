import asyncio
import traceback
from scholarly import scholarly, ProxyGenerator

from data import api_config
from log_config import logger

# 配置代理
pg = ProxyGenerator()
succeed = pg.SingleProxy(api_config.ipfoxy_proxy_auth)
logger.debug(f'SingleProxy设置succeed = {succeed}')
if not succeed:
    raise Exception('scholarly setting Proxy failed')

# success = pg.SingleProxy(http = <your http proxy>, https = <your https proxy>)
scholarly.use_proxy(pg, secondary_proxy_generator=pg)


class QueryItem:
    name: str
    pages: int
    year_low: int
    year_high: int
    min_cite: int

    def __init__(self, name, pages, year_low=None, year_high=None, min_cite=None):
        self.name = name
        self.pages = pages
        self.year_low = year_low
        self.year_high = year_high
        self.min_cite = min_cite

    def __str__(self):
        return str(self.__dict__)


class ByScholarly:
    def __init__(self, logger):
        self.logger = logger

    def parse_pub(self, json_obj):
        pub = json_obj
        author = ', '.join(pub['bib']['author'])
        return {
            'cut': pub['bib']['abstract'],
            'url': pub['pub_url'],
            'author': author,
            'title': pub['bib']['title'],
            'num_citations': pub['num_citations'],
            'eprint_url': pub.get('eprint_url'),
            'raw_pub': pub,
        }

    async def fill_bibtex(self, pub):
        pub['BibTeX'] = {'link': None, 'string': None}

        # 通过原始pub对象获取
        raw_pub = pub['raw_pub']
        if 'url_scholarbib' in raw_pub:
            pub['BibTeX']['link'] = 'https://scholar.google.com' + raw_pub['url_scholarbib']
        else:
            pub['BibTeX']['link'] = None

        try:
            bib_str = await asyncio.to_thread(scholarly.bibtex, raw_pub)
            pub['BibTeX']['string'] = bib_str
        except Exception as e:
            self.logger.error('scholarly库获取bibtex失败\n' + traceback.format_exc())
            return False

        return True

    async def query_scholar(self, item: QueryItem):
        """
        :return: 一次生成最多10篇文章
        """
        pages = item.pages
        # 从第0页开始
        i = 0
        pubs = []
        # 遍历生成器，结束时自动退出
        async for res in SearchPubsAsync(item):
            pub = self.parse_pub(res)
            pubs.append(pub)
            if len(pubs) == 10:  # 每隔一页
                full_page = pubs
                pubs = []  # 重新装载
                yield full_page

                i += 1
                if i >= pages:  # debug
                    break

        # 结束生成器


class QueryScholarlyError(Exception):
    pass


class SearchPubsAsync:
    def __init__(self, item: QueryItem):
        self.item = item

    def __aiter__(self):
        item = self.item
        name = self.item.name
        # 创建生成器
        self.q = scholarly.search_pubs(name, year_low=item.year_low, year_high=item.year_high)
        return self

    def next_to_anext(self):
        try:
            return next(self.q)
        except StopIteration:
            raise StopAsyncIteration  # 异步退出信号
        except Exception as e:
            logger.error(traceback.format_exc())
            raise QueryScholarlyError(f'scholarly爬取谷歌异常 {e}')

    async def __anext__(self):
        value = await asyncio.to_thread(self.next_to_anext)
        return value
