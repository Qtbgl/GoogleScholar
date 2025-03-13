class PubItem(object):
    def __init__(self, raw_pub, task_id):
        self.raw_pub = raw_pub
        self.task_id = task_id
        self.thrown_reason = None
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
        return self.raw_pub.get('bib', {}).get('abstract')

    def thrown(self, reason):  # fill_pub取消级别的才记录此项，不是忽略级别
        """
        标记成不想要这篇文章了
        """
        self.thrown_reason = reason

    @property
    def is_thrown(self):
        return self.thrown_reason is not None

    def fill_abstract(self, abstract):
        # assert self.thrown_reason is None
        self.abstract = abstract

    def fill_bibtex(self, bibtex):
        # assert self.thrown_reason is None
        self.bibtex = bibtex

