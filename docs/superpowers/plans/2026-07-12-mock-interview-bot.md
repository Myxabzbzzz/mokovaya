# Моковая — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Telegram bot that lets two people find each other for a live algorithmic mock interview — one joins as interviewer, one as candidate, the bot matches them FIFO and hands over contact info; the interview itself happens outside the bot.

**Architecture:** aiogram 3 bot with FSM-based registration, a PostgreSQL database (SQLAlchemy 2.0 async models, alembic migrations), and a small pure-function matching service that owns all queue/match logic so it can be unit-tested without touching Telegram at all. Handlers are thin — they translate Telegram events into calls to the matching service and format the responses.

**Tech Stack:** Python 3.10+, aiogram>=3.0, SQLAlchemy>=2.0 (asyncio), asyncpg (runtime DB driver), psycopg2-binary (alembic sync driver), alembic, pydantic-settings, pytest + pytest-asyncio + aiosqlite (tests only, in-memory DB — no local Postgres required to run the test suite).

## Global Constraints

- Registration and menu copy must match the spec verbatim (see `docs/superpowers/specs/2026-07-12-mock-interview-bot-design.md` §2–3): the welcome text, the two role button labels (`🎤 Хочу собеседовать`, `💻 Хочу пройти собеседование`), and the contact question (`Как с тобой можно связаться? Напиши Telegram-юзернейм или номер телефона`).
- Contact field (`users.contact`) is free-text — no format validation, no distinguishing phone vs. username.
- Matching is role-only FIFO (earliest `joined_at` in the opposite queue wins). No language/level filtering — out of scope for MVP.
- No queue timeout/auto-cancellation — a user waits until matched or until they cancel manually.
- Do not build: in-bot code editor, video/audio, scheduling/slots, ratings/feedback. These are explicitly out of scope per the spec's §6.
- Follow the conventions already established in the sibling project `Well Prepared bot` (aiogram Router-per-feature, `DbSessionMiddleware` injecting `session` into handler data, SQLAlchemy `Mapped`/`mapped_column` models, `pydantic_settings.BaseSettings` for config, alembic with a hand-written sync migration).

---

## File Structure

```
моковая/
├── pyproject.toml
├── requirements.txt
├── .env.example
├── .gitignore
├── alembic.ini
├── config/
│   ├── __init__.py
│   └── settings.py          # Settings (bot_token, database_url)
├── db/
│   ├── __init__.py
│   ├── base.py               # Base, engine, async_session
│   └── models.py             # User, QueueEntry, Match, QueueRole, QueueStatus
├── services/
│   ├── __init__.py
│   └── matching.py           # join_queue, cancel_queue — all queue/match logic
├── bot/
│   ├── __init__.py
│   ├── main.py                # build_dispatcher(), main()
│   ├── states.py              # Registration FSM states
│   ├── middlewares/
│   │   ├── __init__.py
│   │   └── db.py              # DbSessionMiddleware
│   └── handlers/
│       ├── __init__.py
│       ├── menu.py            # main_menu_keyboard(), send_main_menu()
│       ├── start.py           # /start, registration (name + contact)
│       └── queue.py           # join_interviewer/join_candidate/cancel_search + match notification
├── migrations/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       └── 0001_initial.py
└── tests/
    ├── __init__.py
    ├── conftest.py            # in-memory sqlite `session` fixture
    ├── test_settings.py
    ├── test_models.py
    ├── test_matching.py
    ├── test_db_middleware.py
    ├── test_menu.py
    ├── test_start_handler.py
    ├── test_queue_handler.py
    └── test_main.py
```

---

### Task 1: Project scaffolding & settings

**Files:**
- Create: `pyproject.toml`
- Create: `requirements.txt`
- Create: `.env.example`
- Create: `.gitignore`
- Create: `config/__init__.py`
- Create: `config/settings.py`
- Test: `tests/test_settings.py`
- Create: `tests/__init__.py`

**Interfaces:**
- Produces: `config.settings.Settings` (pydantic `BaseSettings` with fields `bot_token: str`, `database_url: str`) and a module-level `settings = Settings()` instance. Every later task that needs config imports `from config.settings import settings`.

- [ ] **Step 1: Create the project directories and non-Python files**

