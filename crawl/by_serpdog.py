import json
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
        if api_key is None:
            self.api_key = '66ac98748bbaa4304df0c960'  # 默认密钥
        else:
            self.api_key = api_key

    def __str__(self):
        return str(self.__dict__)


def parse_pubs(text):
    obj = json.loads(text)
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


def query_scholar(item: QueryItem):
    """
    :return: 一次生成最多10篇文章
    """
    for i in range(item.pages):
        # 一整页获取
        # 创建查询
        payload = {
            'api_key': item.api_key,
            'q': item.name,
            'page': 10 * i,
        }
        if item.as_ylo:
            payload['as_ylo'] = item.as_ylo
        if item.as_yhi:
            payload['as_yhi'] = item.as_yhi
        if item.hl:
            payload['hl'] = item.hl

        try:
            resp = requests.get('https://api.serpdog.io/scholar', params=payload)
            assert resp.status_code == 200
            pubs = parse_pubs(resp.text)
            # 加入BibTeX
            for pub in pubs:
                try:
                    fill_pub(pub, item.api_key)
                except Exception as e:
                    print(e)

            # generate new group of pubs
            yield pubs

        except Exception as e:
            print(e)
            yield []


def fill_pub(pub, api_key):
    payload = {
        'api_key': api_key,
        'q': pub['id'],
    }
    resp = requests.get('https://api.serpdog.io/scholar_cite', params=payload)
    assert resp.status_code == 200
    obj = json.loads(resp.text)
    # 解析链接
    bib_link = None
    for link in obj['links']:
        if link['name'] == 'BibTeX':
            bib_link = link['link']
            break
    # 获取内容
    try:
        assert bib_link is not None
        resp = requests.get(bib_link)
        assert resp.status_code == 200
        pub['BibTeX'] = resp.text
    except Exception as e:
        print(e)
        pub['BibTeX'] = None

    return pub
