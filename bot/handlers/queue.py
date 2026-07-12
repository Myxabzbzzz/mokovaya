from aiogram import Bot, F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.handlers.menu import send_main_menu
from db.models import Match, QueueRole, User
from services.matching import AlreadyInQueueError, NotInQueueError, cancel_queue, join_queue

router = Router()

CANCEL_KEYBOARD = InlineKeyboardMarkup(
    inline_keyboard=[[InlineKeyboardButton(text="❌ Отменить поиск", callback_data="cancel_search")]]
)

ROLE_LABELS = {
    QueueRole.interviewer: "интервьюером",
    QueueRole.candidate: "кандидатом",
}


async def _current_user(session: AsyncSession, telegram_id: int) -> User:
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    return result.scalar_one()


async def _notify_match(bot: Bot, session: AsyncSession, match: Match) -> None:
    interviewer = await session.get(User, match.interviewer_id)
    candidate = await session.get(User, match.candidate_id)

    await bot.send_message(
        interviewer.telegram_id,
        "Найден партнёр! Ты — интервьюер.\n"
        f"Кандидат: {candidate.name}\nКонтакт: {candidate.contact}\n\n"
        "Договоритесь о времени сами.",
    )
    await bot.send_message(
        candidate.telegram_id,
        "Найден партнёр! Ты — кандидат.\n"
        f"Интервьюер: {interviewer.name}\nКонтакт: {interviewer.contact}\n\n"
        "Договоритесь о времени сами.",
    )


async def _join(callback: CallbackQuery, session: AsyncSession, bot: Bot, role: QueueRole) -> None:
    user = await _current_user(session, callback.from_user.id)

    try:
        result = await join_queue(session, user.id, role)
    except AlreadyInQueueError:
        await callback.answer(
            "Ты уже в очереди, отмени поиск, если хочешь передумать", show_alert=True
        )
        return

    await callback.answer()

    if isinstance(result, Match):
        await _notify_match(bot, session, result)
        return

    await callback.message.answer(
        f"Ищем партнёра ({ROLE_LABELS[role]})... Можно отменить поиск.",
        reply_markup=CANCEL_KEYBOARD,
    )


@router.callback_query(F.data == "join_interviewer")
async def join_interviewer(callback: CallbackQuery, session: AsyncSession, bot: Bot) -> None:
    await _join(callback, session, bot, QueueRole.interviewer)


@router.callback_query(F.data == "join_candidate")
async def join_candidate(callback: CallbackQuery, session: AsyncSession, bot: Bot) -> None:
    await _join(callback, session, bot, QueueRole.candidate)


@router.callback_query(F.data == "cancel_search")
async def cancel_search(callback: CallbackQuery, session: AsyncSession) -> None:
    user = await _current_user(session, callback.from_user.id)

    try:
        await cancel_queue(session, user.id)
    except NotInQueueError:
        await callback.answer("Ты не в очереди", show_alert=True)
        return

    await callback.answer()
    await callback.message.answer("Поиск отменён.")
    await send_main_menu(callback.message)
