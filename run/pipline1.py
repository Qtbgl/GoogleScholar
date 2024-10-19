import logging


class QueryItem:
    name: str
    pages: int
    year_low: int
    year_high: int
    min_cite: int
    ignore_bibtex: bool

    # def __init__(self, name, pages, year_low=None, year_high=None, min_cite=None, ignore_bibtex=False):
    #     self.name = name
    #     self.pages = pages
    #     self.year_low = year_low
    #     self.year_high = year_high
    #     self.min_cite = min_cite
    #     self.ignore_bibtex = ignore_bibtex

    def __str__(self):
        return str(self.__dict__)


class RunnerConfig:
    logger: logging.Logger
    item: QueryItem


class ReadResult:
    def get_progress(self):
        pass

    def deliver_pubs(self):
        pass


class WriteResult:
    def register_new(self, pub):
        pass

    def mark_error(self, pub, error):
        pass


class GoodbyeBecauseOfError(Exception):
    pass
