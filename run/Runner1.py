import asyncio
import traceback
import urllib.parse

from parse.gpt_do_page_text import GptDoPageText
from record.Record1 import Record1
from crawl.by_scholarly import ByScholarly, QueryItem, QueryScholarlyError, get_version_urls, fill_bibtex
from crawl.by_nodiver import Crawl
from tools.nodriver_tools import wait_to_complete


class Runner1:
    def __init__(self, crawl: Crawl, record: Record1, logger):
        # 依赖对象
        self.crawl = crawl
        self.record = record
        self.logger = logger
        self.source = ByScholarly(self.logger)

    async def run(self, item):
        async with self.crawl:
            async with self.record:
                await self.finish(item)

    async def finish(self, item: QueryItem):
        # 创建查询
        self.logger.info(f'任务查询 {item}')
        self.record.set_pages(item.pages)
        try:
            # for every 10 pubs
            async for pubs in self.source.query_scholar(item):
                # 爬取网页
                self.logger.info(f'准备异步爬取pubs {len(pubs)}')
                tasks = [self.fill_pub(pub, item) for pub in pubs]
                await asyncio.gather(*tasks)  # 异步浏览器爬取

        except asyncio.CancelledError as e:
            self.logger.error('任务取消' + '\n' + traceback.format_exc())
            raise
        except QueryScholarlyError as e:
            self.logger.error(e)
            raise e
        except Exception as e:
            self.logger.error('未预料的异常' + '\n' + traceback.format_exc())
            raise Exception(f'发生异常，中断爬取 {e}')

        # 不返回结果

    async def fill_pub(self, pub, item: QueryItem):
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

        # 异步执行两个任务
        task_abstract = asyncio.create_task(self.fill_abstract(pub))
        task_bibtex = asyncio.create_task(self.fill_bibtex(pub))
        try:
            succeed = await task_abstract
            # if not succeed:
            #     # 再次尝试
            #     task_abstract = asyncio.create_task(self.fill_abstract_2(pub))
            #
            # succeed = await task_abstract
            if not succeed:
                # 只记录为空，不退出
                pub['abstract'] = None

        except asyncio.CancelledError:
            raise
        except Exception as e:
            # 所有异常不抛出
            self.logger.error(traceback.format_exc())
            self.record.fail_to_fill(pub, f'爬取摘要时出错 {e}')
            # 取消任务
            task_abstract.cancel()
            # 结束退出，因为是未预料的异常
            return

        try:
            # 等待bib异步任务结束
            succeed = await task_bibtex
            if not succeed:
                self.record.fail_to_fill(pub, 'BibTeX未正常获取')
                # 退出，因为不合要求
                return

        except asyncio.CancelledError:
            raise
        except Exception as e:
            self.logger.error(traceback.format_exc())
            self.record.fail_to_fill(pub, f'爬取BibTeX时出错 {e}')
            # 取消任务
            task_abstract.cancel()
            return

        # 成功结束
        self.record.success_fill(pub)
        self.logger.debug(f'退出文献信息任务 {pub["url"]}')

    async def fill_bibtex(self, pub):
        succeed = False
        for i in range(3):
            try:
                await asyncio.wait_for(fill_bibtex(pub), timeout=90)  # debug 防止一直等下去
                succeed = True
                break
            except asyncio.CancelledError:
                raise
            except Exception as e:
                self.logger.error(f'scholarly.bibtex失败 {e} {pub["url"]}')

        self.logger.debug(f'退出bibtex任务 {pub["url"]}')
        return succeed

    async def _fill_abstract(self, page_url, pub):
        if await self.crawl.is_page_pdf(page_url):
            raise self.crawl.PageIsPdfError()

        title = pub['title']
        cut = pub['cut']
        page = await self.crawl.browser.get(page_url, new_tab=True)
        try:
            await page.wait(2)
            await page.wait_for(text=title, timeout=30)  # 确保标签出现
            if not await wait_to_complete(page, 30):
                self.logger.debug(f'网页未等待加载完成 {page_url}')

            html_str = await page.get_content()

            gpt = GptDoPageText(self.logger)
            # 访问GPT，提取结果
            pub['abstract'] = await gpt.get_abstract(cut, html_str)

        except asyncio.TimeoutError as e:
            parsed = urllib.parse.urlparse(page_url)
            path = await page.save_screenshot(f'{parsed.hostname}.png')
            self.logger.debug(f'已保存网页截图 {path} {page_url}')
            raise e
        except (GptDoPageText.GPTQueryError, GptDoPageText.GPTAnswerError) as e:
            parsed = urllib.parse.urlparse(page_url)
            path = await page.save_screenshot(f'{parsed.hostname}.png')
            self.logger.debug(f'已保存网页截图 {path} {page_url}')
            raise
        finally:
            await page.close()

    async def fill_abstract(self, pub):
        page_url = pub['url']
        try:
            await self._fill_abstract(page_url, pub)
        except self.crawl.PageIsPdfError as e:
            self.logger.error(f'直接爬取摘要失败 网页是pdf {page_url}')
            return False
        except asyncio.TimeoutError as e:
            self.logger.error(f'直接爬取摘要失败 {e} {page_url}')
            return False
        except (GptDoPageText.GPTQueryError, GptDoPageText.GPTAnswerError) as e:
            self.logger.error(f'直接爬取摘要失败 {e} {page_url}')
            return False

        self.logger.debug(f'退出摘要任务 {page_url}')
        return True

    async def fill_abstract_2(self, pub):
        prime_url = pub['url']
        version_link = pub['version_link']
        if not version_link:
            self.logger.error(f'爬取摘要失败 文献缺少其他版本 {prime_url}')
            return False

        # 获取其他版本链接
        try:
            version_urls = await get_version_urls(version_link)
            self.logger.debug(f'成功获取其他版本 {prime_url}')
        except QueryScholarlyError as e:
            self.logger.error(f'爬取摘要失败 获取其他版本出错 {e} {prime_url}')
            # 不抛出
            return False

        for url in version_urls:
            if url == prime_url:  # 已经尝试过了
                continue

            try:
                await self._fill_abstract(url, pub)
                return True
            except self.crawl.PageIsPdfError as e:
                self.logger.error(f'爬取摘要失败 网页是pdf {url}')
            except asyncio.TimeoutError as e:
                self.logger.error(f'爬取摘要失败 {e} {url}')
            except (GptDoPageText.GPTQueryError, GptDoPageText.GPTAnswerError) as e:
                self.logger.error(f'爬取摘要失败 {e} {url}')

        return False
