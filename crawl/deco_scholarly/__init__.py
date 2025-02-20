# 先设置logging等级，再加载scholarly模块
import logging
logger = logging.getLogger('scholarly')  # 对于scholarly的日志
logger.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(name)s %(asctime)s %(levelname)s %(message)s', datefmt='%m-%d %H:%M:%S')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# 再加载scholarly模块
from scholarly import scholarly

# 修改scholarly中的方法
import crawl.deco_scholarly.deco_scholar_pub
import crawl.deco_scholarly.deco_get_page
import crawl.deco_scholarly.deco_get_bibtex

# 其他相关的工具方法
from crawl.deco_scholarly.scholarly_tool import get_scholarly_nav, use_proxy, ScholarlyUseProxy

# 以后外面的代码，都有用过__init__.py文件来导入scholarly相关的模块
__all__ = ['scholarly', 'get_scholarly_nav', 'use_proxy', 'ScholarlyUseProxy']
