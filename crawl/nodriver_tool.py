import asyncio
import os
import traceback

import nodriver
from nodriver.core.browser import Browser, Config


async def create(logger):
    """
    :return: 可能抛出浏览器打开异常
    """
    config = Config(headless=True)
    # 创建实例，一般不会报错
    # 保留实例，以关闭浏览器进程
    browser = Browser(config)
    try:
        await browser.start()
    except Exception as e1:
        logger.error('浏览器启动失败 ' + traceback.format_exc())
        try:
            stop(browser, logger)
        except Exception as e2:
            logger.error('浏览器关闭进程时出错 ' + traceback.format_exc())
            raise e2 from e1

        raise e1

    logger.info('成功打开浏览器')
    return browser


class BrowserAuto:
    def __init__(self, browser: nodriver.Browser, logger):
        self.logger = logger
        self.browser = browser

    async def __aenter__(self):  # 不在此处开启浏览器
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # 关闭浏览器
        self.logger.info('准备关闭浏览器')
        try:
            self.browser.stop()  # 标准关闭
        except Exception as e:
            self.logger.info(traceback.format_exc())
            raise e  # 再次抛出，不影响原异常


def stop(browser, logger):
    """
    :param browser: 关闭浏览器进程，代码复制于nodriver
    :param logger:
    :return:
    """
    self = browser
    assert isinstance(self._process, asyncio.subprocess.Process), '浏览器进程不存在'
    logger.info('进入自定义函数，开始关闭进程')
    for _ in range(3):
        try:
            self._process.terminate()
            logger.info(
                "terminated browser with pid %d successfully" % self._process.pid
            )
            break
        except (Exception,):
            try:
                self._process.kill()
                logger.info(
                    "killed browser with pid %d successfully" % self._process.pid
                )
                break
            except (Exception,):
                try:
                    if hasattr(self, "browser_process_pid"):
                        os.kill(self._process_pid, 15)
                        logger.info(
                            "killed browser with pid %d using signal 15 successfully"
                            % self._process.pid
                        )
                        break
                except (TypeError,):
                    logger.info("typerror", exc_info=True)
                    pass
                except (PermissionError,):
                    logger.info(
                        "browser already stopped, or no permission to kill. skip"
                    )
                    pass
                except (ProcessLookupError,):
                    logger.info("process lookup failure")
                    pass
                except (Exception,):
                    raise
        self._process = None
        self._process_pid = None
