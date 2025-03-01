from scholarly import scholarly, MaxTriesExceededException

from bootstrap.spider_get_page import SpiderCrawlFailed
from config import spider_config

from scholarly.publication_parser import _SearchScholarIterator
__search_load_url = getattr(_SearchScholarIterator, '_load_url')


def search_load_url(self, url: str):
    # 应对谷歌学术方面的出错（检索、bibtex时）
    global __search_load_url
    max_tries = spider_config.search_max_tries
    example = None
    for _ in range(max_tries):  # TODO: 多次尝试在异步并行下取消不了的问题
        try:
            return __search_load_url(url)
        except SpiderCrawlFailed as e:
            example = e
            pass  # 吸收

    raise MaxTriesExceededException(f"spider爬取尝试{max_tries}次都失败 {example} {url}")


# 使用反射修改类的方法

setattr(_SearchScholarIterator, '_load_url', search_load_url)
print('scholarly已修改', __search_load_url, __file__)
