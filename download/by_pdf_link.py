import os.path

import aiohttp
from aiohttp import ClientResponseError

from download.common_tool import make_uname_for_file


def _save(data, save_dir):
    name = make_uname_for_file()
    with open(os.path.join(save_dir, name), 'wb') as f:
        f.write(data)
    return name


async def download_pdf(pdf_url, save_dir, logger):
    url = pdf_url
    async with aiohttp.ClientSession() as session:  # 计划: 流式/分块下载（但一般文件不会太大）
        async with session.get(url) as response:
            try:
                response.raise_for_status()
                name = _save(await response.read(), save_dir)
                logger.debug(f'下载完成 {url}')
                # 还可以加入更多的信息，如文件大小，是否pdf等
                return name

            except ClientResponseError as cre:
                logger.error(f'下载失败 {url} {cre.status} - {cre.message}')
                raise DownloadFailed(f'下载失败 {cre}')


class DownloadFailed(Exception):
    pass


class ByPdfLink:
    def __init__(self, pdf_url, save_dir, logger):
        self.save_dir = save_dir
        self.logger = logger
        self.pdf_url = pdf_url
        # 下载结果
        self._saved_name = None
        self._succeed = None
        self._err = None

    async def download(self, ):
        try:
            self._saved_name = await download_pdf(self.pdf_url, self.save_dir, self.logger)
            self._succeed = True
        except DownloadFailed as e:
            self._succeed = False
            self._err = e

        return self._succeed

    @property
    def succeed(self):
        assert self._succeed is not None, '还没下载呢'
        return self._succeed

    def get_result(self, quest_id):
        assert self._succeed, '没有下载成功'
        return {
            'file_remote': self._saved_name,
            'quest_id': quest_id,
            'get_by': 'PDF链接直接下载',
        }

    @property
    def err(self):
        assert self._succeed is not None, '还没下载呢'
        return self._err
