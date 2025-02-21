from scholarly._navigator import Navigator
from spider import Spider
from data import api_config

# 存在于文件模块
spider = Spider(api_key=api_config.spider_api_key)


def _new_get_page(self, pagerequest: str, premium: bool = False) -> str:
    # print(f'hack in {self}._get_page, {pagerequest} {premium}')
    if not pagerequest:
        raise Exception(f'网页请求为空, {pagerequest}, on {self}._get_page')

    url = pagerequest
    try:
        scraped_data = spider.scrape_url(url)
        item = scraped_data[0]
    except Exception as e:
        raise Exception(f'spider接口调用抛出异常 {e} {url}') from e

    # 如果spider-cloud访问不出错，但爬取任务失败
    if item['error']:
        raise Exception(f"spider接口访问结果error {item['error']} {url}")

    # 如果item.error为空，但目标网页的爬取有误..
    has_captcha = self._requests_has_captcha(item['content'])
    if not (200 <= item['status'] < 300) or has_captcha:
        raise Exception(f"spider接口爬取{item['status']} has_captcha为{has_captcha} {url}")

    # print(item['url'], item['status'], item['costs'])
    return item['content']


# 使用反射修改类的方法
setattr(Navigator, '_get_page', _new_get_page)
print('scholarly已修改网页获取方式')
