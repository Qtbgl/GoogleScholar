import bibtexparser


def add_abstract(bib_str, abstract):
    try:
        bib_db = bibtexparser.loads(bib_str)
        bib_db.entries[0]['abstract'] = abstract
        new_str = bibtexparser.dumps(bib_db)
        return new_str
    except Exception as e:
        raise Exception(f'bib解析出错 {e} 原字符串为 {bib_str}')


def del_abstract(bib_str):
    try:
        bib_db = bibtexparser.loads(bib_str)
        entry = bib_db.entries[0]
        if 'abstract' in entry.keys():
            del entry['abstract']

        new_str = bibtexparser.dumps(bib_db)
        return new_str
    except Exception as e:
        raise Exception(f'bib解析出错 {e} 原字符串为 {bib_str}')


def make_entry(bib_raw, abstract):
    entry = bibtexparser.loads(bib_raw).entries[0]
    entry['abstract'] = abstract
    return entry


def split_arxiv(entries):
    # 初始化两个列表来存储条目，遍历每个BibTeX条目
    arxiv_entries = []
    other_entries = []
    for entry in entries:
        if 'arxiv' in entry.get('venue', '').lower():
            arxiv_entries.append(entry)
        else:
            other_entries.append(entry)

    # 创建BibDatabase对象
    arxiv_db = bibtexparser.bibdatabase.BibDatabase()
    other_db = bibtexparser.bibdatabase.BibDatabase()

    # 将条目添加到相应的数据库
    arxiv_db.entries = arxiv_entries
    other_db.entries = other_entries

    arxiv_bib = bibtexparser.dumps(arxiv_db)
    other_bib = bibtexparser.dumps(other_db)

    return arxiv_bib, other_bib
