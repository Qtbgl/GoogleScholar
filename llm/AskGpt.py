import asyncio

from llm.llm_tool import ask_gpt_async


class AskGpt:
    def __init__(self, timeout=None):
        self.timeout = timeout

    class GPTQueryError(Exception):
        pass

    class GPTAnswerError(Exception):
        pass

    async def ask_gpt(self, query_txt):
        try:
            # logger.debug(f'ask_gpt_async 的 timeout 为 {self.timeout}')
            ans = await ask_gpt_async(query_txt, self.timeout)
        except asyncio.CancelledError:
            raise
        except Exception as e:
            raise self.GPTQueryError(f'访问GPT出错 {e}')

        if '抱歉' in ans or "I'm sorry" in ans or "I'm unable" in ans:
            raise self.GPTAnswerError('GPT回答有误 ' + ans)

        return ans
