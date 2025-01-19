import os

from download.common_tool import GoodbyeBecauseOfError
from download.Runner import Runner, TaskConfig

from app.api_tool import project_root
from app.params_tool import param_check, check_key, ParamError


async def remote_download(obj, logger):
    config = await init_config(obj, logger)

    # """Manage task execution ~~and heartbeat~~."""
    runner = Runner(config)
    task = runner.finish()  # 用协程
    try:
        result = await task
    except Exception as e:
        raise GoodbyeBecauseOfError(e)

    return result


async def init_config(obj, logger):
    config = TaskConfig()
    config.logger = logger
    try:
        config.quests = parse_params(obj)
        # 下载目录
        save_dir = os.path.join(project_root, 'data', 'download')
        os.makedirs(save_dir, exist_ok=True)
        config.pdf_save_dir = save_dir
    except ParamError as e:
        raise GoodbyeBecauseOfError(f"api参数异常 {e}")
    except Exception as e:
        logger.error(f'初始化时异常 {type(e)} {e}')
        raise GoodbyeBecauseOfError(e)

    return config


@param_check
def parse_params(obj):
    """Parse input parameters from the WebSocket message."""
    check_key(obj)
    for q in obj['quests']:
        assert q['quest_id']
        # 确保有下载链接
        assert q['eprint_url'] or q['title']

    return obj['quests']
