import json
import re
from urllib.parse import quote

import aiohttp
import requests


class Payload:
    def __init__(self, api_key, as_ylo=None, as_yhi=None):
        self.as_ylo = as_ylo
        self.as_yhi = as_yhi
        self.api_key = api_key  # serpdog的api_key


class QueryItem:
    name: str
    pages: int
    min_cite: int
    payload: Payload

    def __init__(self, name, pages, payload: Payload, min_cite=None):
        self.pages = pages
        self.name = name
        self.min_cite = min_cite
        self.payload = payload

    def __str__(self):
        return str(self.__dict__)


def get_payload(item: QueryItem, i):
    payload = {
        'q': item.name,
        'page': 10 * i,
    }
    for k, v in item.payload.__dict__.items():
        if v is not None:
            payload[k] = v

    return payload


class BySerpdog:

    def __init__(self, logger):
        self.logger = logger

    def parse_pubs(self, json_obj):
        obj = json_obj
        pubs = []
        for res in obj["scholar_results"]:
            num_citations = None
            if 'cited_by' in res['inline_links'] and 'total' in res['inline_links']['cited_by']:
                m_cited = re.search(r'\d+', res['inline_links']['cited_by']['total'])
                if m_cited is None:
                    self.logger.debug(f"记录cited_by存在但无法提取情况：{res['inline_links']['cited_by']['total']}")
                else:
                    num_citations = int(m_cited.group())

            resources = res.get('resources', [])
            pubs.append({
                'id': res["id"],
                'url': res['title_link'],
                'cut': res['snippet'],
                'title': res['title'],
                'author': res['displayed_link'],
                'num_citations': num_citations,
                'eprint_url': resources[0]['link'] if len(resources) else None,
            })
        return pubs

    async def query_scholar(self, item: QueryItem):
        """
        :return: 一次生成最多10篇文章
        """
        async with aiohttp.ClientSession() as session:
            for i in range(item.pages):
                # 一整页获取
                # 创建查询
                payload = get_payload(item, i)
                async with session.get('https://api.serpdog.io/scholar', params=payload) as resp:
                    if resp.status != 200:
                        self.logger.error(f'{resp.status} {await resp.text()}')
                        raise self.SerpdogError('serpdog\'s api请求失败')

                    pubs = self.parse_pubs(await resp.json(encoding='utf-8'))
                    # generate new group of pubs
                    yield pubs
        # 暂时不处理异常

    async def get_bibtex_link(self, pub, item: QueryItem):
        api_key = item.payload.api_key
        payload = {
            'api_key': api_key,
            'q': pub['id'],
        }
        async with aiohttp.ClientSession() as session:
            async with session.get('https://api.serpdog.io/scholar_cite', params=payload) as resp:
                if resp.status != 200:
                    self.logger.error(f'{resp.status} {await resp.text()}')
                    raise self.SerpdogError('serpdog\'s api请求失败')

                obj = await resp.json(encoding='utf-8')  # 不太会是中文
                # 解析链接
                for link in obj['links']:
                    if link['name'] == 'BibTeX':
                        return link['link']  # 暂不获取内容

                raise KeyError(f'No BibTeX link in {obj}')
        # 未处理异常

    async def get_bibtex_string(self, bibtex_link, item: QueryItem):
        api_key = item.payload.api_key
        bibtex_link = quote(bibtex_link)
        payload = {'api_key': api_key, 'url': bibtex_link, 'render_js': 'false'}
        async with aiohttp.ClientSession() as session:
            async with session.get('https://api.serpdog.io/scrape', params=payload) as resp:
                if resp.status != 200:
                    self.logger.error(f'{resp.status} {await resp.text()}')
                    raise self.SerpdogError('serpdog\'s api请求失败')

                string = await resp.text(encoding='utf-8')
                return string

    class SerpdogError(Exception):
        pass
