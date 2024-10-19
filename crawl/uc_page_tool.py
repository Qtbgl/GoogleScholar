import asyncio
import re

import nodriver
from bs4 import BeautifulSoup, Comment


async def wait_to_complete(page: nodriver.Tab, timeout):
    loop = asyncio.get_running_loop()
    now = loop.time()
    while True:
        s = await page.evaluate("document.readyState")
        if s == 'complete':
            return True

        if loop.time() - now > timeout:  # 不抛异常
            return False

        await page.wait(0.5)


async def wait_to_load(page: nodriver.Tab, init_wait=None, wait_gap=0.5, timeout=10):
    if init_wait:
        await page.wait(init_wait)

    async def to_load():
        while not (await page.evaluate("document.readyState") == 'complete'):
            await page.wait(wait_gap)

    await asyncio.wait_for(to_load(), timeout)


class SearchPage:
    def get_target(self):
        pass

    def __call__(self, page_content: str) -> bool:
        pass


async def wait_for_text(page: nodriver.Tab, search: SearchPage, timeout=10):
    loop = asyncio.get_running_loop()
    now = loop.time()

    content = await page.get_content()
    # 检查是否存在
    while not search(content):
        if loop.time() - now > timeout:
            raise asyncio.TimeoutError(
                f"等待网页内容时超时 {type(search)} {search.get_target()}"
            )
        await page.wait(0.5)
        content = await page.get_content()

    return content


class SearchTitleOnPage(SearchPage):
    def __init__(self, title):
        self.title = title

    def get_target(self):
        return self.title

    def __call__(self, page_content: str):
        title = self.title
        # 使用正则表达式分割字符串，保留字母、数字、连字符和下划线
        words = re.split(r'[^a-zA-Z0-9_-]+', title)
        # 去除空字符串
        words = [word for word in words if word]

        soup = BeautifulSoup(page_content, "html.parser")
        for tag in soup.find_all(string=True):  # 遍历所有文本结点
            if tag.parent.name in ('script', 'style',) or isinstance(tag, Comment):  # 过滤js,css,注释
                continue

            text = str(tag).strip()
            if not text:
                continue

            # 检测标题的每一个字都在内容中
            all_match = True
            for word in words:
                if word.lower() not in text.lower():
                    all_match = False
                    break

            if all_match:
                return True

        return False
