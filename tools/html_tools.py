from bs4 import BeautifulSoup
import re


def get_xpath(tag):
    """
    获取标签的 XPath
    
    参数:
    tag (bs4.element.Tag) - 要获取 XPath 的标签
    
    返回:
    str - 标签的 XPath
    """
    xpath = []
    while tag.name != 'html':
        pre = tag.find_previous_siblings(tag.name)
        post = tag.find_next_siblings(tag.name)
        if len(pre) + len(post) == 0:
            xpath.insert(0, f"{tag.name}")
        else:
            idx = len(pre) + 1
            xpath.insert(0, f"{tag.name}[{idx}]")
            
        tag = tag.parent        
    xpath.insert(0, "/html")
    return "/".join(xpath)


def merge_xpath(xpaths):
    def loop():
        n = len(xpaths)
        # 元素两两匹配
        for i in range(n):
            for j in range(n):
                # print('ij', i, j)
                if i != j and xpaths[i] in xpaths[j]:
                    return j  # 返回子路径
                    
    while True:
        # print('loop')
        i = loop()
        if i is None:
            break
        # 更新列表
        xpaths.pop(i)
            
    # end while
    return xpaths


def find_tag(root, xpath):
    """
    根据给定的 XPath 和 HTML 内容,返回定位到的结点。
    
    参数:
    root (tag): BeautifulSoup根节点
    xpath (str): 要使用的 XPath 表达式
    
    返回:
    bs4.element.Tag: 定位到的结点,如果没有找到则返回 None
    """
    # 使用 BeautifulSoup 解析 HTML 文档
    soup = root
    parts = xpath.split('/')

    for part in parts[1:]:
        # xpath逐个标签寻找
        match = re.match(r"(\w+)(?:\[(\d+)\])?", part)
        name = match.group(1)
        id = match.group(2)
        if id is None:  # 默认唯一情况
            id = 1
        else:
            id = int(id)  # re返回字符串

        # print('->', part, id)
        # 匹配对应的子结点
        number = 0
        for tag in soup.children:
            if tag.name == name:
                number += 1
                # print('??', number == id, number, type(number), id, type(id))
                if number == id:
                    soup = tag
                    # print('bingo')
                    break
                    
        assert soup.name == name, f'未成功匹配{part}'
        
    # end for
    return soup
