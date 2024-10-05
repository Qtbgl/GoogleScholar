from fastapi import Path, WebSocket
from starlette.websockets import WebSocketDisconnect
import asyncio
import traceback
from run.pipline1 import RunnerContext, GoodbyeBecauseOfError
from run.Runner1 import Runner1

from app.api_tool import app


@app.websocket("/query1/{name}")
async def query1(
        websocket: WebSocket,
        name: str = Path(..., title="terms to be searched"),
):
    await websocket.accept()

    from log_config import logger
    logger.info(f'新连接 {websocket.url}')

    async def goodbye(msg_obj: dict):
        await websocket.send_json(msg_obj)
        await websocket.close()

    with RunnerContext() as context:
        try:
            obj = await websocket.receive_json()
            config = await context.initialize_config(name, obj, logger)
            await run_task(websocket, config)
        except GoodbyeBecauseOfError as e:
            await goodbye({'error': str(e)})
        except WebSocketDisconnect as e:
            logger.error(f"Connection closed {e}")
        except Exception as e:
            logger.error(f'query1 吸收异常 {e} ' + traceback.format_exc())


async def run_task(websocket, config):
    """Manage task execution and heartbeat."""
    logger = config.logger
    runner = Runner1(config)
    task = asyncio.create_task(runner.finish())
    try:
        while not task.done():
            await websocket.send_json({'type': 'Heartbeat', 'progress': runner.get_progress()})
            await asyncio.sleep(5)

        # task因为异常而结束时
        if task.exception():
            await websocket.send_json(
                {'type': 'Result', 'error': str(task.exception()), 'data': runner.deliver_pubs()})
        else:
            await websocket.send_json(
                {'type': 'Result', 'error': None, 'data': runner.deliver_pubs()})

        await websocket.close()
    finally:
        if not task.done():
            logger.info('---------------------------------------------Task not done, canceling...')
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                logger.info("---------------------------------------------Task was cancelled!")


# async def cleanup_tasks(config):
#     """Cancel all pending tasks and clean up resources."""
#     logger = config.logger
#     for task in asyncio.all_tasks():
#         task.cancel()
#         try:
#             await task
#         except asyncio.CancelledError:
#             pass
#         except Exception as e:
#             logger.error(f'cleanup_tasks 吸收异常 {type(e)} {e}')
#
#     browser = config.browser
#     logger.info('准备关闭浏览器')
#     try:
#         browser.stop()  # 标准关闭
#     except Exception as e:
#         logger.info('关闭浏览器异常 ' + traceback.format_exc())
