from scholarly._navigator import Navigator
from spider import Spider
from data import api_config

# 存在于文件模块
spider = Spider(api_key=api_config.spider_api_key)


def _new_get_page(self, pagerequest: str, premium: bool = False) -> str:
    # print(f'hack in {self}._get_page, {pagerequest} {premium}')
    url = pagerequest
    scraped_data = spider.scrape_url(url)
    item = scraped_data[0]
    if item['error'] or item['status'] != 200:
        raise Exception(f"spider爬取出错: {item['status']}, {item['error']}")

    # print(item['url'], item['status'], item['costs'])
    return item['content']


# 使用反射修改类的方法
setattr(Navigator, '_get_page', _new_get_page)
print('scholarly已修改网页获取方式')
