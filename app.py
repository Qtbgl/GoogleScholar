import asyncio
import os
import pickle
from datetime import datetime

from search_pub import query
from bootstrap import deco_scholarly
from set_logging import setup_console_logging, setup_file_loging
from tools.bib_tool import split_arxiv, make_entry

# 先装饰一下原本的scholarly库
deco_scholarly()

# 再设置一下日志
setup_console_logging('CrawlGoogleScholar', level='info')


class Query:
    def __init__(self, save_dir=''):
        self.data = []
        self.save_dir = save_dir

    async def main(self, **kwargs):
        # 创建日志文件名，在每一次任务上
        log_file = os.path.join('data/log', f"{datetime.now().strftime('%Y-%m-%d-%H%M%S')}.log")
        setup_file_loging('CrawlGoogleScholar', log_file)

        # 进入实际的query
        try:
            async for pub in query(**kwargs):
                self.data.append(pub)
        except Exception as e:
            print(f'query函数出错了 {e}')

        print(f'已获得 {len(self.data)} 篇论文')
        if len(self.data):
            self.save_data(log_file, kwargs)
            self.save_bibs()

    def make_path(self, filename):
        return os.path.join(self.save_dir, filename)

    def save_data(self, log_file, kwargs):
        record = {
            'log_file': log_file,
            'kwargs': kwargs,
            'data': [vars(pub) for pub in self.data]
        }
        with open(self.make_path('data.pkl'), 'wb') as f:
            pickle.dump(record, f)

        print(f'已保存 {len(self.data)} 篇文章的结果')

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
            entries.append(make_entry(bib_raw, abstract))

        arxiv_bib, other_bib = split_arxiv(entries)
        # 将arXiv条目写入.bib文件
        with open(self.make_path('data.arXiv.bib'), 'w') as f:
            f.write(arxiv_bib)

        # 将其他条目写入.bib文件
        with open(self.make_path('data.bib'), 'w') as f:
            f.write(other_bib)

        print(f'正在保存 {len(entries)} 篇文章的bib')
