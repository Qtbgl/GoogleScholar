import asyncio
import logging

from fill_pub_abstract import fill_abstract
from fill_pub_bibtex import fill_bibtex
from pub_item import PubItem

logger = logging.getLogger('CrawlGoogleScholar')


async def fill(pub: PubItem, min_cite=None):
    num_citations = pub.num_citations
    # 过滤引用数量
    if min_cite is not None and min_cite > 0:
        if num_citations < min_cite:
            pub.thrown('引用数量过滤')   # TODO: 以后加上论文被撤回过滤
            return

    # 创建任务
    tasks = [asyncio.create_task(fill_abstract(pub)), asyncio.create_task(fill_bibtex(pub))]
    try:
        # 等待所有任务完成
        await asyncio.gather(*tasks)
    finally:
        for task in tasks:
            task.cancel()
        # 等待所有任务完成取消
        await asyncio.gather(*tasks, return_exceptions=True)
        logger.debug(f'退出文献填充任务 #{pub.task_id}')
