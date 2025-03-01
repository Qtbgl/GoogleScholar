class PubItem(object):
    def __init__(self, raw_pub, task_id):
        self.raw_pub = raw_pub
        self.task_id = task_id
        self.cancel_reason = None
        self.abstract = None
        self.bibtex = None

    @property
    def pub_url(self):
        return self.raw_pub.get("pub_url")

    @property
    def num_citations(self):
        return self.raw_pub.get('num_citations', 0)
    
    @property
    def cut(self):
        return self.raw_pub.get('bib', {}).get('abstract'),

    def cancel_its_fill(self, reason):  # 取消级别的才记录此项，不是忽略级别
        self.cancel_reason = reason

    def fill_abstract(self, abstract):
        assert self.cancel_reason is None
        self.abstract = abstract

    def fill_bibtex(self, bibtex):
        assert self.cancel_reason is None
        self.bibtex = bibtex

