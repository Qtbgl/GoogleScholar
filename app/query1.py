from fastapi import Path, WebSocket
from starlette.websockets import WebSocketDisconnect

from api_tool import app


@app.websocket("/query1/{name}")
async def query1(
    websocket: WebSocket,
    name: str = Path(..., title="terms to be searched"),
):
    await websocket.accept()
    obj = await websocket.receive_json()

    import asyncio
    import traceback
    from app.params_tool import check_key, get_int, get_bool, ParamError, param_check

    async def goodbye(msg_obj: dict):
        await websocket.send_json(msg_obj)
        await websocket.close()  # 关闭连接

    @param_check
    def parse_params():
        check_key(obj)
        item = QueryItem()
        item.name = name
        item.pages = get_int(obj, 'pages', a=1, default=1)
        item.year_low = get_int(obj, 'year_low', a=1900, b=2024)
        item.year_high = get_int(obj, 'year_high', a=1900, b=2024)
        item.min_cite = get_int(obj, 'min_cite')
        item.ignore_bibtex = get_bool(obj, 'ignore_bibtex', default=False)
        return item

    # 构建api参数
    from log_config import logger
    logger.info('query1 new call')
    try:
        from run.pipline1 import QueryItem, RunnerConfig
        config = RunnerConfig()
        config.logger = logger
    except Exception as e:
        logger.error('未知异常 ' + traceback.format_exc())
        return

    # 解析api参数
    try:
        config.item = parse_params()
    except ParamError as e:
        await goodbye({"error": f"api参数异常 {e}"})
        return
    except Exception as e:
        logger.error('未知异常 ' + traceback.format_exc())
        return

    # 创建资源
    try:
        from crawl import nodriver_tool
        config.browser = await nodriver_tool.create(logger)
    except Exception as e:
        await goodbye({'error': f'nodriver启动浏览器出错 {e}'})
        return

    from data import api_config
    if api_config.scholarly_use_proxy:
        logger.info('准备设置 scholarly IP代理')
        try:
            from crawl import by_scholarly
            succeed = by_scholarly.use_proxy()
            logger.debug(f'设置 scholarly IP代理 {"succeed" if succeed else "failed"}')
            assert succeed
        except Exception as e:
            await goodbye({'error': f'scholarly setting Proxy failed {e}'})
            return

    try:
        from run.Runner1 import Runner1
        runner = Runner1(config)
        # 创建任务
        task = asyncio.create_task(runner.finish())
    except Exception as e:
        await goodbye({'error': f'创建任务时出错 {e}'})
        return

    result = {'type': 'Result', 'error': None}
    try:
        while not task.done():
            # 获取进度
            obj = {'type': 'Heartbeat', 'progress': runner.get_progress()}
            await websocket.send_json(obj)  # 发送心跳消息
            await asyncio.sleep(5)

        try:
            await task
        except Exception as e:
            # 异常信息返回，不抛出
            logger.error(f'task error retrieved: {e}')
            result['error'] = str(e)
        finally:
            # 返回任务执行结果
            result['data'] = runner.deliver_pubs()
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
            logger.info('---------------------------------------------Task not done, canceling...')
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                logger.info("---------------------------------------------Task was cancelled!")
