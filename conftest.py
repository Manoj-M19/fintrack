"""
Global pytest fixtures shared across unit and integration tests.

Key decisions:
- Uses an in-memory SQLite (via aiosqlite) for fast unit tests
- For integration tests, DATABASE_URL env var should point to a real Postgres test DB
- Every test gets a fresh DB session — no state leaks between tests
"""
import asyncio
from collections.abc import AsyncGenerator
from typing import Any

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.security import create_access_token, hash_password

# ── Event loop (single loop for the entire test session) ─────────────────────
@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ── In-memory SQLite engine (fast, no external deps) ─────────────────────────
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="session")
async def engine():
    eng = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await eng.dispose()


@pytest_asyncio.fixture
async def db_session(engine) -> AsyncGenerator[AsyncSession, None]:
    """Yields a session that is rolled back after each test — zero cleanup needed."""
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        yield session
        await session.rollback()


# ── FastAPI test client ───────────────────────────────────────────────────────
@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    AsyncClient wired to the FastAPI app with the test DB session injected.
    Overrides the real get_db dependency so no real Postgres is needed.
    """
    from app.main import create_app

    app: FastAPI = create_app()

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


# ── Auth helpers ──────────────────────────────────────────────────────────────
@pytest.fixture
def auth_headers() -> dict[str, str]:
    """Returns Authorization headers for a fake user_id=1 (use in unit tests)."""
    token = create_access_token(subject=1)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def make_auth_headers():
    """Factory: generate auth headers for any user_id."""
    def _make(user_id: int) -> dict[str, str]:
        token = create_access_token(subject=user_id)
        return {"Authorization": f"Bearer {token}"}
    return _make