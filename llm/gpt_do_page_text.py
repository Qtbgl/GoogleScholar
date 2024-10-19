import re
import traceback

from bs4 import BeautifulSoup, Comment

from llm.AskGpt import AskGpt


def extract_string_tag(root):
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


def extract_js_strings(js_code):
    js_strings = []
    for s in re.findall(r'"(.*?)"', js_code):
        if len(s.split()) >= 3:
            js_strings.append(s)

    for s in re.findall(r"'(.*?)'", js_code):
        if len(s.split()) >= 3:
            js_strings.append(s)

    return js_strings


def process_html(html_str):
    root = BeautifulSoup(html_str, 'html.parser')
    # 删除 <style> 标签
    for style_tag in root.find_all('style'):
        style_tag.decompose()

    # 删减 <script> 标签
    for script_tag in root.find_all('script'):
        js_strings = extract_js_strings(script_tag.text)
        script_tag.string = '\n'.join(js_strings)

    return root.prettify()


# class GptDoPageText(AskGpt):
#     def __init__(self, timeout=None):
#         super().__init__(timeout)
#
#     async def get_abstract(self, cut, html_str):
#         root = BeautifulSoup(html_str, 'html.parser')
#         web_txt = extract_text(root)
#         query_txt = '\n'.join([
#             '以下是一段不完整的摘要：', str(cut),
#             '以下是该文章/出版物的网页内容：', web_txt,
#             '请从上面的网页内容中找出完整的摘要，直接以英文输出摘要'
#         ])
#         # query_txt = '\n'.join([
#         #     'The following is a partial excerpt of an abstract:', cut,
#         #     'The following is the web content of this article/publication:', web_txt,
#         #     'Please extract the complete abstract from the web content above and output it directly'
#         # ])
#
#         # logger.info('\n'.join([
#         #     ' '
#         #     f'                      Query GPT for Page: {pub["url"]}',
#         #     query_txt,
#         #     '-------------------------------Answer----------------------------',
#         #     ans
#         # ]))
#
#         ans = await self.ask_gpt(query_txt)
#         return ans
