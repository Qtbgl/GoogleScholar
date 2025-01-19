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
