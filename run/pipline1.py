import os
import sys
import asyncio.subprocess
import typing

import websockets

from app.params_tool import param_check, check_key, get_int, get_bool, ParamError
from data import api_config

from crawl import by_scholarly


class QueryItem:
    name: str
    pages: int
    year_low: int
    year_high: int
    min_cite: int
    ignore_bibtex: bool

    # def __init__(self, name, pages, year_low=None, year_high=None, min_cite=None, ignore_bibtex=False):
    #     self.name = name
    #     self.pages = pages
    #     self.year_low = year_low
    #     self.year_high = year_high
    #     self.min_cite = min_cite
    #     self.ignore_bibtex = ignore_bibtex

    def __str__(self):
        return str(self.__dict__)


class ReadResult:
    def get_progress(self):
        pass

    def deliver_pubs(self):
        pass


class RunnerConfig:
    logger: typing.Any
    item: QueryItem
    websocket: websockets.WebSocketClientProtocol
    node_process: asyncio.subprocess.Process


class WriteResult:
    def success_fill(self, pub):
        pass

    def fail_to_fill(self, pub, error):
        pass


class GoodbyeBecauseOfError(Exception):
    pass


class RunnerContext:
    def __init__(self):
        self.config = RunnerConfig()
        self.config.node_process = None
        self.config.websocket = None

    async def initialize_config(self, name, obj, logger):
        """Initialize RunnerConfig and parse parameters."""
        config = self.config
        config.logger = logger
        try:
            config.item = parse_params(name, obj)
            config.node_process = await create_node_process()
            config.websocket = await connect_to_node(logger)
            await initialize_scholarly(logger)
        except ParamError as e:
            raise GoodbyeBecauseOfError(f"api参数异常 {e}")
        except Exception as e:
            raise GoodbyeBecauseOfError(e)

        return config

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """关闭 WebSocket 连接和 node 进程"""
        logger = self.config.logger
        websocket = self.config.websocket

        if websocket is not None:
            try:
                await websocket.close()
                logger.info("WebSocket connection closed.")
            except Exception as e:
                logger.error(e)

        node_process = self.config.node_process
        if node_process is not None:
            if node_process.returncode is None:
                logger.info("Node process is still running.")
                try:
                    node_process.terminate()
                    # 等待进程结束，设置超时
                    await asyncio.wait_for(node_process.wait(), 60)
                    logger.info("Node process terminated.")
                except Exception as e:
                    logger.error(e)
                    node_process.kill()  # 强制结束进程
                    await node_process.wait()  # 等待进程完全终止
                    logger.info("Node process killed.")


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


async def create_node_process():
    # 获取项目根目录
    script_path = os.path.abspath(sys.argv[0])
    project_root = os.path.dirname(script_path)
    node_script_path = os.path.join(project_root, 'node.py')

    # 启动 node.py 文件
    node_process = await asyncio.create_subprocess_exec(
        'python', node_script_path,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    return node_process


async def connect_to_node(logger):
    # 获取端口并构建 URL
    port = api_config.sub_node_port
    url = f"ws://localhost:{port}"
    websocket_connection = await websockets.connect(url)
    logger.info(f"连接到任务结点 {url}")
    return websocket_connection


async def initialize_scholarly(logger):
    if api_config.scholarly_use_proxy:
        logger.info('准备设置 scholarly IP代理')
        succeed = by_scholarly.use_proxy()
        logger.debug(f'设置 scholarly IP代理 {"succeed" if succeed else "failed"}')
        assert succeed, '设置 scholarly IP代理失败'
