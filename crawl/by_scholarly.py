import asyncio
import traceback

from bs4 import BeautifulSoup
from scholarly import scholarly, ProxyGenerator, Publication

from data import api_config

from run.pipline1 import QueryItem


def use_proxy():
    # 配置代理
    pg = ProxyGenerator()
    succeed = pg.SingleProxy(api_config.ipfoxy_proxy_auth)
    # logger.debug(f'设置 scholarly IP代理 {"succeed" if succeed else "failed"}')
    if not succeed:
        return False

    # success = pg.SingleProxy(http = <your http proxy>, https = <your https proxy>)
    scholarly.use_proxy(pg, secondary_proxy_generator=pg)
    return True


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

    def __aiter__(self):
        item = self.item
        name = self.item.name
        # 创建生成器
        self.q = scholarly.search_pubs(name, year_low=item.year_low, year_high=item.year_high)
        return self

    def next_to_anext(self):
        try:
            return next(self.q)
        except StopIteration:
            raise StopAsyncIteration  # 异步退出信号
        except Exception as e:
            raise QueryScholarlyError(e)

    async def __anext__(self):
        value = await asyncio.to_thread(self.next_to_anext)
        return value


def get_bib_link(raw_pub):
    if 'url_scholarbib' in raw_pub:
        return 'https://scholar.google.com' + raw_pub['url_scholarbib']
    return None


async def fill_bibtex(pub):
    pub['BibTeX'] = {'link': None, 'string': None}

    # 通过原始pub对象获取
    raw_pub = pub['raw_pub']
    pub['BibTeX']['link'] = get_bib_link(raw_pub)

    bib_str = await asyncio.to_thread(scholarly.bibtex, raw_pub)
    pub['BibTeX']['string'] = bib_str


async def get_version_urls(version_link):
    # 依赖于scholarly
    nav = getattr(scholarly, '_Scholarly__nav')

    from scholarly._navigator import Navigator
    assert isinstance(nav, Navigator)

    # 借用nav对象方法，用代理爬取谷歌页面
    try:
        html = await asyncio.to_thread(nav._get_page, version_link, True)
    except asyncio.CancelledError:
        raise
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


def alter_scholarly():
    """
    只能一次修改，否则方法会无限递归
    """
    from scholarly.publication_parser import PublicationParser
    _scholar_pub = getattr(PublicationParser, '_scholar_pub')  # 保存原先方法

    def _new_scholar_pub(self, __data, publication: Publication):
        # logger.info(f'succeed to hijack {self}._scholar_pub')
        # 调用原有函数
        publication = _scholar_pub(self, __data, publication)
        # 补充数据
        databox = __data.find('div', class_='gs_ri')
        lowerlinks = databox.find('div', class_='gs_fl').find_all('a')
        for link in lowerlinks:
            if 'version' in link.text:
                publication['version_link'] = link['href']

        publication.setdefault('version_link', None)
        return publication

    # 使用反射修改类的方法
    setattr(PublicationParser, '_scholar_pub', _new_scholar_pub)


# 代码加载时
if api_config.scholarly_alter_code:
    alter_scholarly()
