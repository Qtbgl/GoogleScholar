import asyncio
import traceback

from parse.gpt_do_page_text import GptDoPageText
from record.Record1 import Record1
from crawl.by_scholarly import ByScholarly, QueryItem, QueryScholarlyError, get_version_urls, fill_bibtex
from crawl.by_nodiver import Crawl
from tools.nodriver_tools import wait_to_complete, SearchTitleOnPage, wait_for_text


class QuitAbstract(Exception):
    pass


class FillPub1:
    def __init__(self, crawl: Crawl, record: Record1, logger):
        # 依赖对象
        self.crawl = crawl
        self.record = record
        self.logger = logger
        self.source = ByScholarly(self.logger)
        # 不返回结果

    async def _fill_pub(self, pub, item: QueryItem):
        min_cite = item.min_cite
        # 过滤引用数量
        if min_cite is not None and min_cite > 0:
            num_citations = pub.get('num_citations')
            if num_citations is None:
                self.record.fail_to_fill(pub, f'无引用数量信息')
                return
            elif num_citations < min_cite:
                self.record.fail_to_fill(pub, f'引用数量不足 {pub["num_citations"]} < {min_cite}')
                return

        tasks = []

        # 创建任务
        tasks.append(asyncio.create_task(self.fill_abstract(pub)))

        if not item.ignore_bibtex:
            tasks.append(asyncio.create_task(self.fill_bibtex(pub)))

        try:
            # 等待所有任务完成
            await asyncio.gather(*tasks)
            self.record.success_fill(pub)
        except Exception as e:
            # 未知的异常
            self.record.fail_to_fill(pub, e)
            self.logger.error(f'未知异常 {traceback.format_exc()}')
            raise
        finally:
            # 确保所有任务结束
            for task in tasks:
                if not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass

    async def fill_pub(self, pub, item):
        self.logger.debug(f'进入文献信息任务 {pub["url"]}')
        try:
            await self._fill_pub(pub, item)
        finally:
            self.logger.debug(f'退出文献信息任务 {pub["url"]}')

    async def fill_bibtex(self, pub):
        """
        scholarly每次爬取时间: 不超过60s
        总时间: 不超过2min
        """
        page_url = pub['url']
        for i in range(2):
            try:
                await asyncio.wait_for(fill_bibtex(pub), timeout=60)  # debug 防止一直等下去
                self.logger.debug(f'bibtex任务成功 {page_url}')
                return
            except asyncio.TimeoutError as e:
                self.logger.debug(f'bibtex获取超时,已尝试{i+1} {page_url}')

    async def _fill_abstract(self, page_url, pub):
        """
        等待时间: 固定2s + 标题出现不超过30s + 网页加载完毕不超过30s
        GPT询问时间: 不超过60s
        总时间: (等待时间 + GPT询问时间) 不超过2min
        """
        if await self.crawl.is_page_pdf(page_url):
            raise QuitAbstract('网页是pdf')

        title = pub['title']
        cut = pub['cut']
        page = await self.crawl.browser.get(page_url, new_tab=True)
        try:
            await page.wait(2)
            # 确保标签出现
            await wait_for_text(page, SearchTitleOnPage(title), timeout=30)

            if not await wait_to_complete(page, 30):
                self.logger.debug(f'网页未等待加载完成 {page_url}')

        except asyncio.TimeoutError as e:
            self.logger.debug(f'失败网页截图 {await page.save_screenshot()}')
            raise QuitAbstract('网页等待超时')

        try:
            html_str = await page.get_content()

            gpt = GptDoPageText(timeout=60)
            # 访问GPT，提取结果
            pub['abstract'] = await gpt.get_abstract(cut, html_str)

        except (GptDoPageText.GPTQueryError, GptDoPageText.GPTAnswerError) as e:
            self.logger.debug(f'失败网页截图 {await page.save_screenshot()}')
            raise QuitAbstract(e)

        # 网页关闭管理部分……

    async def fill_abstract(self, pub):
        page_url = pub['url']
        try:
            await self._fill_abstract(page_url, pub)
            self.logger.debug(f'摘要任务成功 {page_url}')
        except QuitAbstract as e:
            self.logger.error(f'摘要任务失败 {e} {page_url}')
        except Exception as e:
            self.logger.error(f'摘要任务失败 {e} {page_url}')
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
