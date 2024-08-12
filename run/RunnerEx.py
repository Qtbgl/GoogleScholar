import asyncio

from parse.parse_html import HTMLParse
from parse.gpt_do_xpath import get_xpath_by_gpt
from record.Record2 import Record2
from crawl.by_scholarly import query_scholar
from crawl.by_nodiver import Crawl


class RunnerEx:
    def __init__(self, crawl: Crawl, record: Record2):
        self.crawl = crawl
        self.record = record

    async def run(self, name, *args, **kwargs):
        # 创建查询
        for pubs in query_scholar(name, *args, **kwargs):
            # 爬取网页
            tasks = [self.handle(pub) for pub in pubs]
            results = await asyncio.gather(*tasks)

    async def handle(self, pub):
        # 爬取网页
        html_str = await self.crawl.fetch_page(pub['url'])
        # 处理内容
        pub['abstract'] = await self.handle_page(pub['url'], html_str)
        # 保存数据
        self.record.save_pub(pub)
        return pub

    async def handle_page(self, url, html_str):
        # 解析网页
        # if 陌生网页
        # then 寻找元素，保存信息
        base_url = self.record.search_history(url)
        if base_url is None:
            return await self.handle_unknown_page(url, html_str)
        else:
            parse = HTMLParse(html_str)
            xpaths = self.record.get_xpaths(base_url)
            try:
                # 单独尝试xpaths
                abstract = '\n'.join(parse.get_texts(xpaths))
            except Exception as err:
                # 确定xpaths不可用
                self.record.disable_xpaths(base_url)
                return await self.handle_unknown_page(url, html_str)

            return abstract

    async def handle_unknown_page(self, url, html_str):
        parse = HTMLParse(html_str)
        # 访问GPT，提取结果
        try:
            # 统一尝试
            xpaths = get_xpath_by_gpt(parse.root)
            # next 提取网页
            abstract = '\n'.join(parse.get_texts(xpaths))
        except Exception as err:
            self.record.fail_to_handle(url)
            return None  # 无结果返回

        # 记录该网址，及相应xpath
        self.record.new_handled(url, xpaths)
        return abstract
