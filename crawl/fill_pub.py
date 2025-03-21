import asyncio
import logging

from crawl.fill_pub_abstract import fill_abstract
from crawl.fill_pub_bibtex import fill_bibtex
from crawl.pub_item import PubItem, ThrowThePub
from llm.llm_tool import ask_gpt_async

logger = logging.getLogger('CrawlGoogleScholar')


async def ask_if_pub_is_retracted(info: str):
    asking = 'Is this a retracted publication? You will first answer Yes/No/Not sure, then give the reason.'
    asking = info + '\n' + asking
    # ans = await AskGpt().ask_gpt(asking)
    ans = await ask_gpt_async(asking, None)
    ans_parse: str = ans.strip().lower()
    # 根据回答执行相应的操作
    if ans_parse.startswith('yes'):
        logger.debug(f"The publication is retracted: {ans} --input: {asking}".replace('\n', '\\n'))
        return IsRetracted(True, ans, True)
    elif ans_parse.startswith('no'):
        # 处理未撤回的情况
        logger.debug(f"The publication is not retracted: {ans} --input: {asking}".replace('\n', '\\n'))
        return IsRetracted(True, ans, False)
    elif ans_parse.startswith('not sure'):
        # 处理不确定的情况
        logger.debug(f"The status of the publication is not clear: {ans} --input: {asking}".replace('\n', '\\n'))
        return IsRetracted(False, ans)
    else:
        logger.debug(f"Unexpected answer: {ans} --input: {asking}".replace('\n', '\\n'))
        return IsRetracted(False, ans)


class IsRetracted:
    def __init__(self, clear, answer, yes=None):
        self.clear = clear
        self.answer = answer
        self.yes = yes


async def throw_pub_if_is_retracted(pub: PubItem, info):
    try:
        result = await ask_if_pub_is_retracted(info)
        if result.clear and result.yes:
            pub.thrown(f'文章是retracted {result.answer}')  # pub中会被标记
        elif not result.clear:
            logger.error(f'GPT无法区分，默认接受文献 #{pub.task_id}')
    except Exception as e:
        logger.error(f'GPT访问出错，默认接受文献 {e} #{pub.task_id}')


async def fill(pub: PubItem, min_cite=None):
    # 在最开始fill时过滤撤回情况
    basic_info = str(pub.basic_info)
    if 'retract' in basic_info.lower():
        await throw_pub_if_is_retracted(pub, basic_info)
        if pub.is_thrown:
            return

    num_citations = pub.num_citations
    # 过滤引用数量
    if min_cite is not None and min_cite > 0:
        if num_citations < min_cite:
            pub.thrown('引用数量过滤')
            return

    # 创建任务
    tasks = [asyncio.create_task(fill_abstract(pub)), asyncio.create_task(fill_bibtex(pub))]
    try:
        # 等待所有任务完成
        await asyncio.gather(*tasks)
    except ThrowThePub as e:
        pub.thrown(reason=str(e))  # 预期效果是任何一个任务抛除异常，整个fill立刻结束
    finally:
        for task in tasks:
            task.cancel()
        # 等待所有任务完成取消
        await asyncio.gather(*tasks, return_exceptions=True)
        # logger.debug(f'退出文献填充任务 #{pub.task_id}')

    more_info = str(vars(pub))
    if 'retract' in more_info.lower():
        await throw_pub_if_is_retracted(pub, more_info)
        if pub.is_thrown:
            return

    # # 改为逐步进行，来检查是否接受这篇，因为fill_bibtex比较消耗爬取次数和机会
    # try:
    #     await fill_abstract(pub)
    #     await fill_bibtex(pub)
    # except ThrowThePub as e:
    #     pub.thrown(reason=str(e))
