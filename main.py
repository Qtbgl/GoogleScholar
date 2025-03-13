import asyncio

from app import Query


async def main():
    key_word = input('Enter a search term: ')
    pages = 1
    # 更多条件
    search_params = {'year_low': 2024}
    # 结果过滤
    filter_params = {'min_cite': None, }

    await Query(save_dir='data/Output').main(
        key_word=key_word, pages=pages, search_params=search_params, filter_params=filter_params)


if __name__ == '__main__':
    asyncio.run(main())
