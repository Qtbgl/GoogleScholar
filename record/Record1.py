from crawl.by_scholarly import QueryItem, get_bib_link
from record.Conn import Conn
from tools.bib_tools import add_abstract, del_abstract


class Record1(Conn):
    def __init__(self, logger):
        super().__init__(logger)
        self.pages = None
        self.fail_pubs = []
        self.filled_pubs = []

    def set_pages(self, pages):
        self.pages = pages

    def fail_to_fill(self, pub, error):
        if pub.get('error'):
            pub['error'] = (error, pub['error'])  # 嵌套链接
        else:
            pub['error'] = error

        self.fail_pubs.append(pub)

    def success_fill(self, pub):
        self.filled_pubs.append(pub)

    def get_progress(self):
        if not self.pages:
            return 0.0

        total = 10 * self.pages
        done = len(self.filled_pubs) + len(self.fail_pubs)
        return done / total

    def deliver_pubs(self, item: QueryItem):
        all_pubs = self.filled_pubs + self.fail_pubs
        # 缺省值
        empty_bib = {'link': None, 'string': None}
        results = []
        # 所有已有的结果
        for pub in all_pubs:
            abstract = pub.get('abstract')
            obj = {
                'title': pub['title'],
                'author': pub['author'],
                'pub_year': pub['pub_year'],
                'pub_url': pub['url'],
                'abstract': abstract,
                'eprint_url': pub.get('eprint_url'),
                'num_citations': pub.get('num_citations', None),
            }
            # 加入bib
            if item.ignore_bibtex:
                obj['bib_link'] = get_bib_link(pub['raw_pub'])  # 为以后添加
            else:
                bib_link = pub.get('BibTeX', empty_bib).get('link')
                bib_raw = pub.get('BibTeX', empty_bib).get('string')
                # bib加入摘要
                if bib_raw and abstract:
                    bib_str = add_abstract(bib_raw, abstract)
                elif bib_raw and not abstract:
                    bib_str = del_abstract(bib_raw)
                else:
                    bib_str = None

                obj['bib_link'] = bib_link
                obj['bib_raw'] = bib_raw
                obj['bib'] = bib_str

            obj['error'] = pub.get('error')
            results.append(obj)

        # 所有已有的结果
        return results
