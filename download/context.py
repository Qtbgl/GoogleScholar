import logging

from app.api_tool import project_root
from app.params_tool import param_check, check_key, get_int, get_bool, ParamError
from data import api_config


class Config:
    logger: logging.Logger
    pubs: list[dir]
    root_path: str

    async def __aenter__(self):
        pass

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


async def initialize_config(obj, logger):
    config = Config()
    config.logger = logger
    try:
        config.pubs = parse_params(obj)
        config.root_path = project_root
    except ParamError as e:
        raise GoodbyeBecauseOfError(f"api参数异常 {e}")
    except Exception as e:
        logger.error(f'初始化时异常 {type(e)} {e}')
        raise GoodbyeBecauseOfError(e)

    return config


class GoodbyeBecauseOfError(Exception):
    pass


@param_check
def parse_params(obj):
    """Parse input parameters from the WebSocket message."""
    check_key(obj)
    pubs = obj['pubs']
    for pub in pubs:
        assert pub['url']  # 确保有下载链接

    return pubs
