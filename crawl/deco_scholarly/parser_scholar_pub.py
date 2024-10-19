from scholarly.publication_parser import PublicationParser
from scholarly import Publication
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
