with open(__file__.replace('.py', '.txt'), 'r') as _f:
    api_key = _f.read().strip()
    if not api_key:
        api_key = input('请输入spider的api_key:')

search_max_tries = 2  # search_load_url函数中
