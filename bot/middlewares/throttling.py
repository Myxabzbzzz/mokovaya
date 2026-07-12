import time
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery


class ThrottlingMiddleware(BaseMiddleware):
    def __init__(
        self,
        rate_limit: float = 2.0,
        time_func: Callable[[], float] = time.monotonic,
    ) -> None:
        self.rate_limit = rate_limit
        self._time_func = time_func
        self._last_call: Dict[int, float] = {}

    async def __call__(
        self,
        handler: Callable[[CallbackQuery, Dict[str, Any]], Awaitable[Any]],
        event: CallbackQuery,
        data: Dict[str, Any],
    ) -> Any:
        user_id = event.from_user.id
        now = self._time_func()
        last_call = self._last_call.get(user_id)

        if last_call is not None and now - last_call < self.rate_limit:
            await event.answer("Слишком быстро, подожди немного", show_alert=True)
            return None

        self._last_call[user_id] = now
        return await handler(event, data)
