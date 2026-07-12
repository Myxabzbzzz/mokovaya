from datetime import datetime, timedelta
from typing import Union

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Match, QueueEntry, QueueRole, QueueStatus

OPPOSITE_ROLE = {
    QueueRole.interviewer: QueueRole.candidate,
    QueueRole.candidate: QueueRole.interviewer,
}

# Minimum time a user must wait after being matched before they can join the
# queue again. Without this, a user could cycle join->match->join indefinitely
# to harvest the contact info of many strangers in a short time.
REMATCH_COOLDOWN = timedelta(minutes=10)


class AlreadyInQueueError(Exception):
    pass


class NotInQueueError(Exception):
    pass


class RecentlyMatchedError(Exception):
    pass


async def join_queue(
    session: AsyncSession, user_id: int, role: QueueRole
) -> Union[QueueEntry, Match]:
    existing = await session.execute(
        select(QueueEntry).where(
            QueueEntry.user_id == user_id,
            QueueEntry.status == QueueStatus.waiting,
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise AlreadyInQueueError()

    last_match_result = await session.execute(
        select(Match)
        .where(or_(Match.interviewer_id == user_id, Match.candidate_id == user_id))
        .order_by(Match.matched_at.desc())
        .limit(1)
    )
    last_match = last_match_result.scalar_one_or_none()
    if last_match is not None and datetime.utcnow() - last_match.matched_at < REMATCH_COOLDOWN:
        raise RecentlyMatchedError()

    # Tiebreak on id: server_default=func.now() has only 1-second resolution on
    # SQLite (used in tests), so two entries created in the same second would
    # otherwise sort arbitrarily.
    # with_for_update(skip_locked=True) prevents a race under real concurrency
    # (e.g. Postgres): without a row lock, two concurrent transactions could
    # both read the same waiting partner before either commits, producing two
    # Match rows for the same partner. This is a no-op on SQLite (used in
    # tests), which doesn't support FOR UPDATE and renders nothing for it.
    partner_result = await session.execute(
        select(QueueEntry)
        .where(
            QueueEntry.role == OPPOSITE_ROLE[role],
            QueueEntry.status == QueueStatus.waiting,
        )
        .order_by(QueueEntry.joined_at.asc(), QueueEntry.id.asc())
        .with_for_update(skip_locked=True)
        .limit(1)
    )
    partner_entry = partner_result.scalar_one_or_none()

    entry = QueueEntry(user_id=user_id, role=role, status=QueueStatus.waiting)
    session.add(entry)
    await session.flush()

    if partner_entry is None:
        await session.commit()
        return entry

    partner_entry.status = QueueStatus.matched
    entry.status = QueueStatus.matched

    interviewer_id = user_id if role == QueueRole.interviewer else partner_entry.user_id
    candidate_id = user_id if role == QueueRole.candidate else partner_entry.user_id

    match = Match(interviewer_id=interviewer_id, candidate_id=candidate_id)
    session.add(match)
    await session.commit()
    await session.refresh(match)
    return match


async def cancel_queue(session: AsyncSession, user_id: int) -> None:
    result = await session.execute(
        select(QueueEntry).where(
            QueueEntry.user_id == user_id,
            QueueEntry.status == QueueStatus.waiting,
        )
    )
    entry = result.scalar_one_or_none()
    if entry is None:
        raise NotInQueueError()

    entry.status = QueueStatus.cancelled
    await session.commit()
