import asyncio
import json
import threading
import traceback
from fastapi import Path, Query, WebSocket

from context import app
from secure import check_key, get_general_params


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
        check_key(obj)
        # 创建item
        from crawl.by_serpdog import QueryItem
        params = get_general_params(obj)  # 通用参数
        # remap参数
        payload = dict(
            pages=params['pages'],
            api_key=obj.get('serpdog_key'),  # 特殊
            as_yhi=params.get('year_high'),
            as_ylo=params.get('year_low'),
        )
        item = QueryItem(name, **payload)

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

    # 线程执行结果
    result = {'type': 'Result'}

    def new_call():
        # 使用nodriver爬取网页时，创建新的事件循环
        logger.info('进入任务线程')
        loop = asyncio.new_event_loop()  # 为该线程创建新的事件循环
        asyncio.set_event_loop(loop)
        try:
            from run.Runner2 import Runner2
            runner = Runner2(crawl, record, logger)
            # 创建任务
            task = runner.run(item)
            loop.run_until_complete(task)  # 运行异步任务
            result['error'] = None
        except Exception as e:
            logger.error(f'new_call返回异常 {e}')
            result['error'] = str(e)   # 异常信息返回，不抛出
        finally:
            result['data'] = record.deliver_pubs()
            loop.close()  # 关事件循环
            logger.info('已关闭任务线程的事件循环')

    closed = False
    try:
        # 在后台线程中运行长任务
        thread = threading.Thread(target=new_call)
        thread.start()
        while thread.is_alive():
            # 获取进度
            obj = {'type': 'Heartbeat', 'progress': record.get_progress()}
            await websocket.send_text(json.dumps(obj))  # 发送心跳消息
            await asyncio.sleep(5)

        thread.join()
        # 返回总结果
        await goodbye(websocket, msg_obj=result)
        closed = True

    except Exception as e:  # 默认是连接问题
        logger.error(f"Connection closed: \n{traceback.format_exc()}")
    finally:
        if not closed:
            await websocket.close()  # 关闭连接
