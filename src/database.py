import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select
from .models import TaskDB
from src.config import Settings

settings = Settings()
DATABASE_URL = f"postgresql+asyncpg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOST}:{settings.DB_PORT}/{settings.POSTGRES_DB}"
engine = create_async_engine(DATABASE_URL, echo=True)
async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def create_task(task_title: str, waiting_time: int) -> int:
    async with async_session_maker() as session:
        task_count = await session.execute(select(func.count(TaskDB.task_number)))
        task_number = await task_count.scalar()
        task_number = task_number + 1 if task_number else 1

        task_db = TaskDB(
            task_number=task_number,
            task_title=task_title,
            waiting_time=waiting_time,
            status="waiting"
        )
        session.add(task_db)
        await session.commit()

    return task_number


async def update_task(task_number: int):
    async with async_session_maker() as session:
        task_db = await session.get(TaskDB, task_number)
        if task_db and task_db.status == "waiting":
            task_db.status = "done"
            await session.commit()


async def get_task_status(task_number: int):
    async with async_session_maker() as session:
        task_db = await session.get(TaskDB, task_number)
        if task_db:
            return {
                "task_number": task_db.task_number,
                "task_title": task_db.task_title,
                "waiting_time": task_db.waiting_time,
                "status": task_db.status
            }
        return None
