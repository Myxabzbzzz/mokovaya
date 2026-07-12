from datetime import datetime, timedelta

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.handlers.menu import send_main_menu
from bot.states import EditProfile
from bot.validators import (
    RESERVED_VALUE_REPLY,
    SQL_INJECTION_REPLY,
    is_reserved_value,
    looks_like_sql_injection,
)
from db.models import User

router = Router()

EDIT_COOLDOWN = timedelta(days=1)


async def _current_user(session: AsyncSession, telegram_id: int) -> User:
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    return result.scalar_one()


@router.callback_query(F.data == "edit_profile")
async def start_edit_profile(
    callback: CallbackQuery, session: AsyncSession, state: FSMContext
) -> None:
    user = await _current_user(session, callback.from_user.id)

    if (
        user.profile_updated_at is not None
        and datetime.utcnow() - user.profile_updated_at < EDIT_COOLDOWN
    ):
        await callback.answer(
            "Менять имя и юзернейм можно раз в сутки, попробуй позже", show_alert=True
        )
        return

    await callback.answer()
    await state.set_state(EditProfile.waiting_for_name)
    await callback.message.answer("Как тебя теперь зовут?")


@router.message(EditProfile.waiting_for_name)
async def process_new_name(message: Message, state: FSMContext) -> None:
    name = (message.text or "").strip()
    if not name:
        await message.answer("Пожалуйста, напиши своё имя текстом.")
        return

    if looks_like_sql_injection(name):
        await message.answer(SQL_INJECTION_REPLY)
        return

    if is_reserved_value(name):
        await message.answer(RESERVED_VALUE_REPLY)
        return

    await state.update_data(name=name[:255])
    await state.set_state(EditProfile.waiting_for_contact)
    await message.answer("Как с тобой можно связаться? Напиши Telegram-юзернейм или номер телефона")


@router.message(EditProfile.waiting_for_contact)
async def process_new_contact(
    message: Message, state: FSMContext, session: AsyncSession
) -> None:
    contact = (message.text or "").strip()
    if not contact:
        await message.answer("Напиши, пожалуйста, юзернейм или номер телефона текстом.")
        return

    if looks_like_sql_injection(contact):
        await message.answer(SQL_INJECTION_REPLY)
        return

    if is_reserved_value(contact):
        await message.answer(RESERVED_VALUE_REPLY)
        return

    data = await state.get_data()
    user = await _current_user(session, message.from_user.id)
    user.name = data["name"]
    user.contact = contact[:255]
    user.profile_updated_at = datetime.utcnow()
    await session.commit()

    await state.clear()
    await message.answer(f"Готово, {user.name}! Профиль обновлён 🎉")
    await send_main_menu(message)
