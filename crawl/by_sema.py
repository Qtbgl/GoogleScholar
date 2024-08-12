import traceback
import urllib.parse

from bs4 import BeautifulSoup

from crawl.by_nodiver import Crawl


class BySema:
    def __init__(self, logger, crawl: Crawl):
        self.logger = logger
        self.crawl = crawl

    class GetPaperError(Exception):
        pass

    async def get_paper_html(self, pub):
        try:
            return await self._get_paper_html(pub)
        except Exception as e:
            self.logger.error(traceback.format_exc(chain=False))
            raise self.GetPaperError()

    async def _get_paper_html(self, pub):
        title = pub['title']
        payload = {'q': title, 'sort': 'relevance'}
        url = 'https://www.semanticscholar.org/search'
        url = f"{url}?{urllib.parse.urlencode(payload)}"
        page = await self.crawl.browser.get(url)
        await page.wait(10)
        await page.wait_for(selector='.result-page', timeout=10)
        # 检索结果
        targets = []
        soup = BeautifulSoup(await page.get_content(), 'html.parser')
        result = soup.find('div', attrs={'class': 'result-page'})
        for target in result.find_all('h2', attrs={'class': 'cl-paper-title'}):
            # 仅匹配标题
            if title.lower() in target.text.lower():
                targets.append(target)

        # 假设第一个
        target = targets[0]
        t = target.find_parents(lambda tag: 'cl-paper-row' in tag.get('class', []))
        t = t[0]
        data_id = t['data-paper-id']
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
