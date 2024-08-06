import traceback

from scholarly import scholarly, ProxyGenerator
from scholarly._proxy_generator import MaxTriesExceededException


class QueryItem:
    name: str
    pages: int
    year_low: int
    year_high: int

    def __init__(self, name, pages, year_low=None, year_high=None):
        self.name = name
        self.pages = pages
        self.year_low = year_low
        self.year_high = year_high

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
            'BibTeX': scholarly.bibtex(pub),
            'eprint_url': pub.get('eprint_url'),
        }

    def query_scholar(self, item: QueryItem):
        """
        :return: 一次生成最多10篇文章
        """
        name = item.name
        i = 0  # 第0页开始
        pubs = []
        try:
            q = scholarly.search_pubs(name, year_low=item.year_low, year_high=item.year_high)
            # 调用生成器
            for res in q:
                pub = self.parse_pub(res)
                pubs.append(pub)
                if len(pubs) == 10:  # 每隔一页
                    full_page = pubs
                    pubs = []  # 重新装载
                    yield full_page
                    # 新一页
                    i += 1
                    if i > item.pages:
                        break
        except MaxTriesExceededException as e:
            self.logger.error(traceback.format_exc())
            raise self.QueryScholarlyError(f'scholarly无法访问谷歌 {e}')

        # 结束生成器

    class QueryScholarlyError(Exception):
        pass
