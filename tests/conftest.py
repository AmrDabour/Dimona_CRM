import asyncio
import pytest
import pytest_asyncio
from typing import AsyncGenerator, Generator
from uuid import uuid4
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy import text

from app.main import app as fastapi_app
from app.database import Base, get_db
from app.config import settings
from app.core.security import get_password_hash, create_access_token
from app.models.user import User
from app.models.team import Team
from app.core.permissions import UserRole

# Force all models to register with Base.metadata
import app.models  # noqa

TEST_DATABASE_URL = settings.database_url.replace("dimora_crm", "dimora_crm_test")

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    poolclass=NullPool,
)

TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Each test gets a completely fresh database.
    DROP SCHEMA CASCADE handles circular FKs cleanly.
    create_all rebuilds everything from scratch.
    """
    async with test_engine.begin() as conn:
        await conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        await conn.execute(text("CREATE SCHEMA public"))
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionLocal() as session:
        yield session
    # No teardown needed -- next test will drop everything


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db():
        yield db_session

    fastapi_app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=fastapi_app),
        base_url="http://test",
    ) as ac:
        yield ac

    fastapi_app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_team(db_session: AsyncSession) -> Team:
    team = Team(
        id=uuid4(),
        name="Test Team",
    )
    db_session.add(team)
    await db_session.commit()
    await db_session.refresh(team)
    return team


@pytest_asyncio.fixture
async def test_admin(db_session: AsyncSession) -> User:
    user = User(
        id=uuid4(),
        email="admin@test.com",
        full_name="Test Admin",
        hashed_password=get_password_hash("password123"),
        role=UserRole.ADMIN,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_manager(db_session: AsyncSession, test_team: Team) -> User:
    user = User(
        id=uuid4(),
        email="manager@test.com",
        full_name="Test Manager",
        hashed_password=get_password_hash("password123"),
        role=UserRole.MANAGER,
        team_id=test_team.id,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_agent(db_session: AsyncSession, test_team: Team) -> User:
    user = User(
        id=uuid4(),
        email="agent@test.com",
        full_name="Test Agent",
        hashed_password=get_password_hash("password123"),
        role=UserRole.AGENT,
        team_id=test_team.id,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
def admin_token(test_admin: User) -> str:
    return create_access_token({"sub": str(test_admin.id), "role": test_admin.role.value})


@pytest.fixture
def manager_token(test_manager: User) -> str:
    return create_access_token({"sub": str(test_manager.id), "role": test_manager.role.value})


@pytest.fixture
def agent_token(test_agent: User) -> str:
    return create_access_token({"sub": str(test_agent.id), "role": test_agent.role.value})


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}
