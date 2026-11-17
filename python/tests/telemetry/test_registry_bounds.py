import tracemalloc

from fi.telemetry._registry import Registry, State


def test_lru_and_absolute_ttl():
    now = [0]
    registry = Registry(capacity=2, ttl=10, clock=lambda: now[0])
    first = registry.get(1, create=True)
    registry.get(2, create=True)
    assert registry.get(1) is first
    registry.get(3, create=True)
    assert registry.get(2) is None
    now[0] = 10
    assert registry.get(1) is None
    assert registry.get(3) is None


def test_default_capacity_and_memory_are_bounded():
    registry = Registry()
    tracemalloc.start()
    try:
        for index in range(4096):
            registry.get(index, create=True)
        before = tracemalloc.get_traced_memory()[0]
        for index in range(4096, 16384):
            registry.get(index, create=True)
        after = tracemalloc.get_traced_memory()[0]
        assert len(registry._entries) == 4096
        assert after - before < 2 * 1024 * 1024
    finally:
        tracemalloc.stop()


def test_skill_list_cap_and_first_load_order():
    state = State()
    for index in range(40):
        attrs = {"fi.skill.version_id": str(index), "fi.skill.id": str(index),
                 "fi.skill.name": "refund", "fi.skill.version": index}
        state.add_skill(attrs)
        state.add_skill(attrs)
    assert state.attrs["fi.skills.version_ids"] == tuple(str(index) for index in range(32))
    assert state.attrs["fi.skills.count"] == 32
    assert state.attrs["fi.skills.truncated"] is True
