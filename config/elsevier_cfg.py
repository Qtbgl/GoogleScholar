with open(__file__.replace('.py', '.txt'), 'r') as _f:
    api_key = _f.read().strip()
    if not api_key:
        api_key = input('Enter your Elsevier API key: ')
