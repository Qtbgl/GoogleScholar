import websockets
import json

from crawl import nodriver_tool
from node.FillPubsAbstract import FillPubsAbstract
from node.node_pipline import TaskConfig, ErrorToTell


async def handle_client(websocket: websockets.WebSocketServerProtocol, logger):
    logger.info("已连接")
    try:
        logger.info("开始创建资源")
        config = await initialize_config(logger)
        filler = FillPubsAbstract(config)

        async for message in websocket:
            obj = json.loads(message)
            if obj.get('end'):
                return

            pubs = get_pubs(obj)
            await filler.finish(pubs)
            await websocket.send(json.dumps(pubs))

    except ErrorToTell as e:
        await websocket.send(json.dumps({'error': str(e)}))
    except websockets.exceptions.ConnectionClosed as e:
        logger.error(f"连接意外中断 {e}")
    except Exception as e:
        logger.error(f'未知异常 {e}')
    finally:
        await websocket.close()


def get_pubs(obj):
    try:
        pubs = obj['pubs']
        for pub in pubs:
            assert 'task_id' in pub
            assert 'url' in pub
            assert 'title' in pub
            assert 'cut' in pub

    except (KeyError, AssertionError) as e:
        raise ErrorToTell(f'请求参数异常 {e}')


async def initialize_config(logger):
    """Initialize RunnerConfig and parse parameters."""
    config = TaskConfig()
    config.logger = logger
    try:
        browser = await nodriver_tool.create(logger)
    except Exception as e:
        logger.error(e)
        raise ErrorToTell(f'nodriver启动浏览器出错 {e}')

    config.browser = browser
    return config
