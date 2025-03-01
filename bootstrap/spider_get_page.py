from spider import Spider, AsyncSpider
from config import spider_config


async def async_scrape_url(url, params):
    app = AsyncSpider(api_key=spider_config.api_key)
    try:
        async with app:
            async for data in app.scrape_url(url, params):
                assert isinstance(data, list) and len(data), f'crawl结果异常 {data}'
                item = data[0]
    except Exception as e:
        raise SpiderAccessError(f'spider接口调用抛出异常 {e} {url}') from e

    check_scrape_result(item)
    return item['content']


def spider_scrape_url(url, params):
    try:
        spider = Spider(api_key=spider_config.api_key)
        data = spider.scrape_url(url, params)  # 参数专用于爬谷歌学术
        assert isinstance(data, list) and len(data), f'crawl结果异常 {data}'
        item = data[0]
    except Exception as e:
        raise SpiderAccessError(f'spider接口调用抛出异常 {e} {url}') from e

    check_scrape_result(item)
    return item['content']


def check_scrape_result(item):
    # 如果spider-cloud访问不出错，但爬取任务失败
    if item['error']:
        raise SpiderAccessError(f"spider接口访问结果error {item['error']} {item['url']}")

    # 如果item.error为空，但目标网页的爬取有误..
    if 200 <= item['status'] < 300:
        raise SpiderCrawlFailed(f"spider接口爬取{item['status']} {item['url']}")


class SpiderAccessError(Exception):
    pass


class SpiderCrawlFailed(Exception):
    pass
