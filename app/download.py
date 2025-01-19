from datetime import datetime

from fastapi import Path, WebSocket
from starlette.responses import FileResponse
from starlette.websockets import WebSocketDisconnect
import asyncio
import traceback

from download.common_tool import GoodbyeBecauseOfError
from download.Runner import Runner

from app.api_tool import app
from tools.log_tool import create_logger

from download.task_remote import remote_download


@app.websocket("/download/remote")
async def download(websocket: WebSocket):
    await websocket.accept()
    logger = create_logger("download", datetime.now())
    logger.info(f'/download 新连接 {websocket.url}')
    try:
        obj = await websocket.receive_json()  # （风险）可能参数传入不对时，有不同的业务
        result = await remote_download(obj, logger)
        await websocket.send_json({'result': result})
    except GoodbyeBecauseOfError as e:
        await websocket.send_json({'error': str(e)})
    except WebSocketDisconnect as e:
        logger.error(f"/download 意外断开连接 {e}")
    except Exception as e:
        logger.error(f'/download 吸收异常 {e} ' + traceback.format_exc())
    finally:
        await websocket.close()


# 文件下载接口
@app.get("/download/remote/get/{file_remote}")
async def download_get(file_remote: str):
    from app.api_tool import project_root
    import os
    file_path = os.path.join(project_root, 'data', 'download', file_remote)
    if os.path.exists(file_path):
        return FileResponse(file_path)
    else:
        return {"error": "File not found"}
