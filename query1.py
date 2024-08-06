from typing import Union

from context import app

from fastapi import Path, Query


@app.get("/query1/{name}")
def query1(
    name: str = Path(..., title="terms to be searched"),
    pages: int = Query(default=3, title="number of pages of publications"),
    min_cite: Union[int, None] = Query(default=None, title="filter by citations, None means not required"),
    year_low: int = Query(default=None, title="minimum year of publication", ge=1900, le=2024),
    year_high: int = Query(default=None, title="maximum year of publication", ge=1900, le=2024),
    patents: bool = Query(default=True, title="Whether or not to include patents"),
    citations: bool = Query(default=True, title="Whether or not to include citations"),
    sort_by: str = Query(default="relevance", title="Sort by 'relevance' or 'date'", pattern="^(relevance|date)$")
):
    # 创建查询
    from crawl.by_scholarly import QueryItem
    param = dict(
        year_low=year_low,
        year_high=year_high,
        patents=patents,
        citations=citations,
        sort_by=sort_by,
    )
    item = QueryItem(name, pages, min_cite, param)

    # # 使用nodriver爬取网页时，创建新的事件循环
    import nodriver as uc
    result = uc.loop().run_until_complete(new_call(item))
    return result


async def new_call(*args, **kwargs):
    from log_config import logger
    logger.info('query1 new call')
    try:
        from crawl.by_nodiver import Crawl
        crawl = await Crawl.create(logger)
    except Exception as e:
        return {'error': f'nodriver启动浏览器出错 {e}'}

    try:
        from record.Record import Record
        record = Record(logger)
    except Exception as e:
        return {'error': f'record创建出错 {e}'}

    # 创建资源
    async with crawl:
        async with record:
            from run.Runner1 import Runner1
            runner = Runner1(crawl, record, logger)
            result = await runner.run(*args, **kwargs)
            return result
