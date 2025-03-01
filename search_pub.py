import asyncio
import logging
import traceback

from scholarly import scholarly

from fill_pub import fill
from pub_item import PubItem

logger = logging.getLogger('CrawlGoogleScholar')


async def query(key_word: str, pages: int, search_params=None, filter_params=None):
    # 检查输入合规性
    if not key_word.strip():
        raise Exception(f'key_word 输入不能为空 {key_word}')
    if not isinstance(pages, int) or pages < 1:
        raise Exception(f'pages 必须大于零 {pages}')

    filter_params = filter_params or {}
    if filter_params:
        for key, value in filter_params.items():
            if key == 'min_cite':
                assert value is None or isinstance(value, int), f'min_cite 应该为空或一个数量 {value}'
            else:
                raise Exception(f'不支持此过滤条件: {key}={value}')

    pubs = []
    logger.debug(f'开始搜索文献: {key_word}')
    for raw_pub in scholarly.search_pubs(key_word, **(search_params or {})):
        task_id = len(pubs)
        pub = PubItem(raw_pub, task_id)
        logger.debug(f'\t #{task_id} {pub.pub_url}')
        # 加入列表
        pubs.append(pub)
        # 结果传递
        yield pub
        if len(pubs) >= pages * 10:  # 每页10篇
            break

    tasks = [fill(pub, **filter_params) for pub in pubs]
    tasks = list(map(asyncio.create_task, tasks))
    try:
        logger.debug(f'开始所有任务 {len(tasks)} 个')
        await asyncio.gather(*tasks)
    except Exception as e:
        logger.error(f'未知异常 {traceback.format_exc()}')
        raise Exception(f'发生异常，中断爬取 {e}')
    finally:
        # 取消未完成的任务
        for task in tasks:
            task.cancel()
            # 等待所有任务完成取消
        await asyncio.gather(*tasks, return_exceptions=True)
        logger.debug(f'所有任务已结束')


# async def query(key_word):
#     for ...:
#         yield pub
#
#     # 之后很长一段
#     await asyncio.sleep(1000)
