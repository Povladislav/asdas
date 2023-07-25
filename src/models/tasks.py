from sqlalchemy import Column, Integer, String

from src.database.database import Base, engine


class TaskDB(Base):
    __tablename__ = "tasks"

    task_number = Column(Integer, primary_key=True, index=True)
    task_title = Column(String, index=True)
    waiting_time = Column(Integer)
    status = Column(String, index=True)



