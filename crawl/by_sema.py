import asyncio
import traceback
import urllib.parse

from bs4 import BeautifulSoup

from crawl.by_nodiver import Crawl
from tools.people_name_tools import match_names


class BySema:
    def __init__(self, logger, crawl: Crawl):
        self.logger = logger
        self.crawl = crawl

    class GetPaperError(Exception):
        pass

    async def get_paper_html(self, pub):
        payload = {'q': pub['title'], 'sort': 'relevance'}
        url = 'https://www.semanticscholar.org/search'
        url = f"{url}?{urllib.parse.urlencode(payload)}"
        # 打开网页
        page = await self.crawl.browser.get(url, new_tab=True)
        try:
            return await self._get_paper_html(pub, page)
        except asyncio.CancelledError:
            raise
        except Exception as e:
            self.logger.error(traceback.format_exc(chain=False))
            raise self.GetPaperError()
        finally:
            # 关闭页面
            await page.close()

    async def _get_paper_html(self, pub, page):
        await page.wait(10)
        await page.wait_for(selector='.result-page', timeout=10)
        # 检索结果
        title = pub['title']
        first_author = pub['author'].split(',')[0]
        targets = []
        soup = BeautifulSoup(await page.get_content(), 'html.parser')
        result = soup.find('div', attrs={'class': 'result-page'})
        for h2 in result.find_all('h2', attrs={'class': 'cl-paper-title'}):
            # 匹配标题
            if not title.lower() in h2.text.lower():
                continue

            target = h2.find_parents(lambda tag: 'cl-paper-row' in tag.get('class', []))
            target = target[0]
            # 匹配作者
            cl_authors = target.find('span', attrs={'class': 'cl-paper-authors'})
            authors = []
            for span in cl_authors.find_all('span', attrs={'data-heap-id': 'heap_author_list_item'}):
                authors.append(span.text)

            # print('authors', authors)
            if not match_names(first_author, authors[0]):
                continue

            targets.append(target)

        htmls = []
        for target in targets:
            try:
                html = await self._get_target_html(target, page)
                htmls.append(html)
            except asyncio.CancelledError:
                raise
            except Exception as e:
                # 不中断
                self.logger.error(traceback.format_exc(chain=False))

        assert len(htmls) > 0
        return htmls

    async def _get_target_html(self, target, page):
        data_id = target['data-paper-id']
        # 浏览器中选中该文献
        js = f"""const paper = document.querySelector('div[data-paper-id="{data_id}"]');"""
        await page.evaluate(js)
        # 获取摘要
        js = """
                const buttons = paper.querySelectorAll('button[aria-label="Expand truncated text"]');
                for (let i = 0; i < buttons.length; i++) {
                  if (buttons[i].textContent.trim() === 'Expand') {
                    buttons[i].click();
                  }
                }"""
        await page.evaluate(js)
        # 展开摘要后，获取网页内容
        soup = BeautifulSoup(await page.get_content(), 'html.parser')
        paper = soup.select_one(f'div[data-paper-id="{data_id}"]')
        html_str = str(paper)
        return html_str
