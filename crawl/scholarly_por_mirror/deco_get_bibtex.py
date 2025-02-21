from urllib.parse import urljoin

from scholarly.publication_parser import PublicationParser

_get_bibtex = getattr(PublicationParser, '_get_bibtex')  # 保存类方法


def _new_get_bibtex(self, bib_url) -> str:
    print('hijack into _get_bibtex', bib_url)
    url = _get_bibtex(self, bib_url)
    if not url:
        raise Exception(f'各类引用中无法找到bibtex的链接 {bib_url}')

    # 原链接中加入镜像网站域名
    bibtex_url = urljoin('https://scholar.lanfanshu.cn', url)
    return bibtex_url


# 使用反射修改类的方法
setattr(PublicationParser, '_get_bibtex', _new_get_bibtex)
print('scholarly已修改_get_bibtex', __file__)
