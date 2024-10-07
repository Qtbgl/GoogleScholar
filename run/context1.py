import asyncio
import os
import sys
import traceback

import websockets

from run.pipline1 import RunnerConfig, GoodbyeBecauseOfError, QueryItem
from app.params_tool import param_check, check_key, get_int, get_bool, ParamError
from data import api_config

from crawl import by_scholarly


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
            config.node_process, config.websocket = await create_node_process(logger)
            await initialize_scholarly(logger)
        except ParamError as e:
            raise GoodbyeBecauseOfError(f"api参数异常 {e}")
        except Exception as e:
            logger.error(f'初始化时异常 {type(e)} {e}')
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


async def create_node_process(logger):
    # 获取项目根目录
    script_path = os.path.abspath(sys.argv[0])
    project_root = os.path.dirname(script_path)
    node_script_path = os.path.join(project_root, 'start_node.py')

    # 指定 Miniconda 环境的 Python 解释器路径
    python_executable = api_config.python_executable

    # 启动 node.py 文件
    node_process = await asyncio.create_subprocess_exec(
        python_executable, node_script_path,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    try:
        websocket = await connect_to_node(node_process, logger)
        return node_process, websocket
    except Exception as e:
        if node_process.returncode is not None:
            logger.error(f"子结点启动失败，准备结束进程")
            try:
                node_process.kill()  # 终止子进程
                await node_process.wait()  # 等待进程完全终止
                logger.info("已结束子结点进程")
            except ProcessLookupError:
                logger.error("尝试终止进程时出错：进程不存在。")
            except Exception as e:
                logger.error(f'关闭进程失败 {traceback.format_exc(chain=False)}')
        raise


async def connect_to_node(node_process, logger, timeout=60):
    # 记录开始时间
    loop = asyncio.get_running_loop()
    start_time = loop.time()

    # 连接 WebSocket，直到成功
    port = api_config.sub_node_port
    url = f"ws://localhost:{port}"
    while True:
        await asyncio.sleep(5)  # 等待 5 秒后尝试
        # 检查进程存活
        if node_process.returncode is not None:
            stderr_output = await node_process.stderr.read()
            stderr_output = stderr_output.decode().strip()
            exit_code = node_process.returncode
            logger.error(f"Node Process意外退出 {exit_code}, Error output: {stderr_output}")
            raise Exception(f"Node Process意外退出 {exit_code}")

        # 检查结点已启动
        try:
            return await websockets.connect(url)
        except ConnectionRefusedError:
            logger.error(f"连接失败，正在重试...")

        # 检查是否超时
        if loop.time() - start_time > timeout:
            raise asyncio.TimeoutError(f"连接超时，无法连接到 {url}")


async def initialize_scholarly(logger):
    if api_config.scholarly_use_proxy:
        logger.info('准备设置 scholarly IP代理')
        succeed = by_scholarly.use_proxy()
        logger.debug(f'设置 scholarly IP代理 {"succeed" if succeed else "failed"}')
        assert succeed, '设置 scholarly IP代理失败'
