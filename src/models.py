from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from .database import Base, engine


class TaskDB(Base):
    __tablename__ = "tasks"

    task_number = Column(Integer, primary_key=True, index=True)
    task_title = Column(String, index=True)
    waiting_time = Column(Integer)
    status = Column(String, index=True)


async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)