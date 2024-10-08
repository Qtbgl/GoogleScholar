import asyncio
import traceback

from crawl.wait_page_tool import wait_to_complete, wait_for_text, SearchTitleOnPage
from node.node_pipline import TaskConfig, ErrorToTell
from parse.gpt_do_page_text import GptDoPageText
from tools.pub_log_tool import display_pub_url


class QuitAbstract(Exception):
    pass


class FillPubsAbstract:
    def __init__(self, config: TaskConfig):
        self.config = config
        self._uc_lock = asyncio.Semaphore(5)

    async def finish(self, pubs):
        logger = self.config.logger
        tasks = [asyncio.create_task(self.fill_abstract(pub)) for pub in pubs]
        try:
            # 爬取网页
            logger.info(f'准备异步爬取 {display_pub_url(pubs)}')
            await asyncio.gather(*tasks)  # 异步浏览器爬取

        except Exception as e:
            logger.error(f'未知异常 {traceback.format_exc()}')
            raise ErrorToTell(f'发生异常，中断爬取 {e}')
        finally:
            # 取消未完成的任务
            for task in tasks:
                task.cancel()
                # 等待所有任务完成取消
            await asyncio.gather(*tasks, return_exceptions=True)

    async def fill_abstract(self, pub):
        """
        限制异步访问数量
        """
        async with self._uc_lock:
            logger = self.config.logger
            task_id = pub['task_id']
            logger.debug(f'进入摘要任务 #{task_id}')
            try:
                await self._fill_abstract(pub)
                logger.debug(f'摘要任务成功 #{task_id}')
            except QuitAbstract as e:
                logger.error(f'摘要任务失败 {e} #{task_id}')
                # 吸收此类型异常
            except asyncio.CancelledError:
                logger.debug(f'取消摘要任务 #{task_id}')
                raise
            except Exception as e:
                logger.error(f'摘要任务失败 {type(e)} {e} #{task_id}')
                raise

    async def _fill_abstract(self, pub):
        """
        等待时间: 固定2s + 标题出现不超过30s + 网页加载完毕不超过30s
        GPT询问时间: 不超过60s
        总时间: (等待时间 + GPT询问时间) 不超过2min
        """
        browser = self.config.browser
        logger = self.config.logger
        page_url = pub['url']

        if 'pdf' in page_url.lower():
            raise QuitAbstract('网页是pdf')

        title = pub['title']
        cut = pub['cut']
        page = await browser.get(page_url, new_tab=True)
        try:
            try:
                await page.wait(2)
                # 确保标签出现
                await wait_for_text(page, SearchTitleOnPage(title), timeout=30)
                if not await wait_to_complete(page, 30):
                    logger.debug(f'网页未等待加载完成 {page_url}')
            except asyncio.TimeoutError as e:
                logger.debug(f'失败网页截图 {await page.save_screenshot()}')
                raise QuitAbstract('网页等待超时')

            try:
                html_str = await page.get_content()
                gpt = GptDoPageText(timeout=60)
                # 访问GPT，提取结果
                pub['abstract'] = await gpt.get_abstract(cut, html_str)
            except (GptDoPageText.GPTQueryError, GptDoPageText.GPTAnswerError) as e:
                logger.debug(f'失败网页截图 {await page.save_screenshot()}')
                raise QuitAbstract(e)
        finally:
            if page in browser.tabs:
                await page.close()
