from record.Conn import Conn
from tools.bib_tools import add_abstract


class Record2(Conn):
    def __init__(self, logger):
        super().__init__(logger)
        self.pages = None
        self.fail_pubs = []
        self.filled_pubs = []

    def set_pages(self, pages):
        self.pages = pages

    def fail_to_fill(self, pub):
        self.fail_pubs.append(pub)

    def success_fill(self, pub):
        self.filled_pubs.append(pub)

    def get_progress(self):
        if not self.pages:
            return 0.0

        total = 10 * self.pages
        done = len(self.filled_pubs) + len(self.fail_pubs)
        return done / total

    def deliver_pubs(self):
        all_pubs = self.filled_pubs + self.fail_pubs
        # 缺省值
        empty_bib = {'link': None, 'string': None}
        results = []
        for pub in all_pubs:
            abstract = pub.get('abstract')
            bib_link = pub.get('BibTeX', empty_bib).get('link')
            bib_raw = pub.get('BibTex', empty_bib).get('string')
            # bib加入摘要
            if abstract and bib_raw:
                bib_str = add_abstract(bib_raw, abstract)
            else:
                bib_str = None

            item = {
                'abstract': abstract,
                'pub_url': pub['url'],
                'title': pub['title'],
                'author': pub['author'],
                'num_citations': pub.get('num_citations', None),
                'eprint_url': pub.get('eprint_url'),
                'bib_link': bib_link,
                'bib_raw': bib_raw,
                'bib': bib_str,
                'error': pub.get('error'),
            }
            results.append(item)

        # 所有已有的结果
        return results
