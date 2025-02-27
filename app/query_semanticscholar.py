from fastapi import HTTPException
from semanticscholar import SemanticScholar

from app.api_tool import app
from data import api_config

@app.get("/semanticscholar/search_paper/{title}")
def get_abstract(title: str, app_key: str):
    if not app_key:
        raise HTTPException(status_code=400, detail="app_key is required")
    if app_key != api_config.app_key:
        raise HTTPException(status_code=400, detail="app_key is invalid")

    result = {'error': None}
    try:
        sch = SemanticScholar()
        paper = sch.search_paper(query=title, match_title=True)
        result['abstract'] = paper.abstract
    except Exception as e:
        result['error'] = str(e)

    return result
