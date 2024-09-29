import asyncio
import traceback

from parse.gpt_do_page_text import GptDoPageText
from crawl.by_scholarly import fill_bibtex
from run.pipline1 import RunnerConfig, WriteResult
from tools.nodriver_tools import wait_to_complete, SearchTitleOnPage, wait_for_text


class QuitAbstract(Exception):
    pass


class FillPub1:
    def __init__(self, config: RunnerConfig, writer: WriteResult):
        # 依赖对象
        self.config = config
        self.writer = writer

    async def _fill_pub(self, pub):
        item = self.config.item
        logger = self.config.logger
        min_cite = item.min_cite

        # 过滤引用数量
        if min_cite is not None and min_cite > 0:
            if pub.get('num_citations', 0) < min_cite:
                await self.writer.fail_to_fill(pub, '过滤引用数量不足的文献')

        # 创建任务
        tasks = [self.fill_abstract(pub)]
        if not item.ignore_bibtex:
            tasks.append(self.fill_bibtex(pub))

        try:
            # 等待所有任务完成
            await asyncio.gather(*tasks)
            self.writer.success_fill(pub)
        except Exception as e:
            # 未知的异常
            self.writer.fail_to_fill(pub, e)
            logger.error(f'未知异常 {traceback.format_exc()}')
            raise

    async def fill_pub(self, pub):
        logger = self.config.logger
        logger.debug(f'进入文献信息任务 {pub["url"]}')
        try:
            await self._fill_pub(pub)
        except asyncio.CancelledError:
            logger.info(f'取消文献信息任务 {pub["url"]}')
            raise  # 重新抛出异常以确保任务被标记为取消
        finally:
            logger.debug(f'退出文献信息任务 {pub["url"]}')

    async def fill_bibtex(self, pub):
        """
        scholarly每次爬取时间: 不超过60s
        总时间: 不超过2min
        """
        logger = self.config.logger
        page_url = pub['url']
        for i in range(2):
            try:
                await asyncio.wait_for(fill_bibtex(pub), timeout=60)  # debug 防止一直等下去
                logger.debug(f'bibtex任务成功 {page_url}')
                return
            except asyncio.TimeoutError as e:
                logger.debug(f'bibtex获取超时,已尝试{i+1} {page_url}')
            except asyncio.CancelledError:
                logger.info(f'取消bibtex任务 {page_url}')
                raise

    async def _fill_abstract(self, page_url, pub):
        """
        等待时间: 固定2s + 标题出现不超过30s + 网页加载完毕不超过30s
        GPT询问时间: 不超过60s
        总时间: (等待时间 + GPT询问时间) 不超过2min
        """
        browser = self.config.browser
        logger = self.config.logger

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

    async def fill_abstract(self, pub):
        logger = self.config.logger
        page_url = pub['url']
        try:
            await self._fill_abstract(page_url, pub)
            logger.debug(f'摘要任务成功 {page_url}')
        except QuitAbstract as e:
            logger.error(f'摘要任务失败 {e} {page_url}')
        except asyncio.CancelledError:
            logger.info(f'取消摘要任务 {page_url}')
            raise
        except Exception as e:
            logger.error(f'摘要任务失败 {e} {page_url}')
            raise

    # async def fill_abstract_2(self, pub):
    #     prime_url = pub['url']
    #     version_link = pub['version_link']
    #     if not version_link:
    #         self.logger.error(f'爬取摘要失败 文献缺少其他版本 {prime_url}')
    #         return False
    #
    #     # 获取其他版本链接
    #     try:
    #         version_urls = await get_version_urls(version_link)
    #         self.logger.debug(f'成功获取其他版本 {prime_url}')
    #     except QueryScholarlyError as e:
    #         self.logger.error(f'爬取摘要失败 获取其他版本出错 {e} {prime_url}')
    #         # 不抛出
    #         return False
    #
    #     for url in version_urls:
    #         if url == prime_url:  # 已经尝试过了
    #             continue
    #
    #         try:
    #             await self._fill_abstract(url, pub)
    #             return True
    #         except self.crawl.PageIsPdfError as e:
    #             self.logger.error(f'爬取摘要失败 网页是pdf {url}')
    #         except asyncio.TimeoutError as e:
    #             self.logger.error(f'爬取摘要失败 {e} {url}')
    #         except (GptDoPageText.GPTQueryError, GptDoPageText.GPTAnswerError) as e:
    #             self.logger.error(f'爬取摘要失败 {e} {url}')
    #
    #     return False
