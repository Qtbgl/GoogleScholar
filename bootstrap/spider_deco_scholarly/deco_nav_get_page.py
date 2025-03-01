from bootstrap.spider_get_page import spider_scrape_url, SpiderCrawlFailed

from scholarly._navigator import Navigator
__nav_get_page = getattr(Navigator, '_get_page')


def nav_get_page(self, pagerequest: str, premium: bool = False) -> str:
    if not pagerequest:
        raise Exception(f'网页请求为空, {pagerequest}, on {self}._get_page')

    url = pagerequest

    # spider方面的
    params = {'proxy_enabled': True, "store_data": False, 'metadata': False, 'request': 'http'}
    content = spider_scrape_url(url, params)
    has_captcha = self._requests_has_captcha(content)
    if has_captcha:
        raise SpiderCrawlFailed(f"spider爬取结果has_captcha {url}")

    return content


# 使用反射修改类的方法

setattr(Navigator, '_get_page', nav_get_page)
print('scholarly已修改', __nav_get_page, __file__)
