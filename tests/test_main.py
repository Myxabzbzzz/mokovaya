from bot.handlers import queue, start
from bot.main import build_dispatcher


def test_build_dispatcher_includes_expected_routers():
    dp = build_dispatcher()

    assert start.router in dp.sub_routers
    assert queue.router in dp.sub_routers
