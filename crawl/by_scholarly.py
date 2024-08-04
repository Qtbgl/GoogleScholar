import traceback

from scholarly import scholarly, ProxyGenerator
from scholarly._proxy_generator import MaxTriesExceededException


class QueryItem:
    name: str
    pages: int
    min_cite: int
    params: dict

    def __init__(self, name, pages=None, min_cite=None, params=None):
        """
        :param name:
        :param pages: 最大查询文章个数
        :param params: 谷歌学术查询参数，字典格式
        """
        self.name = name
        self.pages = pages
        self.min_cite = min_cite
        self.params = params if params else {}

    def __str__(self):
        return str(self.__dict__)


class ByScholarly:
    def __init__(self, logger):
        self.logger = logger

    def query_pubs(self, name, params):
        search_query = scholarly.search_pubs(name, **params)
        for pub in search_query:
            yield {
                'cut': pub['bib']['abstract'],
                'url': pub['pub_url'],
                'author': pub['bib']['author'],
                'title': pub['bib']['title'],
                'num_citations': pub['num_citations'],
                'bibtex': scholarly.bibtex(pub),
                'eprint_url': pub.get('eprint_url'),
            }

    def query_scholar(self, item: QueryItem):
        """
        :return: 一次生成最多10篇文章
        """
        name = item.name
        params = item.params
        # 创建查询
        i = 0  # 第0页开始
        pubs = []
        try:
            for pub in self.query_pubs(name, params):  # 调用生成器
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
            raise self.QueryScholarlyError(f'scholarly访问问题:{e}')

        # 结束生成器

    class QueryScholarlyError(Exception):
        pass
