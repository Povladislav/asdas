from fastapi import FastAPI, HTTPException, BackgroundTasks
import asyncio
from pydantic import BaseModel
from src.config import Settings
from database import create_task, update_task, get_task_status

app = FastAPI()
settings = Settings()


class Task(BaseModel):
    task_title: str
    waiting_time: int


@app.post("/tasks/", status_code=200)
async def create_task_endpoint(task: Task, background_tasks: BackgroundTasks):
    task_number = await create_task(task.task_title, task.waiting_time)
    background_tasks.add_task(update_task_status, task_number=task_number, waiting_time=task.waiting_time)
    return {"task_number": task_number}


# Function to update task status after waiting time
async def update_task_status(task_number: int, waiting_time: int):
    await asyncio.sleep(waiting_time)
    await update_task(task_number)


@app.get("/tasks/{task_number}/", status_code=200)
async def get_task_status_endpoint(task_number: int):
    task = await get_task_status(task_number)
    if task:
        return task
    raise HTTPException(status_code=404, detail="Task not found")