```bash
mkdir -p "/Users/myxabzbzzzz/РАБОТА/моковая/config" \
         "/Users/myxabzbzzzz/РАБОТА/моковая/db" \
         "/Users/myxabzbzzzz/РАБОТА/моковая/services" \
         "/Users/myxabzbzzzz/РАБОТА/моковая/bot/middlewares" \
         "/Users/myxabzbzzzz/РАБОТА/моковая/bot/handlers" \
         "/Users/myxabzbzzzz/РАБОТА/моковая/tests"
```

`pyproject.toml`:

```toml
[build-system]
requires = ["setuptools>=68.0", "wheel"]
build-backend = "setuptools.backends._legacy:_Backend"

[project]
name = "mokovaya-bot"
version = "0.1.0"
description = "Telegram bot for peer-to-peer algorithmic mock interviews"
requires-python = ">=3.10"
dependencies = [
    "aiogram>=3.0",
    "sqlalchemy[asyncio]>=2.0",
    "asyncpg>=0.29",
    "psycopg2-binary>=2.9",
    "alembic>=1.13",
    "python-dotenv>=1.0",
    "pydantic>=2.0",
    "pydantic-settings>=2.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-asyncio>=0.21",
    "aiosqlite>=0.19",
]

[tool.setuptools.packages.find]
include = ["bot*", "services*", "db*", "config*"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
```

`requirements.txt`:

```
aiogram>=3.0
sqlalchemy[asyncio]>=2.0
asyncpg>=0.29
psycopg2-binary>=2.9
alembic>=1.13
python-dotenv>=1.0
pydantic>=2.0
pydantic-settings>=2.0
pytest>=7.0
pytest-asyncio>=0.21
aiosqlite>=0.19
```

`.env.example`:

```
# Telegram Bot
BOT_TOKEN=your_bot_token_here

# PostgreSQL
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/mokovaya
```

`.gitignore`:

```
__pycache__/
*.pyc
.venv/
.env
*.egg-info/
.pytest_cache/
```

`tests/__init__.py`: empty file.

- [ ] **Step 2: Write the failing test for settings**

`tests/test_settings.py`:

```python
from config.settings import Settings


def test_settings_reads_env_vars(monkeypatch):
    monkeypatch.setenv("BOT_TOKEN", "test-token-123")
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@host/db")

    settings = Settings(_env_file=None)

    assert settings.bot_token == "test-token-123"
    assert settings.database_url == "postgresql+asyncpg://u:p@host/db"


def test_settings_has_sane_defaults():
    settings = Settings(_env_file=None)

    assert settings.bot_token == ""
    assert "postgresql+asyncpg" in settings.database_url
```

- [ ] **Step 3: Run test to verify it fails**

Run: `cd "/Users/myxabzbzzzz/РАБОТА/моковая" && python -m pytest tests/test_settings.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'config'` (or `config.settings` not found).

- [ ] **Step 4: Implement `config/settings.py`**

`config/__init__.py`: empty file.

`config/settings.py`:

```python
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    bot_token: str = ""
    database_url: str = "postgresql+asyncpg://user:password@localhost:5432/mokovaya"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd "/Users/myxabzbzzzz/РАБОТА/моковая" && python -m pytest tests/test_settings.py -v`
Expected: PASS (2 passed)

- [ ] **Step 6: Commit**

```bash
cd "/Users/myxabzbzzzz/РАБОТА/моковая"
git add pyproject.toml requirements.txt .env.example .gitignore config/ tests/
git commit -m "feat: scaffold project and add settings"
```

---

### Task 2: DB base + models

**Files:**
- Create: `db/__init__.py`
- Create: `db/base.py`
- Create: `db/models.py`
- Create: `tests/conftest.py`
- Test: `tests/test_models.py`

**Interfaces:**
- Consumes: `config.settings.settings` (Task 1).
- Produces:
  - `db.base.Base` (SQLAlchemy `DeclarativeBase`), `db.base.engine`, `db.base.async_session` (`async_sessionmaker`).
  - `db.models.User(telegram_id: int, name: str, contact: str)`.
  - `db.models.QueueRole` enum: `interviewer`, `candidate`.
  - `db.models.QueueStatus` enum: `waiting`, `matched`, `cancelled`.
  - `db.models.QueueEntry(user_id: int, role: QueueRole, status: QueueStatus = waiting)`.
  - `db.models.Match(interviewer_id: int, candidate_id: int)`.
  - `tests/conftest.py` provides a pytest-asyncio fixture `session` (fresh in-memory SQLite `AsyncSession` with all tables created) — every later test file that touches the DB depends on this fixture by name.

