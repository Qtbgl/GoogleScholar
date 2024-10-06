import traceback

import websockets
import json

from crawl import nodriver_tool
from node.FillPubsAbstract import FillPubsAbstract
from node.node_pipline import TaskConfig, ErrorToTell


async def handle_client(websocket: websockets.WebSocketServerProtocol, logger):
    logger.info("已连接")
    with FillPubsContext() as context:
        try:
            logger.info("开始创建任务资源")
            filler = await context.create(logger)
            async for message in websocket:
                obj = json.loads(message)
                if obj.get('end'):
                    return
                pubs = parse_params(obj)
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


class FillPubsContext:
    def __init__(self):
        self.config = TaskConfig()
        self.config.browser = None

    def __enter__(self):
        return self

    async def create(self, logger):
        config = self.config
        config.logger = logger
        try:
            browser = await nodriver_tool.create(logger)
        except Exception as e:
            logger.error(e)
            raise ErrorToTell(f'nodriver启动浏览器出错 {e}')

        config.browser = browser
        return FillPubsAbstract(self.config)

    def __exit__(self, exc_type, exc_val, exc_tb):
        logger = self.config.logger
        if self.config.browser:
            logger.info('准备关闭浏览器')
            try:
                browser = self.config.browser
                browser.stop()  # 标准关闭
            except Exception as e:
                logger.info('关闭浏览器异常 ' + traceback.format_exc())


def parse_params(obj):
    try:
        pubs = obj['pubs']
        for pub in pubs:
            assert 'task_id' in pub
            assert 'url' in pub
            assert 'title' in pub
            assert 'cut' in pub

    except (KeyError, AssertionError) as e:
        raise ErrorToTell(f'请求参数异常 {e}')
