import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand

from bot.handlers import edit_profile, queue, start, tasks
from bot.middlewares.db import DbSessionMiddleware
from bot.middlewares.throttling import ThrottlingMiddleware
from config.settings import settings


def build_dispatcher() -> Dispatcher:
    dp = Dispatcher()
    dp.update.middleware(DbSessionMiddleware())
    dp.callback_query.middleware(ThrottlingMiddleware())
    dp.include_router(start.router)
    dp.include_router(queue.router)
    dp.include_router(edit_profile.router)
    dp.include_router(tasks.router)
    return dp


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stdout,
    )

    bot = Bot(token=settings.bot_token)
    dp = build_dispatcher()

    await bot.set_my_commands([
        BotCommand(command="start", description="Начать / главное меню"),
    ])

    logging.info("Starting bot...")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
