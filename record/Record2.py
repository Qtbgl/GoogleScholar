from record.Conn import Conn


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
        bib_default = {'link': None, 'string': None}
        # 所有已有的结果
        return [{
            'abstract': pub.get('abstract'),
            'pub_url': pub['url'],
            'title': pub['title'],
            'author': pub['author'],
            'num_citations': pub.get('num_citations', None),
            'eprint_url': pub.get('eprint_url'),
            'BibTeX': pub.get('BibTeX', bib_default),
            'error': pub.get('error'),
        } for pub in all_pubs]
