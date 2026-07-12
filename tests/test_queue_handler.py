from unittest.mock import AsyncMock

from bot.handlers.queue import cancel_search, join_candidate, join_interviewer
from db.models import User


def _make_callback(user_id: int):
    callback = AsyncMock()
    callback.from_user.id = user_id
    callback.message = AsyncMock()
    return callback


async def _make_user(session, telegram_id, name, contact):
    user = User(telegram_id=telegram_id, name=name, contact=contact)
    session.add(user)
    await session.commit()
    return user


async def test_join_interviewer_waits_when_no_candidate(session):
    await _make_user(session, 1, "Боря", "@borya")
    callback = _make_callback(1)
    bot = AsyncMock()

    await join_interviewer(callback, session, bot)

    callback.answer.assert_awaited_once_with()
    callback.message.answer.assert_awaited_once()
    assert "Ищем партнёра" in callback.message.answer.call_args.args[0]
    bot.send_message.assert_not_awaited()


async def test_join_candidate_after_interviewer_notifies_both(session):
    await _make_user(session, 1, "Боря", "@borya")
    await _make_user(session, 2, "Аня", "@anya")
    bot = AsyncMock()

    await join_interviewer(_make_callback(1), session, bot)
    await join_candidate(_make_callback(2), session, bot)

    assert bot.send_message.await_count == 2
    sent_to = {call.args[0] for call in bot.send_message.call_args_list}
    assert sent_to == {1, 2}


async def test_join_when_already_in_queue_shows_alert(session):
    await _make_user(session, 1, "Боря", "@borya")
    bot = AsyncMock()

    await join_interviewer(_make_callback(1), session, bot)
    second_callback = _make_callback(1)
    await join_interviewer(second_callback, session, bot)

    second_callback.answer.assert_awaited_once_with(
        "Ты уже в очереди, отмени поиск, если хочешь передумать", show_alert=True
    )


async def test_cancel_search_when_not_in_queue_shows_alert(session):
    await _make_user(session, 1, "Боря", "@borya")
    callback = _make_callback(1)

    await cancel_search(callback, session)

    callback.answer.assert_awaited_once_with("Ты не в очереди", show_alert=True)


async def test_cancel_search_removes_from_queue(session):
    await _make_user(session, 1, "Боря", "@borya")
    bot = AsyncMock()
    await join_interviewer(_make_callback(1), session, bot)

    callback = _make_callback(1)
    await cancel_search(callback, session)

    callback.message.answer.assert_any_call("Поиск отменён.")
