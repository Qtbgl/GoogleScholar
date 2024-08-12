import traceback

from parse.AskGpt import AskGpt


class GptDoHtml(AskGpt):
    def __init__(self, logger):
        self.logger = logger

    async def get_abstract(self, html_str):
        query_txt = '\n'.join([
            html_str,
            '请从上面的网页片段中找出完整的摘要，直接以英文输出摘要',
        ])
        ans = await self.ask_gpt(query_txt)
        return ans