- [ ] **Step 1: Write the failing tests**

`tests/conftest.py`:

```python
import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from db.base import Base


@pytest_asyncio.fixture
async def session():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as s:
        yield s

    await engine.dispose()
```

`tests/test_models.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd "/Users/myxabzbzzzz/РАБОТА/моковая" && python -m pytest tests/test_models.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'db'`.

- [ ] **Step 3: Implement `db/base.py` and `db/models.py`**

`db/__init__.py`: empty file.

`db/base.py`:

```python
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from config.settings import settings

engine = create_async_engine(settings.database_url, echo=False)
async_session = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass
```

`db/models.py`:

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd "/Users/myxabzbzzzz/РАБОТА/моковая" && python -m pytest tests/test_models.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
cd "/Users/myxabzbzzzz/РАБОТА/моковая"
git add db/ tests/conftest.py tests/test_models.py
git commit -m "feat: add DB base and models (User, QueueEntry, Match)"
```

---

### Task 3: Alembic migration setup

**Files:**
- Create: `alembic.ini`
- Create: `migrations/env.py`
- Create: `migrations/script.py.mako`
- Create: `migrations/versions/__init__.py`
- Create: `migrations/versions/0001_initial.py`

**Interfaces:**
- Consumes: `db.base.Base`, `db.models` (Task 2), `config.settings.settings` (Task 1).
- Produces: a runnable `alembic upgrade head` that creates `users`, `queue`, `matches` tables against a real Postgres database. No unit test — verified by running the migration against Postgres (manual step, documented below), since this is infrastructure, not app logic.

- [ ] **Step 1: Create alembic scaffolding**

`alembic.ini`:

```ini
[alembic]
script_location = migrations
prepend_sys_path = .
sqlalchemy.url = driver://user:pass@localhost/dbname

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```

`migrations/versions/__init__.py`: empty file.

`migrations/script.py.mako`:

```mako
"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
${imports if imports else ""}

revision: str = ${repr(up_revision)}
down_revision: Union[str, None] = ${repr(down_revision)}
branch_labels: Union[str, Sequence[str], None] = ${repr(branch_labels)}
depends_on: Union[str, Sequence[str], None] = ${repr(depends_on)}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
```

`migrations/env.py`:

```python
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import settings  # noqa: E402
from db.base import Base  # noqa: E402
from db.models import *  # noqa: E402, F401, F403 — register all models

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

sync_url = settings.database_url.replace("+asyncpg", "+psycopg2").replace(
    "postgresql://", "postgresql+psycopg2://"
)
if sync_url.startswith("postgresql+psycopg2+psycopg2"):
    sync_url = sync_url.replace("postgresql+psycopg2+psycopg2", "postgresql+psycopg2")
config.set_main_option("sqlalchemy.url", sync_url)


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

- [ ] **Step 2: Hand-write the initial migration**

`migrations/versions/0001_initial.py`:

```python
"""Initial schema — users, queue, matches

Revision ID: 0001_initial
Revises:
Create Date: 2026-07-12

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("telegram_id", sa.BigInteger(), unique=True, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("contact", sa.String(255), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False
        ),
    )

    queue_role_enum = sa.Enum("interviewer", "candidate", name="queuerole")
    queue_status_enum = sa.Enum("waiting", "matched", "cancelled", name="queuestatus")

    op.create_table(
        "queue",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("role", queue_role_enum, nullable=False),
        sa.Column(
            "status", queue_status_enum, nullable=False, server_default="waiting"
        ),
        sa.Column(
            "joined_at", sa.DateTime(), server_default=sa.func.now(), nullable=False
        ),
    )

    op.create_table(
        "matches",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "interviewer_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False
        ),
        sa.Column(
            "candidate_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False
        ),
        sa.Column(
            "matched_at", sa.DateTime(), server_default=sa.func.now(), nullable=False
        ),
    )


def downgrade() -> None:
    op.drop_table("matches")
    op.drop_table("queue")
    op.drop_table("users")
    op.execute("DROP TYPE IF EXISTS queuestatus")
    op.execute("DROP TYPE IF EXISTS queuerole")
```

- [ ] **Step 3: Verify the migration against a local Postgres**

This is infrastructure, not app logic — verify manually rather than via pytest:

```bash
cd "/Users/myxabzbzzzz/РАБОТА/моковая"
createdb mokovaya   # skip if the DB already exists
cp .env.example .env   # then edit .env with a real BOT_TOKEN and DATABASE_URL if needed
python -m alembic upgrade head
```

