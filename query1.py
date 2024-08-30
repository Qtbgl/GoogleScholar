import asyncio
import json
import traceback
from fastapi import Path, WebSocket
from starlette.websockets import WebSocketDisconnect

from context import app


@app.websocket("/query1/{name}")
async def query1(
    websocket: WebSocket,
    name: str = Path(..., title="terms to be searched"),
):
    await websocket.accept()

    async def goodbye(msg_obj: dict):
        await websocket.send_text(json.dumps(msg_obj))
        await websocket.close()  # 关闭连接

    # 解析api参数
    try:
        data = await websocket.receive_text()
        obj = json.loads(data)

        from tools.param_tools import Params, check_key
        check_key(obj)

        from crawl.by_scholarly import QueryItem
        p = Params(obj)
        item = QueryItem(
            name=name,
            pages=p.pages,
            year_low=p.year_low,
            year_high=p.year_high,
            min_cite=p.min_cite,
        )
    except Exception as e:
        await goodbye({"error": f"api参数异常 {e}"})
        return

    # 创建资源
    from log_config import logger
    logger.info('query1 new call')
    try:
        from crawl.by_nodiver import Crawl
        crawl = await Crawl.create(logger)
    except Exception as e:
        await goodbye({'error': f'nodriver启动浏览器出错 {e}'})
        return

    from crawl.by_scholarly import use_proxy
    succeed = use_proxy()
    if not succeed:
        await goodbye({'error': f'scholarly setting Proxy failed'})
        return

    try:
        from record.Record1 import Record1
        record = Record1(logger)
    except Exception as e:
        await goodbye({'error': f'record创建出错 {e}'})
        return

    try:
        from run.Runner1 import Runner1
        runner = Runner1(crawl, record, logger)
        # 创建任务
        task = asyncio.create_task(runner.run(item))
    except Exception as e:
        await goodbye({'error': f'创建任务时出错 {e}'})
        return

    result = {'type': 'Result', 'error': None}
    try:
        while not task.done():
            # 获取进度
            obj = {'type': 'Heartbeat', 'progress': record.get_progress()}
            await websocket.send_text(json.dumps(obj))  # 发送心跳消息
            await asyncio.sleep(5)

        try:
            await task
        except Exception as e:
            # 异常信息返回，不抛出
            logger.error(f'task error retrieved: {e}')
            result['error'] = str(e)
        finally:
            # 返回任务执行结果
            result['data'] = record.deliver_pubs()
            await goodbye(msg_obj=result)

    except WebSocketDisconnect as e:
        logger.error(f"Connection closed: {type(e)} {e}")
    except Exception as e:
        logger.error(f"Unexpected Error: {type(e)} {e} \n{traceback.format_exc()}")
        try:
            await websocket.close()
        except Exception as e:
            logger.error(f"Unexpected Error: {type(e)} {e}")
    finally:
        if not task.done():
            logger.info('Task not done, canceling...')
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                logger.info("Task was cancelled!")
