def display_pub_url(pubs):
    rows = ["#{} {}".format(pub['task_id'], pub['url']) for pub in pubs]
    rows_output = '\n\t'.join(rows)  # 生成输出字符串
    return f'{len(pubs)} pubs: \n\t{rows_output}'
