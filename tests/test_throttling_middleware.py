from unittest.mock import AsyncMock

from bot.middlewares.throttling import ThrottlingMiddleware


def _make_callback(user_id: int):
    callback = AsyncMock()
    callback.from_user.id = user_id
    return callback


async def test_allows_first_call():
    middleware = ThrottlingMiddleware(rate_limit=2.0, time_func=lambda: 100.0)
    callback = _make_callback(1)
    handled = []

    async def handler(event, data):
        handled.append(event)
        return "ok"

    result = await middleware(handler, callback, {})

    assert result == "ok"
    assert handled == [callback]
    callback.answer.assert_not_awaited()


async def test_blocks_rapid_repeat_from_same_user():
    clock = {"now": 100.0}
    middleware = ThrottlingMiddleware(rate_limit=2.0, time_func=lambda: clock["now"])
    handled = []

    async def handler(event, data):
        handled.append(event)
        return "ok"

    await middleware(handler, _make_callback(1), {})
    clock["now"] = 101.0  # 1s later, still inside the 2s window
    second_callback = _make_callback(1)
    result = await middleware(handler, second_callback, {})

    assert result is None
    assert len(handled) == 1
    second_callback.answer.assert_awaited_once_with(
        "Слишком быстро, подожди немного", show_alert=True
    )


async def test_allows_different_users_independently():
    clock = {"now": 100.0}
    middleware = ThrottlingMiddleware(rate_limit=2.0, time_func=lambda: clock["now"])
    handled = []

    async def handler(event, data):
        handled.append(event)
        return "ok"

    await middleware(handler, _make_callback(1), {})
    result = await middleware(handler, _make_callback(2), {})

    assert result == "ok"
    assert len(handled) == 2


async def test_allows_same_user_after_window_elapses():
    clock = {"now": 100.0}
    middleware = ThrottlingMiddleware(rate_limit=2.0, time_func=lambda: clock["now"])
    handled = []

    async def handler(event, data):
        handled.append(event)
        return "ok"

    await middleware(handler, _make_callback(1), {})
    clock["now"] = 103.0  # past the 2s window
    result = await middleware(handler, _make_callback(1), {})

    assert result == "ok"
    assert len(handled) == 2
