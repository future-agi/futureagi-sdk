import time
from fi.client import Client

from fi.client import ModelTypes, Environments

fi_client = Client(
    api_key="5ffab106598343a79720824d380632ce",
    secret_key="faf78735c36c459f8f6be81823950f9d"
)

response = fi_client.log(
    "prompt-template",
    ModelTypes.GENERATIVE_LLM,
    Environments.PRODUCTION,
    "1.2",
    int(time.time()),
    {'chat_history':
     [{'role': 'user',
      'variables': {'name': 'Garvit',
      'value_proposition': 'Get location information of your social media following to place better ads and sponsorships'},
      'prompt_template': 'You work for a company which offers the following value to their prospects:{{Value Proposition}} Take a deep breath, clear your mind and from the given posts first select the post most relevant to your value proposition. The entire post could be related to the value proposition or there could be a small portion in the post that might be relevant. \n\nAfter having found the most relevant post, write a **single sentence** opener for an outreach message referencing the post. Summarize the content of the post briefly to make a catchy opener. \n\nIf none of the posts are remotely relevant to the value proposition, say "no relevant post" instead of forcing an opener.\n\nAhdhere to the following guidelines to create an authentic, high quality opener:\n1. Active and dynamic; recipients absolutely despise passive and dull  \n2. Avoid salesy jargon. \n3. Avoid mentioning things that they obviously already know. Avoid being patronizing and condescending. Don\'t just reword their speech and quote it back to them. It is super annoying! \n4. Avoid using salesy words like "perfectly", "innovative", "possibly", "unique", "expert", or any word or phrases that make you sound overconfident.\n5. Remember that the value proposition we have is only a guess that it will benefit the recipient. We might be completely wrong. Thus, avoid being overly confident in the opener. Choose appropriate words to express this uncertainty.\n   5.1 One way to express this uncertainty is to start the opener confirming that your value proposition is indeed valid for them. Start the opener with "if", "is", "what", "did", etc.\n   2.2 The other way is to be transparent and express in the opener itself that you might be wrong\n\n**'},
      {'role': 'assistant',
      'content': "If you're looking to strategically harness your LinkedIn growth for better ad targeting, our insights might spark some ideas."}]}
).result()
print(response)
