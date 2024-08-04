import re

import nodriver as uc
import requests.utils
from bs4 import BeautifulSoup

from crawl.by_scholarly import QueryItem


class Crawl:
    def __init__(self):
        self.headless = False  # TODO
        self.user_data_dir = None

    async def __aenter__(self):
        print('打开浏览器')
        self.browser = await uc.start(headless=self.headless, user_data_dir=self.user_data_dir)
        return self

    async def fetch_page(self, pub):
        # 打开网页
        page = await self.browser.get(pub['url'], new_tab=True)  # debug 需要在new_tab，否则会竞争页面
        # 等待页面加载
        await page.wait(3)
        title: str = pub['bib']['title']
        # 检查元素加载
        await page.wait_for(text=title[:40], timeout=10)

        content = await page.get_content()
        await page.close()  # debug 关闭页面，释放内存
        return content

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # 关闭浏览器
        print('关闭浏览器')
        for tag in self.browser.tabs:
            await tag.close()

    async def query_scholar(self, item: QueryItem):
        _PUBSEARCH = '/ scholar?hl=en&q={0}'
        query = item.name
        url = self._construct_url(
            _PUBSEARCH.format(requests.utils.quote(query)))
        url = 'https://scholar.google.com{0}'.format(url)
        page = await self.browser.get(url, new_tab=True)
        await page.wait(1)
        # 解析网页
        res = BeautifulSoup(await page.get_content(), 'html.parser')
        publib = res.find('div', id='gs_res_glb').get('data-sva')
        soup = res
        rows = soup.find_all('div', class_='gs_r gs_or gs_scl') + soup.find_all('div', class_='gsc_mpat_ttl')
        publication = self.load_in_pub(soup)

    def _construct_url(self, baseurl: str, patents: bool = True,
                       citations: bool = True, year_low: int = None,
                       year_high: int = None, sort_by: str = "relevance",
                       include_last_year: str = "abstracts",
                       start_index: int = 0) -> str:
        """Construct URL from requested parameters."""
        url = baseurl

        yr_lo = '&as_ylo={0}'.format(year_low) if year_low is not None else ''
        yr_hi = '&as_yhi={0}'.format(year_high) if year_high is not None else ''
        citations = '&as_vis={0}'.format(1 - int(citations))
        patents = '&as_sdt={0},33'.format(1 - int(patents))
        sortby = ''
        start = '&start={0}'.format(start_index) if start_index > 0 else ''

        if sort_by == "date":
            if include_last_year == "abstracts":
                sortby = '&scisbd=1'
            elif include_last_year == "everything":
                sortby = '&scisbd=2'
            else:
                # self.logger.debug(
                #     "Invalid option for 'include_last_year', available options: 'everything', 'abstracts'")
                return
        elif sort_by != "relevance":
            # self.logger.debug("Invalid option for 'sort_by', available options: 'relevance', 'date'")
            return

        # improve str below
        return url + yr_lo + yr_hi + citations + patents + sortby + start

    def load_in_pub(self, soup):
        # 装入数据
        publication = {}
        publication['bib'] = {}
        databox = soup.find('div', class_='gs_ri')
        title = databox.find('h3', class_='gs_rt')

        cid = soup.get('data-cid')
        pos = soup.get('data-rp')

        publication['gsrank'] = int(pos) + 1

        if title.find('span', class_='gs_ctu'):  # A citation
            title.span.extract()
        elif title.find('span', class_='gs_ctc'):  # A book or PDF
            title.span.extract()

        publication['bib']['title'] = title.text.strip()

        if title.find('a'):
            publication['pub_url'] = title.find('a')['href']

        author_div_element = databox.find('div', class_='gs_a')
        authorinfo = author_div_element.text
        authorinfo = authorinfo.replace(u'\xa0', u' ')  # NBSP
        authorinfo = authorinfo.replace(u'&amp;', u'&')  # Ampersand
        publication['bib']["author"] = self._get_authorlist(authorinfo)
        authorinfo_html = author_div_element.decode_contents()
        publication["author_id"] = self._get_author_id_list(authorinfo_html)

        # There are 4 (known) patterns in the author/venue/year/host line:
        #  (A) authors - host
        #  (B) authors - venue, year - host
        #  (C) authors - venue - host
        #  (D) authors - year - host
        # The authors are handled above so below is only concerned with
        # the middle venue/year part. In principle the venue is separated
        # from the year by a comma. However, there exist venues with commas
        # and as shown above there might not always be a venue AND a year...
        venueyear = authorinfo.split(' - ')
        # If there is no middle part (A) then venue and year are unknown.
        if len(venueyear) <= 2:
            publication['bib']['venue'], publication['bib']['pub_year'] = 'NA', 'NA'
        else:
            venueyear = venueyear[1].split(',')
            venue = 'NA'
            year = venueyear[-1].strip()
            if year.isnumeric() and len(year) == 4:
                publication['bib']['pub_year'] = year
                if len(venueyear) >= 2:
                    venue = ','.join(venueyear[0:-1])  # everything but last
            else:
                venue = ','.join(venueyear)  # everything
                publication['bib']['pub_year'] = 'NA'
            publication['bib']['venue'] = venue

        if databox.find('div', class_='gs_rs'):
            publication['bib']['abstract'] = databox.find('div', class_='gs_rs').text
            publication['bib']['abstract'] = publication['bib']['abstract'].replace(u'\u2026', u'')
            publication['bib']['abstract'] = publication['bib']['abstract'].replace(u'\n', u' ')
            publication['bib']['abstract'] = publication['bib']['abstract'].strip()

            if publication['bib']['abstract'][0:8].lower() == 'abstract':
                publication['bib']['abstract'] = publication['bib']['abstract'][9:].strip()

        # publication['url_scholarbib'] = _BIBCITE.format(cid, pos)
        # sclib = self.nav.publib.format(id=cid)
        # publication['url_add_sclib'] = sclib

        lowerlinks = databox.find('div', class_='gs_fl').find_all('a')

        publication["num_citations"] = 0

        for link in lowerlinks:
            if 'Cited by' in link.text:
                publication['num_citations'] = int(re.findall(r'\d+', link.text)[0].strip())
                publication['citedby_url'] = link['href']

            if 'Related articles' in link.text:
                publication['url_related_articles'] = link['href']

        if soup.find('div', class_='gs_ggs gs_fl'):
            publication['eprint_url'] = soup.find(
                'div', class_='gs_ggs gs_fl').a['href']
        return publication

    def _get_authorlist(self, authorinfo):
        authorlist = list()
        text = authorinfo.split(' - ')[0]
        for i in text.split(','):
            i = i.strip()
            if bool(re.search(r'\d', i)):
                continue
            if ("Proceedings" in i or "Conference" in i or "Journal" in i or
                    "(" in i or ")" in i or "[" in i or "]" in i or
                    "Transactions" in i):
                continue
            i = i.replace("…", "")
            authorlist.append(i)
        return authorlist

    def _get_author_id_list(self, authorinfo_inner_html):
        author_id_list = list()
        html = authorinfo_inner_html.split(' - ')[0]
        for author_html in html.split(','):
            author_html = author_html.strip()
            match = re.search('\\?user=(.*?)&amp;', author_html)
            if match:
                author_id_list.append(match.groups()[0])
            else:
                author_id_list.append("")
        return author_id_list
