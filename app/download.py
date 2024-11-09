from datetime import datetime

from fastapi import Path, WebSocket
from starlette.websockets import WebSocketDisconnect
import asyncio
import traceback

from download.context import GoodbyeBecauseOfError, initialize_config
from download.Runner import Runner

from app.api_tool import app
from tools.log_tool import create_logger


@app.websocket("/download")
async def download(websocket: WebSocket):
    await websocket.accept()
    logger = create_logger("download", datetime.now())
    logger.info(f'/download 新连接 {websocket.url}')
    try:
        obj = await websocket.receive_json()
        config = await initialize_config(obj, logger)
        async with config:
            await run_task(websocket, config)

    except GoodbyeBecauseOfError as e:
        await websocket.send_json({'error': str(e)})
    except WebSocketDisconnect as e:
        logger.error(f"/download 意外断开连接 {e}")
    except Exception as e:
        logger.error(f'/download 吸收异常 {e} ' + traceback.format_exc())
    finally:
        await websocket.close()


async def run_task(websocket, config):
    """Manage task execution and heartbeat."""
    logger = config.logger
    runner = Runner(config)
    task = runner.finish()  # 用协程
    try:
        result = await task
        await websocket.send_json({'result': result})
    except Exception as e:
        raise GoodbyeBecauseOfError(e)
