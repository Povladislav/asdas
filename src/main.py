from fastapi import FastAPI, HTTPException, BackgroundTasks
import random
import asyncio
from sqlalchemy import Column, Integer, String, func
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.future import select
from pydantic import BaseModel
from src.config import Settings

app = FastAPI()
settings = Settings()

DATABASE_URL = f"postgresql+asyncpg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOST}:{settings.DB_PORT}/{settings.POSTGRES_DB}"

Base = declarative_base()


class TaskDB(Base):
    __tablename__ = "tasks"

    task_number = Column(Integer, primary_key=True, index=True)
    task_title = Column(String, index=True)
    waiting_time = Column(Integer)
    status = Column(String, index=True)


engine = create_async_engine(DATABASE_URL, echo=True)
async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# Создание таблицы при старте приложения
@app.on_event("startup")
async def startup_event():
    await create_tables()


# Pydantic модель для задачи (task)
class Task(BaseModel):
    task_number: int
    task_title: str
    waiting_time: int
    status: str


# Endpoint to accept new tasks and put them in the queue
@app.post("/tasks/", status_code=200)
async def create_task(task: Task, background_tasks: BackgroundTasks):
    async with async_session_maker() as session:
        task_count = await session.execute(select(func.count(TaskDB.task_number)))
        task_number = task_count.scalar()
        task_number = task_number + 1 if task_number else 1

        task_db = TaskDB(
            task_number=task_number,
            task_title=task.task_title,
            waiting_time=task.waiting_time,
            status="waiting"
        )
        session.add(task_db)
        await session.commit()

    background_tasks.add_task(update_task_status, task_number=task_number, waiting_time=task.waiting_time)
    return {"task_number": task_number}


# Function to update task status after waiting time
async def update_task_status(task_number: int, waiting_time: int):
    await asyncio.sleep(waiting_time)
    async with async_session_maker() as session:
        task_db = await session.get(TaskDB, task_number)
        if task_db and task_db.status == "waiting":
            task_db.status = "done"
            await session.commit()


# Endpoint to get the status of a specific task by its task number
@app.get("/tasks/{task_number}/", status_code=200)
async def get_task_status(task_number: int):
    async with async_session_maker() as session:
        task_db = await session.get(TaskDB, task_number)
        if task_db:
            return Task(
                task_number=task_db.task_number,
                task_title=task_db.task_title,
                waiting_time=task_db.waiting_time,
                status=task_db.status
            )
        raise HTTPException(status_code=404, detail="Task not found")
