from spider import Spider, AsyncSpider
from data import api_config

spider = Spider(api_key=api_config.spider_api_key)  # 暂时在全局


def deco_nav_get_page():
    """
    只能一次修改，否则方法会无限递归
    """
    from scholarly._navigator import Navigator
    # _get_page = getattr(Navigator, '_get_page')  # (不用)原先方法

    def _new_get_page(self, pagerequest: str, premium: bool = False) -> str:
        # print(f'hack in {self}._get_page, {pagerequest} {premium}')
        url = pagerequest
        scraped_data = spider.scrape_url(url)
        item = scraped_data[0]
        if item['error']:  # TODO: 异常情况考虑
            raise Exception(item)

        # print(item['url'], item['status'], item['costs'])
        return item['content']

    # 使用反射修改类的方法
    setattr(Navigator, '_get_page', _new_get_page)
