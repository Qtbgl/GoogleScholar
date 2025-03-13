from semanticscholar import AsyncSemanticScholar


async def get_abstract_by_semanticscholar(title):  # TODO: 会重复日志
    sch = AsyncSemanticScholar()
    paper = await sch.search_paper(query=title, match_title=True)
    assert paper.abstract, '返回的摘要为空'
    abstract = paper.abstract

    return abstract
