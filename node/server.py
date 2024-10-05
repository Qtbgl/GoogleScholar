from datetime import datetime

import websockets

from node.server_handler import handle_client
from tools.log_tool import create_logger
from data import api_config


async def open_server():
    # 创建 logger 实例
    logger = create_logger('subs', datetime.now())
    port = api_config.sub_node_port

    async def handler(websocket, path):
        await handle_client(websocket, logger)
        server.close()

    server = await websockets.serve(handler, "localhost", port)
    logger.info(f"WebSocket server started on ws://localhost:{port}")

    # 等待服务器被关闭
    await server.wait_closed()
    logger.info("Server has been shut down.")


# 在项目根路径中调用
