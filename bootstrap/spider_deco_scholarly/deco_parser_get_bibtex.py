from bootstrap.spider_get_page import SpiderCrawlFailed

from scholarly.publication_parser import PublicationParser
__parser_get_bibtex = getattr(PublicationParser, '_get_bibtex')


def parser_get_bibtex(self, bib_url) -> str:
    global __parser_get_bibtex
    bibtex_url = __parser_get_bibtex(self, bib_url)  # 先到各引用链接的页面，找到bibtex_url
    if not bibtex_url:
        raise SpiderCrawlFailed(f'文章引用页面爬取有误，找不到bibtex_url {bib_url}')

    return bibtex_url


# 使用反射修改类的方法
setattr(PublicationParser, '_get_bibtex', parser_get_bibtex)
print('scholarly已修改', __parser_get_bibtex, __file__)
