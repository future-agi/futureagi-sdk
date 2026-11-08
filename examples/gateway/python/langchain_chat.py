"""Use stock LangChain with a person-owned gateway key, not a platform key pair."""

import asyncio
import os

from fi.gateway import openai_kwargs
from langchain_openai import ChatOpenAI


def make_chat() -> ChatOpenAI:
    """Read FI_GATEWAY_API_KEY and FI_GATEWAY_BASE_URL on the server."""
    return ChatOpenAI(
        model=os.environ["FI_GATEWAY_MODEL"],
        **openai_kwargs(session_id="example-langchain"),
        max_retries=0,
        timeout=15,
    )


async def ask(prompt: str) -> str:
    """Generate one answer asynchronously using the stock LangChain client."""
    answer = await make_chat().ainvoke(prompt)
    return str(answer.content)


def ask_sync(prompt: str) -> str:
    """Synchronous twin for scripts that do not run an event loop."""
    return str(make_chat().invoke(prompt).content)


if __name__ == "__main__":
    print(asyncio.run(ask("Say hello in one sentence.")))
