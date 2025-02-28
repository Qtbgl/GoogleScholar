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

        if gpt_is_sorry(ans) or not check_content_success(ans):
            raise self.GPTAnswerError('GPT回答有误 ' + ans)

        return ans


def gpt_is_sorry(ans):
    if '抱歉' in ans or "I'm sorry" in ans or "I'm unable" in ans:
        return True
    else:
        return False


def check_content_success(response):
    # 定义一些关键词，表示没有成功获取所需内容
    keywords = [
        "does not contain",
        "placeholder",
        "error message",
        "JavaScript and cookies need to be enabled",
        "cannot extract",
        "no information related"
    ]

    # 检查是否包含这些关键词
    hit = 0
    threshold = 3
    for keyword in keywords:
        if keyword in response:
            hit += 1
            if hit >= threshold:
                return False

    return True
