import time

from scholarly.publication_parser import PublicationParser


def _new_get_bibtex(self, bib_url) -> str:
    max_tries = 2
    wait_time = 1  # 1s
    for i in range(max_tries):
        # 原本的代码
        soup = self.nav._get_soup(bib_url)
        styles = soup.find_all('a', class_='gs_citi')
        for link in styles:
            if link.string.lower() == "bibtex":
                return link.get('href')
        # 下一次尝试
        if i < max_tries - 1:
            time.sleep(wait_time)
    raise Exception(f'各类引用中无法找到bibtex的链接 {bib_url}')


# 使用反射修改类的方法
setattr(PublicationParser, '_get_bibtex', _new_get_bibtex)
