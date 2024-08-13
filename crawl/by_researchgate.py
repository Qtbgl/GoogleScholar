import asyncio
import traceback
import urllib.parse

from bs4 import BeautifulSoup

from crawl.by_nodiver import Crawl
from tools.people_name_tools import match_names


class ByResearchGate:
    def __init__(self, logger, crawl: Crawl):
        self.logger = logger
        self.crawl = crawl

    class GetLinkError(Exception):
        pass

    async def get_html(self, page_url, pub):
        if await self.crawl.is_page_pdf(page_url):
            raise Crawl.PageIsPdfError()

        kw1 = pub['title'].split()
        keywords = kw1[:4]
        # kw2 = [s for s in pub['cut'].split() if re.match(r'^[a-zA-Z]+$', s)]
        # keywords = kw1[:4] + kw2[:12]  # 用标题和摘要勉强匹配
        # 长时间等待
        html_str = await self.crawl.fetch_page(page_url, wait_sec=10, keywords=keywords)
        return html_str

    async def get_links(self, pub):
        try:
            links = await self._get_links(pub)
            assert len(links) > 0
            return links
        except asyncio.CancelledError:
            raise
        except Exception as e:
            self.logger.error(traceback.format_exc(chain=False))  # 函数内具体出错
            raise self.GetLinkError(e)

    async def _get_links(self, pub: dict):
        title = pub['title']
        payload = {'q': title, }
        url = 'https://www.researchgate.net/search/publication'  # 需要网络支持
        url = f"{url}?{urllib.parse.urlencode(payload)}"
        kws = ("Discover the world's scientific knowledge",)
        sls = ('.search-indent-container',)
        text = await self.crawl.fetch_page(url, keywords=kws, selectors=sls)

        # scraping
        soup = BeautifulSoup(text, 'html.parser')
        container = soup.find("div", class_="search-indent-container")
        first_author = pub['author'].split(',')[0]

        # def is_the_author(full_name):
        #     for s in first_author.split():  # 假设reseachgate作者名字全写
        #         if s not in full_name:
        #             return False
        #     return True

        # 文本相似匹配
        links = []

        for nova_item in container.find_all("div", class_="nova-legacy-o-stack__item"):
            # 匹配标题
            link = nova_item.find("a", string=lambda s: s and title.lower() in s.lower())
            if not link:
                continue

            # 匹配作者
            flag = False
            for author in soup.find_all('span', {
                'class': 'nova-legacy-v-person-inline-item__fullname',
                "itemprop": "name"
            }):
                name = author.text
                if match_names(first_author, name):
                    flag = True
                    break

            if not flag:
                continue

            # 提取链接 URL
            url = 'https://www.researchgate.net/' + link["href"]
            links.append(url)

        return links