Expected: alembic prints `Running upgrade  -> 0001_initial, Initial schema — users, queue, matches` and exits 0. If you don't have a local Postgres available, it's fine to defer this verification until Task 9 (running the whole bot) — the rest of this plan's tests run against in-memory SQLite and don't need Postgres.

- [ ] **Step 4: Commit**

```bash
cd "/Users/myxabzbzzzz/РАБОТА/моковая"
git add alembic.ini migrations/
git commit -m "feat: add alembic migration for initial schema"
```

---

### Task 4: Matching service (core queue/match logic)

**Files:**
- Create: `services/__init__.py`
- Create: `services/matching.py`
- Test: `tests/test_matching.py`

**Interfaces:**
- Consumes: `db.models.{User, QueueEntry, QueueRole, QueueStatus, Match}` (Task 2), the `session` fixture (Task 2).
- Produces:
  - `services.matching.AlreadyInQueueError(Exception)`
  - `services.matching.NotInQueueError(Exception)`
  - `async def join_queue(session: AsyncSession, user_id: int, role: QueueRole) -> QueueEntry | Match` — raises `AlreadyInQueueError` if `user_id` already has a `waiting` entry. Returns the new `QueueEntry` (status `waiting`) if no partner is available, or the newly created `Match` if one was found.
  - `async def cancel_queue(session: AsyncSession, user_id: int) -> None` — raises `NotInQueueError` if `user_id` has no `waiting` entry.
  - These two functions are what `bot/handlers/queue.py` (Task 8) calls directly.

- [ ] **Step 1: Write the failing tests**

`tests/test_matching.py`:

```python
import pytest
from sqlalchemy import select

from db.models import Match, QueueEntry, QueueRole, QueueStatus, User
from services.matching import (
    AlreadyInQueueError,
    NotInQueueError,
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd "/Users/myxabzbzzzz/РАБОТА/моковая" && python -m pytest tests/test_matching.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'services'`.

- [ ] **Step 3: Implement `services/matching.py`**

`services/__init__.py`: empty file.

`services/matching.py`:

```python
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
) -> QueueEntry | Match:
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd "/Users/myxabzbzzzz/РАБОТА/моковая" && python -m pytest tests/test_matching.py -v`
Expected: PASS (8 passed)

- [ ] **Step 5: Commit**

```bash
cd "/Users/myxabzbzzzz/РАБОТА/моковая"
git add services/ tests/test_matching.py
git commit -m "feat: add matching service with FIFO role-based queue"
```

---

### Task 5: FSM states + DB session middleware

**Files:**
- Create: `bot/__init__.py`
- Create: `bot/states.py`
- Create: `bot/middlewares/__init__.py`
- Create: `bot/middlewares/db.py`
- Test: `tests/test_db_middleware.py`

**Interfaces:**
- Consumes: `db.base.async_session` (Task 2).
- Produces:
  - `bot.states.Registration` — `StatesGroup` with `waiting_for_name` and `waiting_for_contact` states. Used by `bot/handlers/start.py` (Task 7).
  - `bot.middlewares.db.DbSessionMiddleware` — aiogram `BaseMiddleware` that injects an `AsyncSession` into handler data under the key `"session"`. Registered in `bot/main.py` (Task 9).

- [ ] **Step 1: Write the failing test**

`tests/test_db_middleware.py`:

```python
from sqlalchemy.ext.asyncio import AsyncSession

from bot.middlewares.db import DbSessionMiddleware


async def test_middleware_injects_async_session():
    middleware = DbSessionMiddleware()
    received = {}

    async def handler(event, data):
        received["session"] = data.get("session")
        return "ok"

    result = await middleware(handler, event=object(), data={})

    assert result == "ok"
    assert isinstance(received["session"], AsyncSession)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd "/Users/myxabzbzzzz/РАБОТА/моковая" && python -m pytest tests/test_db_middleware.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'bot'`.

- [ ] **Step 3: Implement states and middleware**

`bot/__init__.py`: empty file.
`bot/middlewares/__init__.py`: empty file.

`bot/states.py`:

```python
from aiogram.fsm.state import State, StatesGroup


class Registration(StatesGroup):
    waiting_for_name = State()
    waiting_for_contact = State()
```

`bot/middlewares/db.py`:

