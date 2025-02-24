from urllib.parse import ParseResult

import aiohttp
from data import api_config


async def get_abstract_by_pii(url_parse: ParseResult):
    # 先获取论文标识符PII
    pii = None
    pths = url_parse.path.strip('/')
    for i, s in enumerate(pths):
        if s == 'pii':
            pii = pths[i]
    if pii is None:
        raise Exception(f'url中缺少pii {url_parse.geturl()}')

    base_url = "https://api.elsevier.com/content/article/pii/"
    url = f"{base_url}{pii}?view=META_ABS"  # META_ABS: 返回元数据和摘要
    headers = {
        "X-ELS-APIKey": api_config.elsevier_api_key,
        "Accept": "application/json",
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            response.raise_for_status()
            data = await response.json()
            abstract = data.get("full-text-retrieval-response", {}).get("coredata", {}).get("dc:description")
            if not abstract:
                raise Exception('摘要不可用')

            return abstract

