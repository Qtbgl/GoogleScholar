import asyncio

from search_pub import query
from bootstrap import deco_scholarly
from set_logging import setup_console_logging, setup_file_loging

# 先装饰一下原本的scholarly库
deco_scholarly()

# 再设置一下日志
setup_console_logging('CrawlGoogleScholar')
setup_file_loging('CrawlGoogleScholar')


async def main():
    key_word = input('Enter a search term: ')
    pages = 1
    # 更多条件
    search_params = {'year_low': 2024}
    # 结果过滤
    filter_params = {'min_cite': None, }
    data = []
    try:
        async for pub in query(key_word, pages, search_params, filter_params):
            data.append(pub)
    except Exception as e:
        print(f'query函数出错了 {e}')
        print(f'但已获得 {len(data)} 篇论文')


asyncio.run(main())
