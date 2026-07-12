import enum
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base


class QueueRole(str, enum.Enum):
    interviewer = "interviewer"
    candidate = "candidate"


class QueueStatus(str, enum.Enum):
    waiting = "waiting"
    matched = "matched"
    cancelled = "cancelled"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    contact: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )


class QueueEntry(Base):
    __tablename__ = "queue"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    role: Mapped[QueueRole] = mapped_column(Enum(QueueRole), nullable=False)
    status: Mapped[QueueStatus] = mapped_column(
        Enum(QueueStatus), default=QueueStatus.waiting, nullable=False
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship()


class Match(Base):
    __tablename__ = "matches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    interviewer_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    matched_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
