import asyncio
import json
import traceback
from fastapi import Path, Query, WebSocket
from starlette.websockets import WebSocketDisconnect

from context import app


async def goodbye(websocket: WebSocket, msg_obj: dict):
    await websocket.send_text(json.dumps(msg_obj))
    await websocket.close()  # 关闭连接


@app.websocket("/query2/{name}")
async def query2(
    websocket: WebSocket,
    name: str = Path(..., title="terms to be searched"),
):
    await websocket.accept()
    # 解析api参数
    try:
        data = await websocket.receive_text()
        obj = json.loads(data)

        from secure import Params, check_key
        check_key(obj)
        assert obj.get('serpdog_key') is not None, '缺少serpdog_key'

        # 创建item
        from crawl.by_serpdog import QueryItem, Payload, get_payload
        p = Params(obj)
        item = QueryItem(
            name=name, pages=p.pages, min_cite=p.min_cite,
            payload=Payload(
                api_key=obj['serpdog_key'],
                as_yhi=p.year_high,
                as_ylo=p.year_low
            ))
    except Exception as e:
        await goodbye(websocket, {"error": f"api参数异常 {e}"})
        return

    await do_query(websocket, item)


async def do_query(websocket: WebSocket, item) -> None:
    # 创建资源
    from log_config import logger
    logger.info('query2 new call')
    try:
        from crawl.by_nodiver import Crawl
        crawl = await Crawl.create(logger)
    except Exception as e:
        await goodbye(websocket, {'error': f'nodriver启动浏览器出错 {e}'})
        return

    try:
        from record.Record2 import Record2
        record = Record2(logger)
    except Exception as e:
        await goodbye(websocket, {'error': f'record创建出错 {e}'})
        return

    # 使用nodriver爬取网页时，创建新的事件循环
    from run.Runner2 import Runner2
    runner = Runner2(crawl, record, logger)
    # 创建任务
    task = asyncio.create_task(runner.run(item))
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
            await goodbye(websocket, msg_obj=result)

    except WebSocketDisconnect as e:
        logger.error(f"Connection closed: {e}")
    except Exception as e:
        logger.error(f"Unexpected Error: {type(e)} {e} \n{traceback.format_exc()}")
        try:
            await websocket.close()
        except Exception as e:
            logger.error(f"Unexpected Error: {type(e)} {e}")
    finally:
        if not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                logger.info("Task was cancelled!")