```python
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from db.base import async_session


class DbSessionMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        async with async_session() as session:
            data["session"] = session
            return await handler(event, data)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd "/Users/myxabzbzzzz/РАБОТА/моковая" && python -m pytest tests/test_db_middleware.py -v`
Expected: PASS (1 passed). This does not need a real Postgres connection — `async_session()` only opens a connection lazily on first query, and the test never runs one.

- [ ] **Step 5: Commit**

```bash
cd "/Users/myxabzbzzzz/РАБОТА/моковая"
git add bot/__init__.py bot/states.py bot/middlewares/ tests/test_db_middleware.py
git commit -m "feat: add FSM states and DB session middleware"
```

---

### Task 6: Main menu keyboard

**Files:**
- Create: `bot/handlers/__init__.py`
- Create: `bot/handlers/menu.py`
- Test: `tests/test_menu.py`

**Interfaces:**
- Produces:
  - `bot.handlers.menu.main_menu_keyboard() -> InlineKeyboardMarkup` — two buttons: `callback_data="join_interviewer"` and `callback_data="join_candidate"`.
  - `async def send_main_menu(message: Message) -> None` — sends the menu keyboard via `message.answer(...)`. Used by `bot/handlers/start.py` (Task 7) and `bot/handlers/queue.py` (Task 8).

- [ ] **Step 1: Write the failing test**

`tests/test_menu.py`:

```python
from unittest.mock import AsyncMock

from bot.handlers.menu import main_menu_keyboard, send_main_menu


def test_main_menu_keyboard_has_both_role_buttons():
    keyboard = main_menu_keyboard()

    callback_data = {
        button.callback_data
        for row in keyboard.inline_keyboard
        for button in row
    }
    assert callback_data == {"join_interviewer", "join_candidate"}

    texts = {
        button.text
        for row in keyboard.inline_keyboard
        for button in row
    }
    assert "🎤 Хочу собеседовать" in texts
    assert "💻 Хочу пройти собеседование" in texts


async def test_send_main_menu_calls_message_answer():
    message = AsyncMock()

    await send_main_menu(message)

    message.answer.assert_awaited_once()
    _, kwargs = message.answer.call_args
    assert "reply_markup" in kwargs
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd "/Users/myxabzbzzzz/РАБОТА/моковая" && python -m pytest tests/test_menu.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'bot.handlers'`.

- [ ] **Step 3: Implement `bot/handlers/menu.py`**

`bot/handlers/__init__.py`: empty file.

`bot/handlers/menu.py`:

```python
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message


def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🎤 Хочу собеседовать", callback_data="join_interviewer")],
            [InlineKeyboardButton(text="💻 Хочу пройти собеседование", callback_data="join_candidate")],
        ]
    )


async def send_main_menu(message: Message) -> None:
    await message.answer(
        "Выбери, что хочешь сделать:",
        reply_markup=main_menu_keyboard(),
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd "/Users/myxabzbzzzz/РАБОТА/моковая" && python -m pytest tests/test_menu.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
cd "/Users/myxabzbzzzz/РАБОТА/моковая"
git add bot/handlers/__init__.py bot/handlers/menu.py tests/test_menu.py
git commit -m "feat: add main menu keyboard"
```

---

### Task 7: Registration handlers (`/start`, name, contact)

**Files:**
- Create: `bot/handlers/start.py`
- Test: `tests/test_start_handler.py`

**Interfaces:**
- Consumes: `bot.states.Registration` (Task 5), `bot.handlers.menu.send_main_menu` (Task 6), `db.models.User` (Task 2), the `session` fixture (Task 2).
- Produces: `bot.handlers.start.router` (aiogram `Router`) with three handlers — `cmd_start`, `process_name`, `process_contact`. `bot/main.py` (Task 9) includes this router.

- [ ] **Step 1: Write the failing tests**

`tests/test_start_handler.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd "/Users/myxabzbzzzz/РАБОТА/моковая" && python -m pytest tests/test_start_handler.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'bot.handlers.start'`.

- [ ] **Step 3: Implement `bot/handlers/start.py`**

```python
from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.handlers.menu import send_main_menu
from bot.states import Registration
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

    await state.update_data(name=name[:255])
    await state.set_state(Registration.waiting_for_contact)
    await message.answer("Как с тобой можно связаться? Напиши Telegram-юзернейм или номер телефона")


@router.message(Registration.waiting_for_contact)
async def process_contact(message: Message, state: FSMContext, session: AsyncSession) -> None:
    contact = (message.text or "").strip()
    if not contact:
        await message.answer("Напиши, пожалуйста, юзернейм или номер телефона текстом.")
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd "/Users/myxabzbzzzz/РАБОТА/моковая" && python -m pytest tests/test_start_handler.py -v`
Expected: PASS (5 passed)

