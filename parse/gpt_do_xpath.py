import re

from tools.html_tools import merge_xpath, get_xpath
from tools.llm_tools import ask_gpt


def look_at_page(root):
    """
    return: 文本片段，处在的标签
    """
    # 获取纯文本内容
    web_str = []
    web_tag = []
    for s in root.find_all(string=True):  # 遍历所有文本结点
        # 筛选标签
        if s.parent.name in ('script', 'style',):  # 过滤js,css
            continue

        tag = s.parent  # 记录标签对象
        s = s.strip()
        if s:
            web_str.append(s)
            web_tag.append(tag)

    # end for
    return web_str, web_tag


def query_gpt(web_str):
    web_txt = '\n'.join([f"文字片段{i}：{s}" for i, s in enumerate(web_str)])  # more close for gpt
    query = '\n'.join([
        '以下是一篇文章/出版物的网页文字片段：', web_txt,
        '请找出摘要或概述性内容对应文字片段，请以列表输出'
    ])
    return ask_gpt(query)


def parse_number(answer):
    pattern = r"文字片段(\d+)"
    matches = re.findall(pattern, answer)
    numbers = [int(number) for number in matches]
    return numbers


def get_xpath_by_gpt(root):
    """
    :param root: bs4标签
    :return:
    """
    # 获取文字片段
    web_str, web_tag = look_at_page(root)
    ans = query_gpt(web_str)
    xpaths = []
    # 提取GPT回答中的数字
    for number in parse_number(ans):
        idx = number  # 下标从0开始
        tag = web_tag[idx]  # 同下标，文字片段
        # 自定义bs4路径导航
        xpath = get_xpath(tag)
        xpaths.append(xpath)

    # 合并子标签路径
    merge_xpath(xpaths)
    assert len(xpaths) > 0, '结果不有效'
    return xpaths
