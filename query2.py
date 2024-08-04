from fastapi import Path, Query

from context import app


@app.get("/query2/{name}")
def query2(
    name: str = Path(..., title="terms to be searched"),
    pages: int = Query(default=3, title="number of pages of publications"),
    year_low: int = Query(default=None, title="minimum year of publication", ge=1900, le=2024),
    year_high: int = Query(default=None, title="maximum year of publication", ge=1900, le=2024),
    language: str = Query(default=None, title="search language, default: en_us"),
    api_key: str = Query(default=None, title='serpdog\'s api_key, default is provided'),
):
    # 创建查询
    from crawl.by_serpdog import QueryItem
    item = QueryItem(name, pages, year_low, year_high, language, api_key)

    # # 使用nodriver爬取网页时，创建新的事件循环
    import nodriver as uc
    result = uc.loop().run_until_complete(new_call(item))
    return result


async def new_call(*args, **kwargs):
    return {'error': 'query2正在更新代码，请使用query1'}
    # # 导入自定义库
    # from run.Runner1 import Runner1
    # from crawl.by_nodiver import Crawl
    # from record.Record import Record
    # # 创建资源
    # async with Crawl() as crawl:
    #     async with Record() as record:
    #         runner = Runner1(crawl, record)
    #         result = await runner.run(*args, **kwargs)
    #         return result
