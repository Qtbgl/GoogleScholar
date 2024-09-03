import asyncio
import re

import nodriver
from bs4 import BeautifulSoup


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


async def wait_for_text(text, page: nodriver.Tab, timeout=10):
    loop = asyncio.get_running_loop()
    now = loop.time()

    def search(html_str):
        soup = BeautifulSoup(html_str, "html.parser")
        return re.search(text, soup.text, re.IGNORECASE)  # 不匹配英文大小写

    content = await page.get_content()
    # 检查是否存在
    while not search(content):
        if loop.time() - now > timeout:
            raise asyncio.TimeoutError(
                "time ran out while waiting for text: %s" % text
            )
        await page.wait(0.5)
        content = await page.get_content()

    return content
