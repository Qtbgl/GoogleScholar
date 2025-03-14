from semanticscholar import AsyncSemanticScholar


# 解决重复日志问题
import bootstrap.deco_semanticscholar


async def get_abstract_by_semanticscholar(title):
    sch = AsyncSemanticScholar()
    paper = await sch.search_paper(query=title, match_title=True)
    assert paper.abstract, '返回的摘要为空'
    abstract = paper.abstract

    return abstract
