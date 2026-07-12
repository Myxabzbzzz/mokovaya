from sqlalchemy.ext.asyncio import AsyncSession

from bot.middlewares.db import DbSessionMiddleware


async def test_middleware_injects_async_session():
    middleware = DbSessionMiddleware()
    received = {}

    async def handler(event, data):
        received["session"] = data.get("session")
        return "ok"

    result = await middleware(handler, event=object(), data={})

    assert result == "ok"
    assert isinstance(received["session"], AsyncSession)
