import json
import traceback

from starlette.websockets import WebSocketDisconnect

from context import app

from fastapi import WebSocket, Path

from tools.param_tools import is_key


@app.websocket("/download/{api_key}")
async def download(
    websocket: WebSocket,
    api_key: str = Path(...),
):
    await websocket.accept()

    async def goodbye(msg_obj: dict):
        await websocket.send_text(json.dumps(msg_obj))
        await websocket.close()  # 关闭连接

    if not is_key(api_key):
        await goodbye({"error": f"Invalid API key!"})
        return

    # 创建资源
    from test_code.log_config import logger
    try:
        from crawl.by_nodiver import Crawl
        crawl = await Crawl.create(logger)
    except Exception as e:
        await goodbye({'error': f'nodriver启动浏览器出错 {e}'})
        return

    from run.Downloader import Downloader
    down = Downloader(crawl, logger)
    # TODO: 激活pdf下载

    try:
        while True:
            data = await websocket.receive_text()

            # 解析api参数
            obj = json.loads(data)
            if obj.get('quit'):
                await websocket.close()
                return

            url = obj.get('url')
            if not url:
                await goodbye({'error': '参数格式不对'})
                return

            try:
                result = await down.run(url)
                await websocket.send_json()

            except Exception as e:
                logger.error(f'task error retrieved: {e}')
                await goodbye({'error': str(e)})
                return

    except WebSocketDisconnect as e:
        logger.error(f"Connection closed: {type(e)} {e}")
    except Exception as e:
        logger.error(f"Unexpected Error: {type(e)} {e} \n{traceback.format_exc()}")
        try:
            await websocket.close()
        except Exception as e:
            logger.error(f"Unexpected Error: {type(e)} {e}")
