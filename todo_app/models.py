from datetime import datetime
from typing import Iterator
from sqlmodel import SQLModel, Field, Relationship
from todo_app.status import Status


class Task(SQLModel, table=True):
    id: int = Field(primary_key=True)
    name: str
    description: str
    author_id: int = Field(foreign_key="user.id")
    project_id: int = Field(foreign_key="project.id")
    status: str = Field(default=Status.NOT_COMPLETED)
    created: datetime = Field(default_factory=datetime.utcnow)
    completed: datetime = Field(default_factory=datetime.utcnow)

    author: "User" = Relationship()
    project: "Project" = Relationship()


class Project(SQLModel, table=True):
    id: int = Field(primary_key=True)
    name: str
    description: str
    owner_id: int = Field(foreign_key="user.id")
    archived: bool = Field(default=False)

    owner: "User" = Relationship()
    tasks: list[Task] = Relationship()

    @property
    def completed_tasks(self) -> Iterator["Task"]:
        return (task for task in self.tasks if task.status == Status.COMPLETED)

    @property
    def unfinished_tasks(self) -> Iterator["Task"]:
        return (task for task in self.tasks if task.status == Status.NOT_COMPLETED)


class User(SQLModel, table=True):
    id: int = Field(primary_key=True)
    name: str
    joined: datetime = Field(default_factory=datetime.utcnow)
    last_login: datetime = Field(default_factory=datetime.utcnow)

    projects: list[Project] = Relationship()

    @property
    def archived_projects(self) -> Iterator[Project]:
        return (proj for proj in self.projects if proj.archived)

    @property
    def active_projects(self) -> Iterator[Project]:
        return (proj for proj in self.projects if not proj.archived)
