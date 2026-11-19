"""LangGraph (``CompiledStateGraph`` / ``Pregel``) and LangChain (``Runnable``) through ``ainvoke``,
with ``config={"configurable": params}``.

LangGraph also gets ``thread_id = "<run_id>:<example_id>:<trial>"`` (unless the params set one): a
graph compiled with a checkpointer refuses to run without it, and a fresh thread per trial keeps
trials from sharing checkpointed state."""

from __future__ import annotations

from typing import Any

from fi.experiments.adapters._base import TaskRunner


def _content(message: Any) -> Any:
    if isinstance(message, dict):
        return message.get("content", message)
    if isinstance(message, (tuple, list)) and len(message) == 2 and isinstance(message[0], str):
        return message[1]
    return getattr(message, "content", message)


def _has_messages_channel(graph: Any) -> bool:
    channels = getattr(graph, "channels", None)
    if isinstance(channels, dict) and "messages" in channels:
        return True
    try:
        schema = graph.get_input_jsonschema()
    except Exception:
        return False
    return "messages" in (schema.get("properties") or {})


def _config(ctx: Any, *, thread: bool = False) -> dict[str, Any]:
    params = dict(getattr(ctx, "params", {}) or {})
    if thread and ctx is not None and "thread_id" not in params:
        params["thread_id"] = f"{ctx.run_id}:{ctx.example_id}:{ctx.trial}"
    return {"configurable": params} if params else {}


class LangGraphRunner(TaskRunner):
    framework = "langgraph"
    is_async = True

    def __init__(self, graph: Any) -> None:
        self.graph = graph
        self.messages_state: bool = bool(_has_messages_channel(graph))
        self.needs_single_input: bool = self.messages_state

    def describe(self) -> str:
        name = getattr(self.graph, "name", None) or "graph"
        if self.messages_state:
            return f'LangGraph → {name}.ainvoke({{"messages": [("user", row.input)]}}) → last message .content'
        return f"LangGraph → {name}.ainvoke(row.inputs) → final state"

    async def acall(self, row: Any, ctx: Any) -> Any:
        payload = {"messages": [("user", row.input)]} if self.messages_state else dict(row.inputs)
        state = await self.graph.ainvoke(payload, config=_config(ctx, thread=True))
        if isinstance(state, dict) and isinstance(state.get("messages"), list) and state["messages"]:
            return _content(state["messages"][-1])
        return state


class LangChainRunner(TaskRunner):
    framework = "langchain"
    is_async = True

    def __init__(self, runnable: Any) -> None:
        self.runnable = runnable
        self.dict_keys: list[str] = self._dict_input_keys(runnable)
        self.needs_single_input: bool = not self.dict_keys

    @staticmethod
    def _dict_input_keys(runnable: Any) -> list[str]:
        try:
            schema = runnable.get_input_jsonschema()
        except Exception:
            return []
        if schema.get("type") != "object":
            return []
        return list((schema.get("properties") or {}).keys())

    def describe(self) -> str:
        name = type(self.runnable).__name__
        arg = f"{{{', '.join(self.dict_keys)}}} from the row" if self.dict_keys else "row.input"
        return f"LangChain → {name}.ainvoke({arg}) → .content"

    async def acall(self, row: Any, ctx: Any) -> Any:
        if self.dict_keys:
            payload: Any = {k: row[k] for k in self.dict_keys if k in row}
        else:
            payload = row.input
        out = await self.runnable.ainvoke(payload, config=_config(ctx))
        return _content(out) if hasattr(out, "content") or isinstance(out, dict) and "content" in out else out
