import asyncio
import logging
from urllib.parse import urlparse

from bootstrap import elsevier_api
from bootstrap.spider_get_page import async_scrape_url, SpiderCrawlFailed
from bootstrap.crawl_semanticscholar import get_abstract_by_semanticscholar
from llm.AskGpt import AskGpt
from llm.process_html_for_gpt import process_html
from pub_item import PubItem

logger = logging.getLogger('CrawlGoogleScholar')


class QuitAbstract(Exception):
    pass


async def fill_abstract(pub: PubItem):
    """
    限制异步访问数量
    """
    task_id = pub.task_id
    logger.debug(f'进入摘要任务 #{task_id}')
    try:
        await _fill_abstract(pub)
        logger.debug(f'摘要任务成功 #{task_id}')
    except QuitAbstract as e:
        logger.error(f'摘要任务失败 {e} #{task_id}')
        # 吸收此类型异常
        # 爬取失败 ！= 抛弃这篇
    except asyncio.CancelledError:
        logger.debug(f'取消摘要任务 #{task_id}')
        raise
    except Exception as e:
        logger.error(f'摘要任务失败 {type(e)} {e} #{task_id}')
        raise


async def _fill_abstract(pub: PubItem):
    """
    等待时间: spider未知
    GPT询问时间: 不超过60s
    """
    # 先用semanticscholar爬取试一试
    try:
        abstract = await get_abstract_by_semanticscholar(pub.basic_info['title'])
        pub.fill_abstract(abstract)
        return
    except Exception as e:
        logger.debug(f'semanticscholar爬取api失败 {e}')

    page_url = pub.pub_url
    if not page_url:
        raise QuitAbstract('缺少网页地址')

    ps = urlparse(page_url)
    if 'pdf' in ps.path.lower():
        raise QuitAbstract('网页是pdf请直接下载')

    if 'ieee.org' in ps.netloc:
        raise QuitAbstract('ieee网站需要浏览器上加载')

    if 'sciencedirect.com' in ps.netloc:
        try:
            abstract = await elsevier_api.get_abstract_by_pii(ps)
            pub.fill_abstract(abstract)
            return  # 暂时简单地分流
        except Exception as e:
            raise QuitAbstract(f'sciencedirect用api获取失败 {e}')

    # 一般情况用如下方式爬取
    try:
        params = {'proxy_enabled': True, "store_data": False, 'metadata': False, 'request': 'smart'}
        content = await async_scrape_url(page_url, params)
    except asyncio.TimeoutError as e:
        raise QuitAbstract(f'spider-cloud请求超时 {e}')  # spider-cloud请求超时处理??
    except SpiderCrawlFailed as e:
        raise QuitAbstract(e)

    # TODO: 检查这篇文章是否retrack即被撤稿
    try:
        html_str = content
        gpt = AskGpt(timeout=60)
        # 访问GPT，提取结果
        web_txt = process_html(html_str)
        # 限制token
        max_len = 2 * 64000  # 最长支持128000个token，每个token > 2字符
        if len(web_txt) > max_len:
            logger.debug(f'截断web_txt {len(web_txt)} 太长的部分 #{pub.task_id}')
            web_txt = web_txt[:max_len] + ' ...'

        query_txt = '\n'.join([
            '以下是一段不完整的摘要：', str(pub.cut),
            '以下是该文章/出版物的网页内容：', web_txt,
            '请从上面的网页内容中找出完整的摘要，直接以英文输出摘要'
        ])
        abstract = await gpt.ask_gpt(query_txt)
        pub.fill_abstract(abstract)
    except (AskGpt.GPTQueryError, AskGpt.GPTAnswerError) as e:
        raise QuitAbstract(e)
