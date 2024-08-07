from fastapi import Path, Query

from context import app
from secure import check_key


@app.get("/query2/{name}")
def query2(
    name: str = Path(..., title="terms to be searched"),
    pages: int = Query(default=3, title="number of pages of publications"),
    year_low: int = Query(default=None, title="minimum year of publication", ge=1900, le=2024),
    year_high: int = Query(default=None, title="maximum year of publication", ge=1900, le=2024),
    serpdog_key: str = Query(default=None, title='serpdog\'s api_key, default is provided'),
    api_key: str = Query(title='user key')
):
    if not check_key(api_key):
        return {"error": "Invalid API key!"}

    # 创建查询
    from crawl.by_serpdog import QueryItem
    item = QueryItem(name, pages, as_ylo=year_low, as_yhi=year_high, api_key=serpdog_key)

    # # 使用nodriver爬取网页时，创建新的事件循环
    import nodriver as uc
    result = uc.loop().run_until_complete(new_call(item))
    return result


async def new_call(*args, **kwargs):
    # return {'error': 'query2正在更新代码，请使用query1'}
    # 导入自定义库
    from log_config import logger
    logger.info('query2 new call')
    try:
        from crawl.by_nodiver import Crawl
        crawl = await Crawl.create(logger)
    except Exception as e:
        return {'error': f'nodriver启动浏览器出错 {e}'}

    try:
        from record.Record2 import Record2
        record = Record2(logger)
    except Exception as e:
        return {'error': f'record创建出错 {e}'}

    # 创建资源
    async with crawl:
        async with record:
            from run.Runner2 import Runner2
            runner = Runner2(crawl, record, logger)
            result = await runner.run(*args, **kwargs)
            return result
