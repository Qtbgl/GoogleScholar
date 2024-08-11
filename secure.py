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
    if 'min_cite' in obj:
        res['min_cite'] = int(obj['min_cite'])

    return res


class Params:
    def __init__(self, obj: dict):
        print('obj', obj)
        self.obj = obj

    @property
    def pages(self):
        return self.obj.get('pages', 1)

    @property
    def year_low(self):
        return get_int(self.obj, 'year_low', a=1900, b=2024)

    @property
    def year_high(self):
        return get_int(self.obj, 'year_high', a=1900, b=2024)

    @property
    def min_cite(self):
        return get_int(self.obj, 'min_cite')


def get_int(obj, key, default=None, a=None, b=None):
    val = obj.get(key)
    if val is None:
        return default

    val = int(val)
    print('???', a, val, b)
    if a is not None:
        assert a <= val, 'Value must be bigger than or equal to {}'.format(a)
    if b is not None:
        assert b >= val, 'Value must be less than or equal to {}'.format(b)
    return val
