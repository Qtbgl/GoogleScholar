import os.path

import aiohttp
from aiohttp import ClientResponseError

from download.context import Config
from download.download_tool import make_uname_for_file


class ByRequest:
    def __init__(self, config: Config):
        self.config = config
        self.save_dir = os.path.join(config.root_path, 'data', 'download')
        os.makedirs(self.save_dir, exist_ok=True)

    def _save(self, data):
        name = make_uname_for_file()
        with open(os.path.join(self.save_dir, name), 'wb') as f:
            f.write(data)
        return name

    async def download_pdf(self, pub):
        logger = self.config.logger
        url = pub['url']

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                try:
                    response.raise_for_status()
                    pub['file'] = self._save(await response.read())
                    logger.debug(f'下载完成 {url}')

                    # 还可以加入更多的信息，如文件大小，是否pdf等

                except ClientResponseError as cre:
                    logger.error(f'下载失败 {url} {cre.status} - {cre.message}')
                    pub['error'] = f'下载失败 {cre}'
