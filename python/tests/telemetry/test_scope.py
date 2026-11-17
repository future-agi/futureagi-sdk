import asyncio
from concurrent.futures import ThreadPoolExecutor
from contextvars import copy_context

import pytest
from fi.telemetry import agent_scope


def test_root_nested_context_and_restoration(tracing, make_snapshot):
    tracer, exporter, _ = tracing
    skill, _ = make_snapshot()
    context, _ = make_snapshot("agent_context")
    with agent_scope(agent="parent"):
        with tracer.start_as_current_span("root"):
            skill.read_all()
            with agent_scope(agent="child", context=context):
                with tracer.start_as_current_span("child") as child:
                    assert child.attributes["gen_ai.agent.name"] == "child"
                    assert "fi.skills.version_ids" not in child.attributes
                    assert child.attributes["fi.context.version_id"] == context.identity.version_id
            with tracer.start_as_current_span("sibling") as sibling:
                assert sibling.attributes["gen_ai.agent.name"] == "parent"
                assert sibling.attributes["fi.skills.version_ids"] == (skill.identity.version_id,)
                assert "fi.context.id" not in sibling.attributes
    with tracer.start_as_current_span("outside") as outside:
        assert "gen_ai.agent.name" not in outside.attributes


def test_plain_nested_scope_inherits_lists_and_isolates_parent(tracing, make_snapshot):
    tracer, _, _ = tracing
    skill, _ = make_snapshot()
    with agent_scope(agent="parent"):
        with tracer.start_as_current_span("root"):
            skill.read_all()
            with agent_scope(agent="child"):
                with tracer.start_as_current_span("child") as span:
                    assert span.attributes["fi.skills.count"] == 1
                    assert span.attributes["gen_ai.agent.name"] == "child"


def test_exception_and_thread_handoff(tracing):
    tracer, _, _ = tracing
    with pytest.raises(RuntimeError):
        with agent_scope(agent="agent"):
            def work():
                with tracer.start_as_current_span("thread") as span:
                    return span.attributes["gen_ai.agent.name"]
            with ThreadPoolExecutor(max_workers=1) as pool:
                assert pool.submit(copy_context().run, work).result() == "agent"
            raise RuntimeError("application failure")
    with tracer.start_as_current_span("outside") as span:
        assert "gen_ai.agent.name" not in span.attributes


async def test_coroutine_decorator_and_cancel_restore(tracing):
    tracer, _, _ = tracing
    @agent_scope(agent="async-agent")
    async def run():
        with tracer.start_as_current_span("async") as span:
            assert span.attributes["gen_ai.agent.name"] == "async-agent"
        raise asyncio.CancelledError()
    with pytest.raises(asyncio.CancelledError):
        await run()
    with tracer.start_as_current_span("outside") as span:
        assert "gen_ai.agent.name" not in span.attributes


async def test_async_generator_restores_between_yields(tracing, make_snapshot):
    tracer, _, _ = tracing
    skill, _ = make_snapshot()
    @agent_scope(agent="generator")
    async def generate():
        with tracer.start_as_current_span("one"):
            skill.read_all()
        yield 1
        with tracer.start_as_current_span("two") as span:
            assert span.attributes["fi.skills.count"] == 1
        yield 2
    async for _ in generate():
        with tracer.start_as_current_span("caller") as span:
            assert "gen_ai.agent.name" not in span.attributes


def test_sync_decorator_and_generator_guidance(tracing):
    tracer, _, _ = tracing
    @agent_scope(agent="sync-agent")
    def run():
        with tracer.start_as_current_span("sync") as span:
            return span.attributes["gen_ai.agent.name"]
    assert run() == "sync-agent"
    def generator():
        yield 1
    with pytest.raises(TypeError, match="body"):
        agent_scope()(generator)
