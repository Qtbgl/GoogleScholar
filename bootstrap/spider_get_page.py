from spider import Spider
from config import spider_config


def spider_scrape_url(url):
    try:
        spider = Spider(api_key=spider_config.api_key)
        params = {'proxy_enabled': True, "store_data": False, 'metadata': False, 'request': 'http'}
        scraped_data = spider.scrape_url(url, params)  # 参数专用于爬谷歌学术
        assert len(scraped_data) == 1, f'spider的crawl结果列表长度异常 {len(scraped_data)}'
        item = scraped_data[0]
    except Exception as e:
        raise SpiderAccessError(f'spider接口调用抛出异常 {e} {url}') from e

    # 如果spider-cloud访问不出错，但爬取任务失败
    if item['error']:
        raise SpiderAccessError(f"spider接口访问结果error {item['error']} {url}")

    # 如果item.error为空，但目标网页的爬取有误..
    if 200 <= item['status'] < 300:
        raise SpiderCrawlFailed(f"spider接口爬取{item['status']} {url}")

    return item['content']


class SpiderAccessError(Exception):
    pass


class SpiderCrawlFailed(Exception):
    pass
