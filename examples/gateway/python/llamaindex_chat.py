"""Use LlamaIndex's OpenAILike class with the gateway's OpenAI-compatible API."""

import asyncio
import os

from fi.gateway import openai_kwargs
from llama_index.core.llms import ChatMessage
from llama_index.llms.openai_like import OpenAILike


def make_chat() -> OpenAILike:
    """Map the helper's base_url to LlamaIndex's api_base without adding /v1."""
    options = openai_kwargs(session_id="example-llamaindex")
    return OpenAILike(
        model=os.environ["FI_GATEWAY_MODEL"],
        api_key=options["api_key"],
        api_base=options["base_url"],
        default_headers=options["default_headers"],
        is_chat_model=True,
        is_function_calling_model=False,
        context_window=8192,
        max_tokens=128,
        max_retries=0,
        timeout=15,
    )


async def ask(prompt: str) -> str:
    """Send a chat message asynchronously, without embeddings or model downloads."""
    answer = await make_chat().achat([ChatMessage(role="user", content=prompt)])
    return str(answer.message.content)


def ask_sync(prompt: str) -> str:
    """Synchronous twin using the same gateway options."""
    answer = make_chat().chat([ChatMessage(role="user", content=prompt)])
    return str(answer.message.content)


if __name__ == "__main__":
    print(asyncio.run(ask("Say hello in one sentence.")))
