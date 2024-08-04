import json
import aiohttp
import requests


class QueryItem:
    name: str
    pages: int
    as_ylo: int
    as_yhi: int
    hl: str
    api_key: str

    def __init__(self, name, pages=3, as_ylo=None, as_yhi=None, hl=None, api_key=None):
        self.name = name
        self.pages = pages
        self.as_ylo = as_ylo
        self.as_yhi = as_yhi
        self.hl = hl
        self.api_key = api_key

    def __str__(self):
        return str(self.__dict__)


class BySerpdog:

    def __init__(self, logger):
        self.logger = logger

    __serpdog_key = '66ac98748bbaa4304df0c960'

    def parse_pubs(self, json_obj):
        obj = json_obj
        pubs = []
        for res in obj["scholar_results"]:
            pubs.append({
                'id': res["id"],
                'url': res['title_link'],
                'cut': res['snippet'],
                'title': res['title'],
                'author': res['displayed_link'],
                'cited': res['inline_links']['cited_by']['total'],
                'resource': res['resources'][0]['link'] if len(res.get('resources', [])) else None
            })
        return pubs

    def get_payload(self, item: QueryItem, i):
        api_key = item.api_key if item.api_key else self.__serpdog_key
        payload = {
            'api_key': api_key,
            'q': item.name,
            'page': 10 * i,
        }
        if item.as_ylo:
            payload['as_ylo'] = item.as_ylo
        if item.as_yhi:
            payload['as_yhi'] = item.as_yhi
        if item.hl:
            payload['hl'] = item.hl

        return payload

    async def query_scholar(self, item: QueryItem):
        """
        :return: 一次生成最多10篇文章
        """
        async with aiohttp.ClientSession() as session:
            for i in range(item.pages):
                # 一整页获取
                # 创建查询
                payload = self.get_payload(item, i)
                async with session.get('https://api.serpdog.io/scholar', params=payload) as resp:
                    assert resp.status == 200
                    pubs = self.parse_pubs(await resp.json(encoding='utf-8'))
                    # generate new group of pubs
                    yield pubs
        # 暂时不处理异常

    async def get_bibtex_link(self, pub, item):
        api_key = item.api_key if item.api_key else self.__serpdog_key
        payload = {
            'api_key': api_key,
            'q': pub['id'],
        }
        async with aiohttp.ClientSession() as session:
            async with session.get('https://api.serpdog.io/scholar_cite', params=payload) as resp:
                assert resp.status == 200
                obj = await resp.json(encoding='utf-8')  # 不太会是中文
                # 解析链接
                for link in obj['links']:
                    if link['name'] == 'BibTeX':
                        return link['link']  # 暂不获取内容

                raise KeyError(f'No BibTeX link in {obj}')
        # 未处理异常
