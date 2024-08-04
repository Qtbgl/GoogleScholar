import nodriver as uc


class Crawl:
    def __init__(self):
        self.headless = True
        self.user_data_dir = None

    async def __aenter__(self):
        print('打开浏览器')
        self.browser = await uc.start(headless=self.headless, user_data_dir=self.user_data_dir)
        return self

    async def fetch_page(self, url, title):
        # 打开网页
        page = await self.browser.get(url, new_tab=True)  # debug 需要在new_tab，否则会竞争页面
        try:
            # 等待页面加载
            await page.wait(3)
            # 检查元素加载
            await page.wait_for(text=title[:40], timeout=10)

            content = await page.get_content()
            return content

        finally:
            await page.close()  # debug 关闭页面，释放内存

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # 关闭浏览器
        print('关闭浏览器')
        for tag in self.browser.tabs:
            await tag.close()
