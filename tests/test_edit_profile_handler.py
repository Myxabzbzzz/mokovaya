from datetime import datetime, timedelta
from unittest.mock import AsyncMock

from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.fsm.storage.memory import MemoryStorage
from sqlalchemy import select

from bot.handlers.edit_profile import process_new_contact, process_new_name, start_edit_profile
from bot.states import EditProfile
from bot.validators import RESERVED_VALUE_REPLY, SQL_INJECTION_REPLY
from db.models import User


def _make_state() -> FSMContext:
    storage = MemoryStorage()
    key = StorageKey(bot_id=1, chat_id=1, user_id=1)
    return FSMContext(storage=storage, key=key)


def _make_callback(user_id: int = 1):
    callback = AsyncMock()
    callback.from_user.id = user_id
    callback.message = AsyncMock()
    return callback


def _make_message(text: str, user_id: int = 1):
    message = AsyncMock()
    message.text = text
    message.from_user.id = user_id
    return message


async def _make_user(session, telegram_id=1, name="Аня", contact="@anya", profile_updated_at=None):
    user = User(
        telegram_id=telegram_id,
        name=name,
        contact=contact,
        profile_updated_at=profile_updated_at,
    )
    session.add(user)
    await session.commit()
    return user


async def test_start_edit_profile_first_time_has_no_cooldown(session):
    await _make_user(session, profile_updated_at=None)
    callback = _make_callback()
    state = _make_state()

    await start_edit_profile(callback, session, state)

    callback.answer.assert_awaited_once_with()
    assert await state.get_state() == EditProfile.waiting_for_name.state
    callback.message.answer.assert_awaited_once()
    assert "зовут" in callback.message.answer.call_args.args[0]


async def test_start_edit_profile_within_cooldown_shows_alert(session):
    await _make_user(session, profile_updated_at=datetime.utcnow())
    callback = _make_callback()
    state = _make_state()

    await start_edit_profile(callback, session, state)

    callback.answer.assert_awaited_once_with(
        "Менять имя и юзернейм можно раз в сутки, попробуй позже", show_alert=True
    )
    assert await state.get_state() is None
    callback.message.answer.assert_not_awaited()


async def test_start_edit_profile_after_cooldown_elapsed(session):
    await _make_user(session, profile_updated_at=datetime.utcnow() - timedelta(hours=25))
    callback = _make_callback()
    state = _make_state()

    await start_edit_profile(callback, session, state)

    callback.answer.assert_awaited_once_with()
    assert await state.get_state() == EditProfile.waiting_for_name.state


async def test_process_new_name_rejects_empty():
    message = _make_message("   ")
    state = _make_state()
    await state.set_state(EditProfile.waiting_for_name)

    await process_new_name(message, state)

    assert await state.get_state() == EditProfile.waiting_for_name.state


async def test_process_new_name_rejects_reserved_value():
    message = _make_message("Myxa")
    state = _make_state()
    await state.set_state(EditProfile.waiting_for_name)

    await process_new_name(message, state)

    assert await state.get_state() == EditProfile.waiting_for_name.state
    message.answer.assert_awaited_once_with(RESERVED_VALUE_REPLY)


async def test_process_new_contact_rejects_sql_injection(session):
    await _make_user(session, telegram_id=42)
    message = _make_message("'; DROP TABLE users; --", user_id=42)
    state = _make_state()
    await state.set_state(EditProfile.waiting_for_contact)
    await state.update_data(name="Аня")

    await process_new_contact(message, state, session)

    assert await state.get_state() == EditProfile.waiting_for_contact.state
    message.answer.assert_awaited_once_with(SQL_INJECTION_REPLY)


async def test_process_new_name_then_contact_updates_user(session):
    await _make_user(session, telegram_id=42, name="Old", contact="@old")
    name_message = _make_message("Новое имя", user_id=42)
    state = _make_state()
    await state.set_state(EditProfile.waiting_for_name)

    await process_new_name(name_message, state)

    assert await state.get_state() == EditProfile.waiting_for_contact.state

    contact_message = _make_message("@new_contact", user_id=42)
    await process_new_contact(contact_message, state, session)

    result = await session.execute(select(User).where(User.telegram_id == 42))
    user = result.scalar_one()
    assert user.name == "Новое имя"
    assert user.contact == "@new_contact"
    assert user.profile_updated_at is not None
    assert await state.get_state() is None
