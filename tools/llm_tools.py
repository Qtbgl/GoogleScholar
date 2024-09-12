# openai == 0.27.6
import openai

openai.api_base = "https://opus.gptuu.com/v1"
openai.api_key = "sk-4F6yLy8eZ8Bz4DkdEe8b94Ff4e1444Dc87E636A4712aAd7f"


async def ask_gpt_async(query, timeout):
    messages = [
        {"role": "user", "content": query},
    ]
    response = await openai.ChatCompletion.acreate(
        model="gpt-4o-mini",
        messages=messages,
        max_tokens=1024,
        n=1,
        stop=None,
        temperature=0.5,
        timeout=timeout,
    )
    return response.choices[0].message.content


def ask_gpt(query):
    #   openai.api_base = "https://giegie.green/"
    #     print (openai.api_key)

    try:
        completion = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            # model="gpt-4",
            #             model="gpt-4-0613",
            #             stream=True,
            messages=[{'role': 'user', 'content': query}, ]
        )
        #         print(completion)

        #         for event in completion:
        #             print (event)

        msg = None
        choices = completion.get('choices', None)
        if choices:

            msg = choices[0]['message']['content'] + '\n\n'
        else:
            msg = completion['message']['content'] + '\n\n'

    except Exception as err:
        msg = 'False'
        msg = (str)(err)
        print('OpenAI API Error:' + msg)
        #         print ('OpenAI API Error!!!!!!!')
        i = 0
        while msg == 'False' and i < 4:
            msg = ask_gpt(query)
            i = i + 1
    #             if msg != 'False':
    #                 break
    return msg
