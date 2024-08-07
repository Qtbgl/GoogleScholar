def is_key(api_key):
    return api_key == 'ccc'


def check_key(obj: dict):
    assert 'api_key' in obj, 'API key missing'
    api_key = obj['api_key']
    assert is_key(api_key), 'Invalid API key!'
    return api_key


def get_general_params(obj: dict):
    res = {}
    # 必需参数
    # 默认参数
    if 'pages' in obj:
        res['pages'] = int(obj['pages'])
    else:
        res['pages'] = 1

    # 可选参数
    if 'year_low' in obj:
        res['year_low'] = int(obj['year_low'])
    if 'year_high' in obj:
        res['year_high'] = int(obj['year_high'])

    return res
