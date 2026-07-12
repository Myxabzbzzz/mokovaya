from typing import Union

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Match, QueueEntry, QueueRole, QueueStatus

OPPOSITE_ROLE = {
    QueueRole.interviewer: QueueRole.candidate,
    QueueRole.candidate: QueueRole.interviewer,
}


class AlreadyInQueueError(Exception):
    pass


class NotInQueueError(Exception):
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

    # Tiebreak on id: server_default=func.now() has only 1-second resolution on
    # SQLite (used in tests), so two entries created in the same second would
    # otherwise sort arbitrarily.
    partner_result = await session.execute(
        select(QueueEntry)
        .where(
            QueueEntry.role == OPPOSITE_ROLE[role],
            QueueEntry.status == QueueStatus.waiting,
        )
        .order_by(QueueEntry.joined_at.asc(), QueueEntry.id.asc())
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
