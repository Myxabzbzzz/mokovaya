from datetime import datetime, timedelta

import pytest
from sqlalchemy import select

from db.models import Match, QueueEntry, QueueRole, QueueStatus, User
from services.matching import (
    AlreadyInQueueError,
    NotInQueueError,
    RecentlyMatchedError,
    cancel_queue,
    join_queue,
)


async def _make_user(session, telegram_id, name, contact):
    user = User(telegram_id=telegram_id, name=name, contact=contact)
    session.add(user)
    await session.flush()
    return user


async def test_join_queue_waits_when_no_partner(session):
    user = await _make_user(session, 1, "Аня", "@anya")

    result = await join_queue(session, user.id, QueueRole.candidate)

    assert isinstance(result, QueueEntry)
    assert result.status == QueueStatus.waiting
    assert result.role == QueueRole.candidate


async def test_join_queue_matches_with_waiting_partner(session):
    candidate = await _make_user(session, 1, "Аня", "@anya")
    interviewer = await _make_user(session, 2, "Боря", "@borya")

    await join_queue(session, candidate.id, QueueRole.candidate)
    result = await join_queue(session, interviewer.id, QueueRole.interviewer)

    assert isinstance(result, Match)
    assert result.candidate_id == candidate.id
    assert result.interviewer_id == interviewer.id


async def test_matched_entries_are_marked_matched(session):
    candidate = await _make_user(session, 1, "Аня", "@anya")
    interviewer = await _make_user(session, 2, "Боря", "@borya")

    await join_queue(session, candidate.id, QueueRole.candidate)
    await join_queue(session, interviewer.id, QueueRole.interviewer)

    result = await session.execute(select(QueueEntry))
    entries = result.scalars().all()
    assert all(entry.status == QueueStatus.matched for entry in entries)


async def test_join_queue_twice_raises(session):
    user = await _make_user(session, 1, "Аня", "@anya")
    await join_queue(session, user.id, QueueRole.candidate)

    with pytest.raises(AlreadyInQueueError):
        await join_queue(session, user.id, QueueRole.candidate)


async def test_fifo_order_matches_earliest_waiting_partner(session):
    first_candidate = await _make_user(session, 1, "Первая", "@first")
    second_candidate = await _make_user(session, 2, "Вторая", "@second")
    interviewer = await _make_user(session, 3, "Интервьюер", "@interviewer")

    await join_queue(session, first_candidate.id, QueueRole.candidate)
    await join_queue(session, second_candidate.id, QueueRole.candidate)
    result = await join_queue(session, interviewer.id, QueueRole.interviewer)

    assert isinstance(result, Match)
    assert result.candidate_id == first_candidate.id


async def test_cancel_queue_marks_entry_cancelled(session):
    user = await _make_user(session, 1, "Аня", "@anya")
    await join_queue(session, user.id, QueueRole.candidate)

    await cancel_queue(session, user.id)

    result = await session.execute(select(QueueEntry).where(QueueEntry.user_id == user.id))
    entry = result.scalar_one()
    assert entry.status == QueueStatus.cancelled


async def test_cancel_queue_when_not_waiting_raises(session):
    user = await _make_user(session, 1, "Аня", "@anya")

    with pytest.raises(NotInQueueError):
        await cancel_queue(session, user.id)


async def test_join_queue_after_cancel_waits_again(session):
    user = await _make_user(session, 1, "Аня", "@anya")
    await join_queue(session, user.id, QueueRole.candidate)
    await cancel_queue(session, user.id)

    result = await join_queue(session, user.id, QueueRole.candidate)

    assert isinstance(result, QueueEntry)
    assert result.status == QueueStatus.waiting


async def test_join_queue_soon_after_match_raises(session):
    candidate = await _make_user(session, 1, "Аня", "@anya")
    interviewer = await _make_user(session, 2, "Боря", "@borya")
    await join_queue(session, candidate.id, QueueRole.candidate)
    await join_queue(session, interviewer.id, QueueRole.interviewer)

    with pytest.raises(RecentlyMatchedError):
        await join_queue(session, candidate.id, QueueRole.candidate)


async def test_join_queue_after_cooldown_elapsed_succeeds(session):
    candidate = await _make_user(session, 1, "Аня", "@anya")
    interviewer = await _make_user(session, 2, "Боря", "@borya")
    await join_queue(session, candidate.id, QueueRole.candidate)
    match = await join_queue(session, interviewer.id, QueueRole.interviewer)

    match.matched_at = datetime.utcnow() - timedelta(minutes=11)
    await session.commit()

    result = await join_queue(session, candidate.id, QueueRole.candidate)

    assert isinstance(result, QueueEntry)
    assert result.status == QueueStatus.waiting
