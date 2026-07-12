from bot.handlers import edit_profile, queue, start
from bot.main import build_dispatcher
from bot.middlewares.throttling import ThrottlingMiddleware


def test_build_dispatcher_includes_expected_routers():
    dp = build_dispatcher()

    assert start.router in dp.sub_routers
    assert queue.router in dp.sub_routers
    assert edit_profile.router in dp.sub_routers
    assert any(
        isinstance(middleware, ThrottlingMiddleware)
        for middleware in dp.callback_query.middleware
    )
