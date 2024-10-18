import asyncio
import pathlib
import re
import tempfile
import time
import traceback

from parse.gpt_do_page_text import GptDoPageText
from record.Record1 import Record1
from crawl.by_scholarly import ByScholarly, QueryItem
from crawl.by_nodiver import Crawl


class Record:
    def __init__(self):
        self.success = []
        self.fail = []

    def success_download(self, url, save_path, name):
        self.success.append({
            'url': url,
            'save_path': save_path,
            'name': name
        })

    def fail_download(self, url, e):
        self.fail.append({
            'url': url,
            'error': str(e),
        })


class Downloader(object):
    def __init__(self, crawl: Crawl, logger):
        # 依赖对象
        self.crawl = crawl
        self.logger = logger



    async def run(self, url):
        async with self.crawl:
            await self.finish(url)

    async def finish(self, url):
        self.logger.info(f'任务下载')
        result = {'url': url, 'error': None}
        try:
            from data.path_config import download
            with tempfile.TemporaryDirectory(dir=download) as temp_dir:
                pdf_file = await self.download_pdf(url, pathlib.Path(temp_dir))
                result['name'] = pdf_file.name
                # 移动到download目录
                save_path = pathlib.Path(download) / f'{temp_dir}.pdf'
                pdf_file.rename(save_path)
                result['save_path'] = save_path

            return result

        except asyncio.CancelledError:
            raise
        except TimeoutError as e:
            result['error'] = f'下载超时 {e}'
            return result
        except Exception as e:
            self.logger.error('未预料的异常' + '\n' + traceback.format_exc())
            raise e

    async def download_pdf(self, pdf_url, temp_path: pathlib.Path):
        # 打开pdf网页，自动下载
        browser = self.crawl.browser
        page = await browser.get(pdf_url, new_tab=True)

        try:
            # Check if the page has loaded successfully
            start = time.time()
            wait_and_see = True
            while True:
                # pdf已存在
                pdf_file = list(temp_path.glob('*.pdf'))
                if len(pdf_file):
                    return pdf_file[0]

                # pdf未存在，但有其他文件
                if any(temp_path.glob('*.crdownload')):
                    if time.time() - start >= 120:
                        raise TimeoutError

                    await asyncio.sleep(2)
                    continue

                # 如何还找不到文件，检查超时
                if time.time() - start >= 60:
                    raise TimeoutError

                # 继续等待网页加载
                if page not in browser.tabs:
                    # 文件和网页都不存在？
                    # 一般是在正常下载pdf了
                    await asyncio.sleep(2)
                else:
                    ready_state = await page.evaluate("document.readyState")
                    # 检查网页是否需要重新加载
                    if ready_state == 'complete':
                        if wait_and_see:  # 保护成功加载情况
                            wait_and_see = False
                            await asyncio.sleep(4)
                        else:
                            await page.reload()
                            wait_and_see = True  # 重新加载后
                            await asyncio.sleep(10)
                    else:
                        await asyncio.sleep(2)

        finally:
            # 网页加载成功后
            if page in browser.tabs:
                print('页面未自动关闭，尝试关闭')
                await page.close()
