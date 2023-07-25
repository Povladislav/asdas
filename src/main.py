from fastapi import FastAPI, HTTPException, BackgroundTasks
import random
import asyncio

from pydantic import BaseModel
from sqlalchemy.future import select

from src.database.database import async_session_maker
from src.models.tasks import TaskDB

app = FastAPI()


class Task(BaseModel):
    task_number: int
    task_title: str
    waiting_time: int
    status: str


async def process_tasks():
    while True:
        await asyncio.sleep(5)  # Adjust the polling interval as needed
        async with async_session_maker as session:
            tasks = await session.execute(
                select(TaskDB).where(TaskDB.status == 'waiting').where(TaskDB.waiting_time <= 0)
            )
            for task in tasks.scalars():
                task.status = "done"
            await session.commit()


# Start the background task processing
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(process_tasks())


# Endpoint to accept new tasks and put them in the queue
@app.post("/tasks/", status_code=200)
async def create_task(task: Task, background_tasks: BackgroundTasks):
    async with async_session_maker as session:
        task_number = await session.execute(select(TaskDB).count() + 1)
        task.task_number = task_number.scalar()

        task_db = TaskDB(
            task_number=task.task_number,
            task_title=task.task_title,
            waiting_time=task.waiting_time,
            status="waiting"
        )
        session.add(task_db)
        await session.commit()

    background_tasks.add_task(update_task_status, task.task_number, task.waiting_time)
    return {"task_number": task.task_number}


# Function to update task status after waiting time
async def update_task_status(task_number: int, waiting_time: int):
    await asyncio.sleep(waiting_time)
    async with async_session_maker as session:
        task_db = await session.get(TaskDB, task_number)
        if task_db and task_db.status == "waiting":
            task_db.status = "done"
            await session.commit()


# Endpoint to get the status of a specific task by its task number
@app.get("/tasks/{task_number}/", status_code=200)
async def get_task_status(task_number: int):
    async with async_session_maker as session:
        task_db = await session.get(TaskDB, task_number)
        if task_db:
            return Task(
                task_number=task_db.task_number,
                task_title=task_db.task_title,
                waiting_time=task_db.waiting_time,
                status=task_db.status
            )
        raise HTTPException(status_code=404, detail="Task not found")
