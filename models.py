from sqlmodel import SQLModel, Field
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from typing import AsyncGenerator
from datetime import datetime
from sqlmodel import create_engine
from sqlmodel import Session


class Component(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    category: str = Field(index=True)
    file_path: str
    content: str
    description: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class DocSection(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    section: str = Field(index=True)
    file_path: str
    content: str
    description: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


# Async database setup
DATABASE_URL = "sqlite+aiosqlite:///reflex_docs.db"
async_engine = create_async_engine(DATABASE_URL, echo=True)

# Keep sync engine for data population
SYNC_DATABASE_URL = "sqlite:///reflex_docs.db"
sync_engine = create_engine(SYNC_DATABASE_URL, echo=True)


async def create_db_and_tables():
    async with async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


def create_db_and_tables_sync():
    SQLModel.metadata.create_all(sync_engine)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSession(async_engine) as session:
        yield session


# Keep sync session for data population


def get_sync_session():
    with Session(sync_engine) as session:
        yield session
