import re


def split_name(name):
    """
    将名字字符串分割为姓和名。

    参数:
    name (str): 需要分割的名字字符串。

    返回:
    tuple: 包含姓和名的元组。
    """
    parts = re.split(r'[^A-Za-z]+', name)
    first = parts[0]
    last = max(parts[1:], key=len)
    return first, last


def match_names(name1, name2):
    """
    匹配两个名字,判断是否为同一个人。
    针对纯英文名，对中文的拼音名可能失效

    参数:
    name1 (str): 第一个名字。
    name2 (str): 第二个名字。

    返回:
    bool: 如果两个名字属于同一个人,返回 True,否则返回 False。
    """
    first1, last1 = split_name(name1)
    first2, last2 = split_name(name2)
    # print('人名比较', first1, last1, '和', first2, last2)

    # 如果firstname是单个字母,直接匹配
    if len(first1) == 1 or len(first2) == 1:
        if first1[0] == first2[0] and last1 == last2:
            return True
        else:
            return False
    # 否则使用模糊匹配
    elif first1 != first2 or last1 != last2:
        return False
    else:
        return True
