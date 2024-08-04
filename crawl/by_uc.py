import undetected_chromedriver as uc


class Crawl:
    async def __aenter__(self):
        ...
        return self

    async def fetch_page(self, url):
        # 打开网页
        content = ...
        return content

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # 关闭浏览器
        ...
