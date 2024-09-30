from fastapi import Path, WebSocket
from starlette.websockets import WebSocketDisconnect
import asyncio
import traceback
from app.params_tool import check_key, get_int, get_bool, ParamError, param_check
from run.pipline1 import QueryItem, RunnerConfig
from crawl import nodriver_tool, by_scholarly
from run.Runner1 import Runner1
from data import api_config

from api_tool import app


@app.websocket("/query1/{name}")
async def query1(
        websocket: WebSocket,
        name: str = Path(..., title="terms to be searched"),
):
    await websocket.accept()

    from log_config import logger
    logger.info(f'新连接 {websocket}')

    async def goodbye(msg_obj: dict):
        await websocket.send_json(msg_obj)
        await websocket.close()

    try:
        obj = await websocket.receive_json()
        config = await initialize_config(name, obj, logger)
        await handle_tasks(websocket, config)
    except GoodbyeBecauseOfError as e:
        await goodbye({'error': str(e)})
    except WebSocketDisconnect as e:
        logger.error(f"Connection closed {e}")
    except Exception as e:
        logger.error(f'query1 吸收异常 {e} ' + traceback.format_exc())


class GoodbyeBecauseOfError(Exception):
    pass


async def initialize_config(name, obj, logger):
    """Initialize RunnerConfig and parse parameters."""
    config = RunnerConfig()
    config.logger = logger

    try:
        config.item = parse_params(name, obj)
        config.browser = await nodriver_tool.create(logger)
        if api_config.scholarly_use_proxy:
            assert by_scholarly.use_proxy()
    except ParamError as e:
        raise GoodbyeBecauseOfError(f"api参数异常 {e}")
    except InitializeError as e:
        raise GoodbyeBecauseOfError(e)

    return config


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


class InitializeError(Exception):
    pass


async def create_browser(logger):
    try:
        browser = await nodriver_tool.create(logger)
    except Exception as e:
        logger.error(e)
        raise InitializeError(f'nodriver启动浏览器出错 {e}')
    return browser


async def initialize_scholarly(logger):
    if not api_config.scholarly_use_proxy:
        return

    logger.info('准备设置 scholarly IP代理')
    try:
        succeed = by_scholarly.use_proxy()
        logger.debug(f'设置 scholarly IP代理 {"succeed" if succeed else "failed"}')
        assert succeed
    except Exception as e:
        raise InitializeError(f'设置 scholarly IP代理出错 {e}')


async def handle_tasks(websocket, config):
    """Manage task execution and heartbeat."""
    try:
        runner = Runner1(config)
        task = asyncio.create_task(runner.finish())

        while not task.done():
            await websocket.send_json({'type': 'Heartbeat', 'progress': runner.get_progress()})
            await asyncio.sleep(5)

        if task.exception():
            await websocket.send_json(
                {'type': 'Result', 'error': task.exception(), 'data': runner.deliver_pubs()})
        else:
            await websocket.send_json(
                {'type': 'Result', 'error': None, 'data': runner.deliver_pubs()})

        await websocket.close()
    finally:
        await cleanup_tasks(config)


async def cleanup_tasks(config):
    """Cancel all pending tasks and clean up resources."""
    logger = config.logger
    for task in asyncio.all_tasks():
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f'cleanup_tasks 吸收异常 {type(e)} {e}')

    browser = config.browser
    logger.info('准备关闭浏览器')
    try:
        browser.stop()  # 标准关闭
    except Exception as e:
        logger.info('关闭浏览器异常 ' + traceback.format_exc())
