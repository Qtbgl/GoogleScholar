import traceback

from scholarly import Publication

from bootstrap.spider_get_page import SpiderCrawlFailed

from scholarly.publication_parser import PublicationParser
__parser_bibtex = getattr(PublicationParser, 'bibtex')
__code = 'parsed_bib = remap_bib(bibtexparser.loads(bibtex,parser).entries[-1], _BIB_MAPPING, _BIB_DATATYPES)'


def parser_bibtex(self, publication: Publication) -> str:
    try:
        return __parser_bibtex(self, publication)   # 会调用到deco_parser_get_bibtex.py的代码
    except IndexError as e:
        global __code
        if __code in traceback.format_exc():
            from bootstrap import spider_get_page
            raise SpiderCrawlFailed(f'谷歌学术bibtex页面结果不对 {spider_get_page.last_data}')


# 使用反射修改类的方法
setattr(PublicationParser, 'bibtex', parser_bibtex)
print(f'已修改scholarly的类方法 {__parser_bibtex} 在文件 {__file__}')
