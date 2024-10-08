import asyncio
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
            async for message in websocket:  # 客户端关闭连接时，异步生成器自然结束
                obj = json.loads(message)
                # logger.debug(f'主进程传入参数 {obj}')
                pubs = parse_params(obj)

                # 创建并执行任务
                task = asyncio.create_task(filler.finish(pubs))

                # 等待任务完成并检查连接状态
                while not task.done():
                    await asyncio.sleep(3)
                    if websocket.closed:  # 检查连接状态
                        logger.error("在处理任务时，WebSocket 连接已关闭")
                        task.cancel()
                        break

                # 自动抛出异常，或等待取消异常（最优化代码逻辑）
                await task

                logger.info('已完成本次任务')
                await websocket.send(json.dumps({'pubs': pubs}))
                logger.info('已发送结果')

        except asyncio.CancelledError as e:
            logger.error(f'子结点被取消 {e}')
        except ErrorToTell as e:
            await websocket.send(json.dumps({'error': str(e)}))
        except websockets.exceptions.ConnectionClosed as e:
            logger.error(f"连接意外中断 {e}")
        except Exception as e:
            logger.error(f'未知异常 {traceback.format_exc()}')
        finally:
            if not websocket.closed:
                await websocket.close()


def parse_params(obj):
    try:
        pubs = obj['pubs']
        for pub in pubs:
            assert 'task_id' in pub
            assert 'url' in pub
            assert 'title' in pub
            assert 'cut' in pub
        return pubs
    except (KeyError, AssertionError) as e:
        raise ErrorToTell(f'请求参数异常 {e}')


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
            try:
                browser = self.config.browser
                browser.stop()  # 标准关闭
                logger.info('已关闭浏览器')
            except Exception as e:
                logger.info('关闭浏览器异常 ' + traceback.format_exc())
