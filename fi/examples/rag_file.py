import time
from fi.client import Client

from fi.client import ModelTypes, Environments

fi_client = Client(
    uri="https://api.futureagi.com",
  api_key="FI_API_KEY",
  secret_key="FI_SECRET_KEY"
)

response = fi_client.log(
    "sZZTSGXIFi",
    ModelTypes.GENERATIVE_LLM,
    Environments.PRODUCTION,
    "1.2",
    int(time.time()),
    {
        "chat_history": [
            {"role": "user", "content": "What is the capital of France?", "context": [
                ["France is a country in Europe.", " The capital of France is Paris."],
                ["Germany is a country in Europe.", " The capital of Germany is Berlin."],
                ["Italy is a country in Europe.", " The capital of Italy is Rome."]
            ]},
            {"role": "assistant",
             "content": "Paris"}
        ]
    }
).result()
print(response)
