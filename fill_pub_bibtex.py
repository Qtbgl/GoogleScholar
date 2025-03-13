import asyncio
import logging

from scholarly import scholarly

from bootstrap.spider_get_page import SpiderCrawlFailed
from pub_item import PubItem

logger = logging.getLogger('CrawlGoogleScholar')


class QuitBibtex(Exception):
    pass


async def fill_bibtex(pub: PubItem):
    """
    爬取时间: spider未知
    """
    task_id = pub.task_id
    logger.debug(f'进入bibtex任务 #{task_id}')
    try:
        await _fill_bibtex(pub)
        logger.debug(f'bibtex任务成功 #{task_id}')
    except QuitBibtex as e:
        logger.error(f'摘要bibtex失败 {e} #{task_id}')
        # 吸收此类型异常
    except asyncio.CancelledError:
        logger.info(f'取消bibtex任务 #{task_id}')
        raise
    except Exception as e:
        logger.error(f'bibtex获取失败 {type(e)} {e} #{task_id}')
        raise


async def _fill_bibtex(pub: PubItem):
    # 通过原始pub对象获取
    # if not has_bib_link(pub):
    #     raise Exception('scholarly未能获得谷歌学术上的bib链接（可能是此文章无bib）')
    # pub['BibTeX']['link'] = get_bib_link(pub)  # debug 要传入pub不是raw_pub

    # 60s超时
    try:
        bib_str = await asyncio.wait_for(_until_get_bib(pub.raw_pub), 60)
    except asyncio.TimeoutError as e:
        raise QuitBibtex(e)

    pub.fill_bibtex(bib_str)


async def _until_get_bib(raw_pub):
    # 确保bibtex函数不会阻塞，并保证被取消后不在调用
    while True:
        try:
            bib_str = await asyncio.to_thread(scholarly.bibtex, raw_pub)
            return bib_str
        except SpiderCrawlFailed as e:
            logger.debug(f'bibtex本次爬取失败，将再次尝试 {e}')  # 日志等级不用error