- [ ] **Step 5: Commit**

```bash
cd "/Users/myxabzbzzzz/РАБОТА/моковая"
git add bot/handlers/start.py tests/test_start_handler.py
git commit -m "feat: add registration flow (name + contact)"
```

---

### Task 8: Queue handlers (join / cancel / match notification)

**Files:**
- Create: `bot/handlers/queue.py`
- Test: `tests/test_queue_handler.py`

**Interfaces:**
- Consumes: `services.matching.{join_queue, cancel_queue, AlreadyInQueueError, NotInQueueError}` (Task 4), `db.models.{QueueRole, Match, User}` (Task 2), `bot.handlers.menu.send_main_menu` (Task 6).
- Produces: `bot.handlers.queue.router` (aiogram `Router`) with `join_interviewer`, `join_candidate`, `cancel_search` callback handlers. `bot/main.py` (Task 9) includes this router.

- [ ] **Step 1: Write the failing tests**

`tests/test_queue_handler.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd "/Users/myxabzbzzzz/РАБОТА/моковая" && python -m pytest tests/test_queue_handler.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'bot.handlers.queue'`.

- [ ] **Step 3: Implement `bot/handlers/queue.py`**

```python
from aiogram import Bot, F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.handlers.menu import send_main_menu
from db.models import Match, QueueRole, User
from services.matching import AlreadyInQueueError, NotInQueueError, cancel_queue, join_queue

router = Router()

CANCEL_KEYBOARD = InlineKeyboardMarkup(
    inline_keyboard=[[InlineKeyboardButton(text="❌ Отменить поиск", callback_data="cancel_search")]]
)

ROLE_LABELS = {
    QueueRole.interviewer: "интервьюером",
    QueueRole.candidate: "кандидатом",
}


async def _current_user(session: AsyncSession, telegram_id: int) -> User:
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    return result.scalar_one()


async def _notify_match(bot: Bot, session: AsyncSession, match: Match) -> None:
    interviewer = await session.get(User, match.interviewer_id)
    candidate = await session.get(User, match.candidate_id)

    await bot.send_message(
        interviewer.telegram_id,
        "Найден партнёр! Ты — интервьюер.\n"
        f"Кандидат: {candidate.name}\nКонтакт: {candidate.contact}\n\n"
        "Договоритесь о времени сами.",
    )
    await bot.send_message(
        candidate.telegram_id,
        "Найден партнёр! Ты — кандидат.\n"
        f"Интервьюер: {interviewer.name}\nКонтакт: {interviewer.contact}\n\n"
        "Договоритесь о времени сами.",
    )


async def _join(callback: CallbackQuery, session: AsyncSession, bot: Bot, role: QueueRole) -> None:
    user = await _current_user(session, callback.from_user.id)

    try:
        result = await join_queue(session, user.id, role)
    except AlreadyInQueueError:
        await callback.answer(
            "Ты уже в очереди, отмени поиск, если хочешь передумать", show_alert=True
        )
        return

    await callback.answer()

    if isinstance(result, Match):
        await _notify_match(bot, session, result)
        return

    await callback.message.answer(
        f"Ищем партнёра ({ROLE_LABELS[role]})... Можно отменить поиск.",
        reply_markup=CANCEL_KEYBOARD,
    )


@router.callback_query(F.data == "join_interviewer")
async def join_interviewer(callback: CallbackQuery, session: AsyncSession, bot: Bot) -> None:
    await _join(callback, session, bot, QueueRole.interviewer)


@router.callback_query(F.data == "join_candidate")
async def join_candidate(callback: CallbackQuery, session: AsyncSession, bot: Bot) -> None:
    await _join(callback, session, bot, QueueRole.candidate)


@router.callback_query(F.data == "cancel_search")
async def cancel_search(callback: CallbackQuery, session: AsyncSession) -> None:
    user = await _current_user(session, callback.from_user.id)

    try:
        await cancel_queue(session, user.id)
    except NotInQueueError:
        await callback.answer("Ты не в очереди", show_alert=True)
        return

    await callback.answer()
    await callback.message.answer("Поиск отменён.")
    await send_main_menu(callback.message)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd "/Users/myxabzbzzzz/РАБОТА/моковая" && python -m pytest tests/test_queue_handler.py -v`
