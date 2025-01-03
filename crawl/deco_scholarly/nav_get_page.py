from scholarly._navigator import Navigator
from spider import Spider
from data import api_config

# 存在于文件模块
spider = Spider(api_key=api_config.spider_api_key)


def _new_get_page(self, pagerequest: str, premium: bool = False) -> str:
    # print(f'hack in {self}._get_page, {pagerequest} {premium}')
    if not pagerequest:
        raise Exception(f'网页请求为空, {self}._get_page, {pagerequest}')

    url = pagerequest
    try:
        scraped_data = spider.scrape_url(url)
        item = scraped_data[0]
    except Exception as e:
        raise Exception(f'spider-cloud爬取出错 {url}, 接口代码出错 {e}, 请检查一下积分余量！') from e

    # spider-cloud访问不出错，但爬取目标网页也会error
    if item['error']:
        raise Exception(f"spider-cloud爬取出错 {item}")
    elif not (200 <= item['status'] < 300):
        # 此时item.error为空，但目标网页的爬取有误
        content = item.get('content')
        if len(content) > 40:
            content = content[:40] + ' ...'

        raise Exception(f"spider-cloud爬取失败, status: {item['status']}, url: {item['url']}, content: {content}")

    # print(item['url'], item['status'], item['costs'])
    return item['content']


# 使用反射修改类的方法
setattr(Navigator, '_get_page', _new_get_page)
print('scholarly已修改网页获取方式')
