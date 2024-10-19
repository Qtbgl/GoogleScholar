import traceback

import asyncio

from nodriver.core.browser import Browser, Config

from crawl import uc_browser_tool


class Crawl:
    @classmethod
    async def create(cls, logger):
        """
        :return: 可能抛出浏览器打开异常
        """
        browser = await uc_browser_tool.create(logger)

        return cls(logger, browser)

    def __init__(self, logger, browser: Browser):
        self.logger = logger
        self.browser = browser
        assert browser and not browser.stopped, 'Crawl的浏览器不可用'

    async def __aenter__(self):  # 不在此处开启浏览器
        self.logger.info('成功打开浏览器')
        return self

    async def fetch_page(self, url, keywords=(), selectors=(), wait_sec=5):
        # 打开网页
        page = await self.browser.get(url, new_tab=True)  # debug 需要在new_tab，否则会竞争页面
        try:
            # 等待页面加载
            await page.wait(wait_sec)

            # if await self.has_captcha(page):
            #     raise self.CaptchaPageError(f'nodriver打开网页含验证码 url:{url} wait_for:{keywords}')

            # 检查元素加载
            for word in keywords:  # 需要所有都存在
                await page.wait_for(text=word, timeout=10)
            for css in selectors:
                await page.wait_for(selector=css, timeout=10)

            content = await page.get_content()
            return content
        except asyncio.exceptions.TimeoutError as e:
            self.logger.error(f'{e}')
            raise self.WaitPageError(f'nodriver等待页面加载失败 url:{url} wait_for:{keywords, selectors}')
        finally:
            await page.close()  # debug 关闭页面，释放内存

    class WaitPageError(Exception):
        pass

    class CaptchaPageError(Exception):
        pass

    class PageIsPdfError(Exception):
        def __init__(self, arg=None):
            super().__init__('网页是pdf' or arg)

    async def is_page_pdf(self, page_url):
        if 'pdf' in page_url.lower():
            return True
        else:
            return False

    async def has_captcha(self, page) -> bool:
        text = await page.get_content()
        try:
            # 似乎无效果
            if 'captcha' in text or 'Captcha' in text or 'CAPTCHA' in text:
                return True
            if 'verify you are human' in text:
                return True
            if '人机验证' in text or ('检查' in text and '连接安全性' in text):
                return True

        except Exception as e:  # 吸收任何异常
            self.logger.error(f'{e}')

        return False

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # 关闭浏览器
        self.logger.info('准备关闭浏览器')
        try:
            self.browser.stop()  # 标准关闭
        except Exception as e:
            self.logger.info(traceback.format_exc())
            raise e  # 再次抛出，不影响原异常
