import bibtexparser


def add_abstract(bib_str, abstract):
    try:
        bib_db = bibtexparser.loads(bib_str)
        bib_db.entries[0]['abstract'] = abstract
        new_str = bibtexparser.dumps(bib_db)
        return new_str
    except Exception as e:
        return None
