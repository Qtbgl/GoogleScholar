import bibtexparser

from log_config import logger


def add_abstract(bib_str, abstract):
    try:
        bib_db = bibtexparser.loads(bib_str)
        bib_db.entries[0]['abstract'] = abstract
        new_str = bibtexparser.dumps(bib_db)
        return new_str
    except Exception as e:
        logger.error(f'bib解析出错 {e} 原字符串为 {bib_str}')
        return None