Expected: PASS (5 passed)

- [ ] **Step 5: Commit**

```bash
cd "/Users/myxabzbzzzz/РАБОТА/моковая"
git add bot/handlers/queue.py tests/test_queue_handler.py
git commit -m "feat: add queue join/cancel handlers with match notification"
```

---

### Task 9: Bot wiring (`main.py`) + run instructions

**Files:**
- Create: `bot/main.py`
- Test: `tests/test_main.py`
- Create: `README.md`

**Interfaces:**
- Consumes: `bot.middlewares.db.DbSessionMiddleware` (Task 5), `bot.handlers.start.router`, `bot.handlers.queue.router` (Tasks 7–8), `config.settings.settings` (Task 1).
- Produces: `bot.main.build_dispatcher() -> Dispatcher` (used by tests and by `main()`), `bot.main.main()` — the polling entrypoint run via `python -m bot.main`.

- [ ] **Step 1: Write the failing test**

`tests/test_main.py`:

```python
from bot.handlers import queue, start
from bot.main import build_dispatcher


def test_build_dispatcher_includes_expected_routers():
    dp = build_dispatcher()

    assert start.router in dp.sub_routers
    assert queue.router in dp.sub_routers
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd "/Users/myxabzbzzzz/РАБОТА/моковая" && python -m pytest tests/test_main.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'bot.main'`.

- [ ] **Step 3: Implement `bot/main.py`**

```python
import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand

from bot.handlers import queue, start
from bot.middlewares.db import DbSessionMiddleware
from config.settings import settings


def build_dispatcher() -> Dispatcher:
    dp = Dispatcher()
    dp.update.middleware(DbSessionMiddleware())
    dp.include_router(start.router)
    dp.include_router(queue.router)
    return dp


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stdout,
    )

    bot = Bot(token=settings.bot_token)
    dp = build_dispatcher()

    await bot.set_my_commands([
        BotCommand(command="start", description="Начать / главное меню"),
    ])

    logging.info("Starting bot...")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd "/Users/myxabzbzzzz/РАБОТА/моковая" && python -m pytest tests/test_main.py -v`
Expected: PASS (1 passed)

- [ ] **Step 5: Run the full test suite**

Run: `cd "/Users/myxabzbzzzz/РАБОТА/моковая" && python -m pytest -v`
Expected: all tests across every task pass (28 passed).

- [ ] **Step 6: Write `README.md`**

```markdown
# Моковая

Telegram-бот для парных алгоритмических мок-собеседований: один участник заходит как интервьюер, другой — как кандидат, бот мэтчит их и передаёт контакты. Само собеседование проходит вне бота.

## Запуск

1. Установи зависимости:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. Скопируй `.env.example` в `.env` и заполни `BOT_TOKEN` (получить у @BotFather) и `DATABASE_URL` (локальный Postgres).
3. Создай базу и накати миграции:
   ```bash
   createdb mokovaya
   python -m alembic upgrade head
   ```
4. Запусти бота:
   ```bash
   python -m bot.main
   ```

## Тесты

Тесты используют in-memory SQLite и не требуют запущенного Postgres:

```bash
python -m pytest -v
```
```

- [ ] **Step 7: Commit**

```bash
cd "/Users/myxabzbzzzz/РАБОТА/моковая"
git add bot/main.py tests/test_main.py README.md
git commit -m "feat: wire dispatcher, add entrypoint and README"
```

---

## Self-Review Notes

- **Spec coverage:** §2 (онбординг-текст) → Task 7 `WELCOME_TEXT`; §3 (регистрация: имя + контакт) → Task 7; §4 (очередь/мэтчинг, FIFO, отмена, граничные случаи) → Tasks 4 and 8; §5 (стек и данные) → Tasks 1–3; §6 (вне рамок MVP) → respected throughout, nothing in this plan builds scheduling, in-bot interview execution, ratings, or level/language filtering.
- **Type consistency checked:** `join_queue` returns `QueueEntry | Match` consistently referenced in Tasks 4 and 8; `QueueRole`/`QueueStatus` enum members used identically across `db/models.py`, `services/matching.py`, `bot/handlers/queue.py`, and their tests.
- **No placeholders:** every step has complete, runnable code; no "TBD" or "similar to Task N" shortcuts.
