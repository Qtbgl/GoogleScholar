import aiohttp
from aiohttp import ClientResponseError

from download.context import DownloadConfig


class ByRequest:
    def __init__(self, config: DownloadConfig):
        self.config = config

    async def download_pdf(self, pub):
        logger = self.config.logger
        url = pub['url']
        filename = ...

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                try:
                    response.raise_for_status()
                    with open(filename, 'wb') as f:
                        f.write(await response.read())
                        logger.debug(f'下载完成 {url}')

                    pub['remote'] = filename  # 服务器端索引id（如url的唯一变换码）
                    # 还可以加入更多的信息，如文件大小，是否pdf等

                except ClientResponseError as cre:
                    logger.error(f'下载失败 {url} {cre.status} - {cre.message}')
                    pub['error'] = f'下载失败 {cre}'
