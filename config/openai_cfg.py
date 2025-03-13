with open(__file__.replace('.py', '.txt'), 'r') as _f:
    openai_api_base, openai_api_key = (string.strip() for string in _f.read().split())
    if not openai_api_key or not openai_api_base:
        openai_api_base = input("请输入openai_api_base:")
        openai_api_key = input("请输入openai_api_key:")
