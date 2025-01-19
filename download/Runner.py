import asyncio
import logging
import traceback

import download.by_pdf_link as by_link
import download.by_scihub as by_scihub
from download.common_tool import get_errs_info


class TaskConfig:
    logger: logging.Logger
    quests: list[dict]
    pdf_save_dir: str


class Runner:
    def __init__(self, config: TaskConfig):
        # 依赖对象
        self.config = config

    async def get_pdf(self, quest):
        save_dir = self.config.pdf_save_dir
        logger = self.config.logger
        errs = ()
        if quest.get('eprint_url'):
            # 尝试直接爬取链接
            try:
                saved_name = by_link.download_pdf(quest.get('eprint_url'), save_dir, logger)
                return {
                    'file_remote': saved_name,
                    'quest_id': quest['quest_id'],
                    'get_by': 'eprint_url',
                }
            except by_link.DownloadFailed as e:
                errs += (e,)

        if quest.get('title'):
            # 尝试从sci-hub上找相同的标题
            try:
                name = by_scihub.download_pdf(quest.get('title'), 'title', save_dir, logger)
                return {
                    'file_remote': name,
                    'quest_id': quest['quest_id'],
                    'get_by': 'title_sci-hub',
                }
            except by_link.DownloadFailed as e:
                errs += (e,)

        # 未成功下载
        return {
            'quest_id': quest['quest_id'],
            'error': get_errs_info(errs)
        }

    async def finish(self):
        logger = self.config.logger
        logger.info(f'开始下载任务')
        quests = self.config.quests
        tasks = [self.get_pdf(q) for q in quests]
        tasks = list(map(asyncio.create_task, tasks))
        try:
            result = await asyncio.gather(*tasks)  # 结果返回
            return result
        except Exception as e:
            logger.error('未预料的异常' + '\n' + traceback.format_exc())
            raise e
        finally:
            for task in tasks:
                task.cancel()  # 取消未完成的任务
            await asyncio.gather(*tasks, return_exceptions=True)
            logger.debug(f'所有下载任务已结束')
