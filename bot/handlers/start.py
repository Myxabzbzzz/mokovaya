from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.handlers.menu import send_main_menu
from bot.states import Registration
from bot.validators import (
    RESERVED_VALUE_REPLY,
    SQL_INJECTION_REPLY,
    is_reserved_value,
    looks_like_sql_injection,
)
from db.models import User

router = Router()

WELCOME_TEXT = (
    "Добро пожаловать в Моковую 👋\n"
    "Здесь можно тренировать алгоритмические собеседования вживую — с реальным человеком, а не с ботом.\n\n"
    "Как это работает:\n"
    "🎤 Ты — интервьюер. Задаёшь задачу и оцениваешь решение — как настоящий интервьюер в компании.\n"
    "💻 Ты — кандидат. Решаешь задачу под наблюдением, как на реальном собеседовании.\n\n"
    "Роль выбираешь каждый раз заново — можно сегодня быть интервьюером, завтра кандидатом. "
    "Многие делают оба захода подряд: сначала спрашивают сами, потом отвечают.\n\n"
    "Бот подбирает пару и даёт контакт для связи — дальше вы сами договариваетесь о времени и площадке для звонка."
)


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, session: AsyncSession) -> None:
    result = await session.execute(
        select(User).where(User.telegram_id == message.from_user.id)
    )
    user = result.scalar_one_or_none()

    if user is not None:
        await state.clear()
        await message.answer(f"С возвращением, {user.name}! 👋")
        await send_main_menu(message)
        return

    await state.set_state(Registration.waiting_for_name)
    await message.answer(WELCOME_TEXT)
    await message.answer("Как тебя зовут?")


@router.message(Registration.waiting_for_name)
async def process_name(message: Message, state: FSMContext) -> None:
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
    await state.set_state(Registration.waiting_for_contact)
    await message.answer("Как с тобой можно связаться? Напиши Telegram-юзернейм или номер телефона")


@router.message(Registration.waiting_for_contact)
async def process_contact(message: Message, state: FSMContext, session: AsyncSession) -> None:
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
    user = User(
        telegram_id=message.from_user.id,
        name=data["name"],
        contact=contact[:255],
    )
    session.add(user)
    await session.commit()

    await state.clear()
    await message.answer(f"Отлично, {user.name}! Ты зарегистрирован(а) 🎉")
    await send_main_menu(message)
