# 先设置logging等级，再加载scholarly模块（但好像都一样有效）
import logging
logger = logging.getLogger('scholarly')  # 对于scholarly的日志
logger.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
file_handler = logging.FileHandler(f"scholarly库日志.log", encoding='utf-8')
file_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(name)s %(asctime)s %(levelname)s %(message)s', datefmt='%m-%d %H:%M:%S')
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)
logger.addHandler(console_handler)
logger.addHandler(file_handler)  # 控制台与文件日志

# 再加载scholarly模块
from scholarly import scholarly
from data import api_config

# 修改scholarly中的方法
if api_config.scholarly_DIY_choose == 'con_spider':
    import crawl.scholarly_con_spider.deco_scholar_pub
    import crawl.scholarly_con_spider.deco_get_page
    import crawl.scholarly_con_spider.deco_get_bibtex
elif api_config.scholarly_DIY_choose == 'por_mirror':
    import crawl.scholarly_por_mirror.deco_get_soup
    import crawl.scholarly_por_mirror.deco_get_bibtex
    scholarly.set_retries(2)  # 防止非异步进程太久不结束

# 其他相关的工具方法
from crawl.scholarly_tool import get_scholarly_nav, use_proxy

# 以后外面的代码，都有用过__init__.py文件来导入scholarly相关的模块
__all__ = ['scholarly', 'get_scholarly_nav', 'use_proxy']
