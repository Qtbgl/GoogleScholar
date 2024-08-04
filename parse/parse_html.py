from bs4 import BeautifulSoup

from tools.html_tools import find_tag


class HTMLParse:
    def __init__(self, html_str):
        self.root = BeautifulSoup(html_str, "html.parser")

    def get_texts(self, xpaths):
        """
        :param xpaths:
        :return: 若找不到抛异常
        """
        texts = []
        for xpath in xpaths:
            tag = find_tag(self.root, xpath)
            texts.append(tag.text)

        assert len(texts) > 0, '结果不有效'
        return texts
