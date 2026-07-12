from unittest.mock import AsyncMock

from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.fsm.storage.memory import MemoryStorage
from sqlalchemy import select

from bot.handlers.start import cmd_start, process_contact, process_name
from bot.states import Registration
from db.models import User


def _make_state() -> FSMContext:
    storage = MemoryStorage()
    key = StorageKey(bot_id=1, chat_id=1, user_id=1)
    return FSMContext(storage=storage, key=key)


def _make_message(text: str, user_id: int = 1):
    message = AsyncMock()
    message.text = text
    message.from_user.id = user_id
    return message


async def test_start_new_user_sends_welcome_and_asks_name(session):
    message = _make_message("/start")
    state = _make_state()

    await cmd_start(message, state, session)

    assert await state.get_state() == Registration.waiting_for_name.state
    assert message.answer.await_count == 2
    assert "Добро пожаловать" in message.answer.call_args_list[0].args[0]
    assert "зовут" in message.answer.call_args_list[1].args[0]


async def test_start_existing_user_shows_main_menu(session):
    session.add(User(telegram_id=1, name="Аня", contact="@anya"))
    await session.commit()

    message = _make_message("/start")
    state = _make_state()

    await cmd_start(message, state, session)

    assert message.answer.await_count == 2
    assert "С возвращением" in message.answer.call_args_list[0].args[0]


async def test_process_name_asks_for_contact():
    message = _make_message("Аня")
    state = _make_state()
    await state.set_state(Registration.waiting_for_name)

    await process_name(message, state)

    assert await state.get_state() == Registration.waiting_for_contact.state
    data = await state.get_data()
    assert data["name"] == "Аня"
    message.answer.assert_awaited_once()
    assert "связаться" in message.answer.call_args.args[0]


async def test_process_name_rejects_empty():
    message = _make_message("   ")
    state = _make_state()
    await state.set_state(Registration.waiting_for_name)

    await process_name(message, state)

    assert await state.get_state() == Registration.waiting_for_name.state


async def test_process_contact_creates_user(session):
    message = _make_message("@anya", user_id=42)
    state = _make_state()
    await state.set_state(Registration.waiting_for_contact)
    await state.update_data(name="Аня")

    await process_contact(message, state, session)

    result = await session.execute(select(User).where(User.telegram_id == 42))
    user = result.scalar_one()
    assert user.name == "Аня"
    assert user.contact == "@anya"
    assert await state.get_state() is None
