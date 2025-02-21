from scholarly import scholarly, ProxyGenerator
from scholarly._navigator import Navigator

from data import api_config


def use_proxy():
    # 配置代理
    pg = ProxyGenerator()
    succeed = pg.SingleProxy(api_config.ipfoxy_proxy_auth)
    # logger.debug(f'设置 scholarly IP代理 {"succeed" if succeed else "failed"}')
    if not succeed:
        return False

    # success = pg.SingleProxy(http = <your http proxy>, https = <your https proxy>)
    scholarly.use_proxy(pg, secondary_proxy_generator=pg)
    return True


def get_scholarly_nav():
    # 依赖于scholarly
    nav = getattr(scholarly, '_Scholarly__nav')
    assert isinstance(nav, Navigator)
    return nav


# 直接加载，不用判断，deco_加载移到别的文件中 —— 2025/2/20

# __all__ = ['scholarly', 'get_scholarly_nav', 'use_proxy', 'ScholarlyUseProxy']


# class ScholarlyUseProxy:
#     _users = 0  # 同时多个请求情况
#
#     @classmethod
#     def create(cls, logger):
#         # 每次使用scholarly时
#         if api_config.scholarly_use_proxy and cls._users == 0:
#             logger.debug('准备创建 scholarly IP代理')
#             succeed = use_proxy()
#             if succeed:
#                 logger.debug(f'成功创建 scholarly IP代理')
#             else:
#                 logger.debug('创建 scholarly IP代理失败')
#
#         return cls()
#
#     def __enter__(self):
#         # 注册用户
#         self._users += 1
#
#     def __exit__(self, exc_type, exc_val, exc_tb):
#         self._users -= 1
