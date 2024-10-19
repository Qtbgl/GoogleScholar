import logging

from spider import AsyncSpider

from run.pipline1 import QueryItem
from app.params_tool import param_check, check_key, get_int, get_bool, ParamError
from data import api_config


class RunnerConfig:
    logger: logging.Logger
    item: QueryItem
    spider: AsyncSpider

    async def __aenter__(self):
        await self.spider.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.spider.__aexit__(exc_type, exc_val, exc_tb)
        pass


async def initialize_config(name, obj, logger):
    """Initialize RunnerConfig and parse parameters."""
    config = RunnerConfig()
    config.logger = logger
    try:
        config.item = parse_params(name, obj)
        config.spider = AsyncSpider(api_key=api_config.spider_api_key)
    except ParamError as e:
        raise GoodbyeBecauseOfError(f"api参数异常 {e}")
    except Exception as e:
        logger.error(f'初始化时异常 {type(e)} {e}')
        raise GoodbyeBecauseOfError(e)

    return config


class GoodbyeBecauseOfError(Exception):
    pass


@param_check
def parse_params(name, obj):
    """Parse input parameters from the WebSocket message."""
    check_key(obj)
    item = QueryItem()
    item.name = name
    item.pages = get_int(obj, 'pages', a=1, default=1)
    item.year_low = get_int(obj, 'year_low', a=1900, b=2024)
    item.year_high = get_int(obj, 'year_high', a=1900, b=2024)
    item.min_cite = get_int(obj, 'min_cite')
    item.ignore_bibtex = get_bool(obj, 'ignore_bibtex', default=False)
    return item
