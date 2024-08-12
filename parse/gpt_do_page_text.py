import traceback

from bs4 import BeautifulSoup, Comment

from parse.AskGpt import AskGpt


def extract_text(root):
    # 获取纯文本内容
    web_str = []
    for tag in root.find_all(string=True):  # 遍历所有文本结点
        # 筛选标签
        if tag.parent.name in ('script', 'style',) or isinstance(tag, Comment):  # 过滤js,css,注释
            continue

        s = tag.strip()  # 不再是标签
        if s:
            web_str.append(s)

    web_txt = '\n'.join(web_str)  # 用换行隔开
    return web_txt


class GptDoPageText(AskGpt):
    def __init__(self, logger):
        self.logger = logger

    async def get_abstract(self, cut, html_str):
        root = BeautifulSoup(html_str, 'html.parser')
        web_txt = extract_text(root)
        query_txt = '\n'.join([
            '以下是一段不完整的摘要：', cut,
            '以下是该文章/出版物的网页内容：', web_txt,
            '请从上面的网页内容中找出完整的摘要，直接以英文输出摘要'
        ])
        # query_txt = '\n'.join([
        #     'The following is a partial excerpt of an abstract:', cut,
        #     'The following is the web content of this article/publication:', web_txt,
        #     'Please extract the complete abstract from the web content above and output it directly'
        # ])

        # logger.info('\n'.join([
        #     ' '
        #     f'                      Query GPT for Page: {pub["url"]}',
        #     query_txt,
        #     '-------------------------------Answer----------------------------',
        #     ans
        # ]))

        ans = await self.ask_gpt(query_txt)
        return ans
