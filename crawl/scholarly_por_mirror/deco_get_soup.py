from bs4 import BeautifulSoup
from scholarly._navigator import Navigator


def _mirror_get_soup(self, url: str) -> BeautifulSoup:
    """Return the BeautifulSoup for a page on scholar.google.com"""
    print('hijack into _get_soup', url)
    html = self._get_page('https://scholar.lanfanshu.cn{0}'.format(url))  # 更换
    html = html.replace(u'\xa0', u' ')
    res = BeautifulSoup(html, 'html.parser')
    try:
        self.publib = res.find('div', id='gs_res_glb').get('data-sva')
    except Exception:
        pass
    return res


# 使用反射修改类的方法
setattr(Navigator, '_get_soup', _mirror_get_soup)
print('scholarly已修改_get_soup', __file__)
