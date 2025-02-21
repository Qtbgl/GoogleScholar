def main():
    from scholarly import scholarly
    import deco_get_bibtex
    import deco_get_soup
    import logging
    # 创建一个日志记录器
    logger = logging.getLogger('scholarly')
    logger.setLevel(logging.DEBUG)
    # 创建一个控制台处理程序
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    # 创建一个格式化器
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    # 将处理程序添加到记录器
    logger.addHandler(console_handler)
    print('开始查询文献')
    search_keyword = 'NSCLC, segmentation'
    q = scholarly.search_pubs(search_keyword)
    # pubs = []
    # for i in range(20):
    #     pub = next(q)
    #     print(f'#{i}', pub['bib']['title'], pub['pub_url'])
    #     pubs.append(pub)
    pub = next(q)
    print(pub)
    bib = scholarly.bibtex(pub)
    print(bib)


if __name__ == '__main__':
    main()
