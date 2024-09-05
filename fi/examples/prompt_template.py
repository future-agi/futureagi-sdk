import time
from fi.client import Client

from fi.client import ModelTypes, Environments

fi_client = Client(
    uri="https://api.futureagi.com",
    api_key="FI_API_KEY",
    secret_key="FI_SECRET_KEY"
)

response = fi_client.log(
    "prompt-template",
    ModelTypes.GENERATIVE_LLM,
    Environments.PRODUCTION,
    "1.2",
    int(time.time()),
    {'chat_history':
     [{'role': 'user',
      "content": "TEXT",
      'variables': {'name': 'Garvit',
      'value_proposition': 'Get location information of your social media .'},
      'prompt_template': 'Xyz template'},
      {'role': 'assistant',
      'content': "abc reply"}]}
).result()
print(response)
