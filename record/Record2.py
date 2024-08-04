from Conn import Conn


class Record2(Conn):
    def search_history(self, url):
        """
        :param url: 寻找与url最相近的网址
        :return: base_url，若未找到返回None
        """

    def get_xpaths(self, base_url):
        """
        :param base_url: 查询此类网页的xpath
        :return:
        """

    def disable_xpaths(self, base_url):
        """
        :param base_url: 此类网页的xpath不可用了
        :return:
        """

    def fail_to_handle(self, url):
        """
        :param url: 记录该网页无法处理
        :return:
        """

    def new_handled(self, url, xpaths):
        """
        :param base_url: 记录成功处理的网页的xpath
        :param xpaths:
        :return:
        """

    def save_pub(self, pub):
        """
        :param pub: 保存此结果
        :return:
        """