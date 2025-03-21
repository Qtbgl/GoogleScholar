import os
import pickle
from datetime import datetime

from crawl.search_pub import query
from bootstrap import deco_scholarly
from tools.set_logging import setup_console_logging, setup_file_loging, remove_log_handler
from tools.bib_tool import split_arxiv, make_entry

# 先装饰一下原本的scholarly库
deco_scholarly()


class Query:
    def __init__(self, save_dir='', console_log_level='debug'):
        self.data = []
        self.save_dir = save_dir
        self.start_time = datetime.now()
        # 创建日志文件名，在每一次Query实例上==一次查询任务
        remove_log_handler('CrawlGoogleScholar')
        setup_console_logging('CrawlGoogleScholar', level=console_log_level)
        log_file = os.path.join('data/log', f"{self.start_time.strftime('%Y-%m-%d-%H%M%S')}.log")
        setup_file_loging('CrawlGoogleScholar', log_file)
        self.log_file = log_file

    @property
    def datetime_short(self):
        return self.start_time.strftime("%h_%d_%H%M%S")

    async def main(self, **kwargs):
        # 进入实际的query
        try:
            async for pub in query(**kwargs):
                self.data.append(pub)
        except Exception as e:
            print(f'query函数出错了 {e}')

        print(f'已获得 {len(self.data)} 篇论文')
        if len(self.data):
            self.save_data(kwargs)
            self.save_bibs()

    def make_path(self, filename):
        os.makedirs(self.save_dir, exist_ok=True)
        return os.path.join(self.save_dir, filename)

    def save_data(self, kwargs):
        record = {
            'log_file': self.log_file,
            'kwargs': kwargs,
            'data': [vars(pub) for pub in self.data]
        }
        with open(self.make_path(f'{self.datetime_short}.data.pkl'), 'wb') as f:
            pickle.dump(record, f)

        print(f'已序列化 {len(self.data)} 篇的爬取结果')

    def save_bibs(self):
        clean_pubs = []
        for pub in self.data:
            if pub.is_thrown:
                print(f'bib将不保存：{pub.thrown_reason}，{pub.basic_info}')
            elif not pub.abstract:
                print(f'bib将不保存：缺少摘要，{pub.basic_info}')
            elif not pub.bibtex:
                print(f'bib将不保存：缺少bibtex引用，{pub.basic_info}')
            else:
                clean_pubs.append(pub)

        # 假设相应的数据都有，过滤的已去除
        entries = []
        for pub in clean_pubs:
            bib_raw = pub.bibtex
            abstract = pub.abstract
            # bib加入摘要
            entry = make_entry(bib_raw, abstract)
            # 更改pub_year键名
            if 'pub_year' in entry.keys():
                entry['year'] = entry['pub_year']
                del entry['pub_year']

            entries.append(entry)

        arxiv_bib, other_bib = split_arxiv(entries)
        # 将arXiv条目写入.bib文件
        with open(self.make_path(f'{self.datetime_short}.arXiv.bib'), 'w', encoding='utf-8') as f:
            f.write(arxiv_bib)

        # 将其他条目写入.bib文件
        with open(self.make_path(f'{self.datetime_short}.bib'), 'w', encoding='utf-8') as f:
            f.write(other_bib)

        print(f'已保存 {len(entries)} 篇文章的bib')

    def clean_data(self):
        print(f'将清空 {len(self.data)} 篇论文的数据')
        self.data = []
