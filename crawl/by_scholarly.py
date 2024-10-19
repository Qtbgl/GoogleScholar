import asyncio
import traceback

from bs4 import BeautifulSoup

from crawl.scholarly_tool import scholarly, get_scholarly_nav
from run.pipline1 import QueryItem


def parse_pub(json_obj):
    pub = json_obj
    author = ', '.join(pub['bib']['author'])
    return {
        'cut': pub['bib']['abstract'],
        'url': pub['pub_url'],
        'author': author,
        'title': pub['bib']['title'],
        'pub_year': pub['bib']['pub_year'],
        'num_citations': pub['num_citations'],
        'eprint_url': pub.get('eprint_url'),
        'raw_pub': pub,
        'version_link': pub.get('version_link'),
    }


async def query_scholar(item: QueryItem):
    """
    :return: 一次生成最多10篇文章
    """
    pages = item.pages
    # 从第0页开始
    i = 0
    pubs = []
    # 遍历生成器，结束时自动退出
    async for res in SearchPubsAsync(item):
        pub = parse_pub(res)
        pubs.append(pub)
        if len(pubs) == 10:  # 每隔一页
            full_page = pubs
            pubs = []  # 重新装载
            yield full_page

            i += 1
            if i >= pages:  # debug
                break

    # 结束生成器


class QueryScholarlyError(Exception):
    pass


class SearchPubsAsync:
    def __init__(self, item: QueryItem):
        self.item = item
        self.q = None

    def __aiter__(self):
        return self

    def init_q(self):
        # 初始化生成器
        item = self.item
        name = self.item.name
        self.q = scholarly.search_pubs(name, year_low=item.year_low, year_high=item.year_high)

    def next_to_anext(self):
        try:
            if self.q is None:
                self.init_q()

            return next(self.q)
        except StopIteration:
            raise StopAsyncIteration  # 异步退出信号
        except Exception as e:
            raise QueryScholarlyError(e)

    async def __anext__(self):
        value = await asyncio.to_thread(self.next_to_anext)
        return value


def get_bib_link(pub):
    raw_pub = pub.get('raw_pub')
    if raw_pub is None:
        return None

    base_url = 'https://scholar.google.com'
    return base_url + raw_pub['url_scholarbib'] if 'url_scholarbib' in raw_pub else None


async def fill_bibtex(pub):
    pub['BibTeX'] = {'link': None, 'string': None}

    # 通过原始pub对象获取
    raw_pub = pub['raw_pub']
    pub['BibTeX']['link'] = get_bib_link(raw_pub)

    bib_str = await asyncio.to_thread(scholarly.bibtex, raw_pub)
    pub['BibTeX']['string'] = bib_str


async def get_version_urls(version_link):
    # 借用nav对象方法，用代理爬取谷歌页面
    nav = get_scholarly_nav()
    try:
        html = await asyncio.to_thread(nav._get_page, version_link, True)
    except Exception as e:
        # logger.debug(traceback.format_exc(chain=False))
        raise QueryScholarlyError(e)

    # 解析页面
    html = html.replace(u'\xa0', u' ')
    soup = BeautifulSoup(html, 'html.parser')
    rows = soup.find_all('div', class_='gs_r gs_or gs_scl')
    version_urls = []
    for row in rows:
        databox = row.find('div', class_='gs_ri')
        title = databox.find('h3', class_='gs_rt')
        # publication['bib']['title'] = title.text.strip()
        if title.find('a'):
            url = title.find('a')['href']
            version_urls.append(url)

    return version_urls
