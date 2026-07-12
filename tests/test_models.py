from datetime import datetime

from sqlalchemy import select

from db.models import Match, QueueEntry, QueueRole, QueueStatus, User


async def test_create_and_query_user(session):
    user = User(telegram_id=123, name="Аня", contact="@anya")
    session.add(user)
    await session.commit()

    result = await session.execute(select(User).where(User.telegram_id == 123))
    fetched = result.scalar_one()
    assert fetched.name == "Аня"
    assert fetched.contact == "@anya"
    assert isinstance(fetched.created_at, datetime)
    assert fetched.profile_updated_at is None


async def test_queue_entry_defaults_to_waiting(session):
    user = User(telegram_id=456, name="Боря", contact="+79990000000")
    session.add(user)
    await session.flush()

    entry = QueueEntry(user_id=user.id, role=QueueRole.candidate)
    session.add(entry)
    await session.commit()

    result = await session.execute(select(QueueEntry).where(QueueEntry.user_id == user.id))
    fetched = result.scalar_one()
    assert fetched.status == QueueStatus.waiting
    assert fetched.role == QueueRole.candidate


async def test_match_links_two_users(session):
    interviewer = User(telegram_id=1, name="Interviewer", contact="@i")
    candidate = User(telegram_id=2, name="Candidate", contact="@c")
    session.add_all([interviewer, candidate])
    await session.flush()

    match = Match(interviewer_id=interviewer.id, candidate_id=candidate.id)
    session.add(match)
    await session.commit()

    result = await session.execute(select(Match))
    fetched = result.scalar_one()
    assert fetched.interviewer_id == interviewer.id
    assert fetched.candidate_id == candidate.id
