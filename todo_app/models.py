from datetime import datetime
from typing import Iterator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import SQLModel, Field, Relationship, select
from todo_app.status import Status


class Task(SQLModel, table=True):
    id: int = Field(primary_key=True)
    name: str
    description: str
    author_id: int = Field(foreign_key="user.id")
    project_id: int = Field(foreign_key="project.id")
    status: str = Status.NOT_COMPLETED
    created: datetime = Field(default_factory=datetime.utcnow)
    completed: datetime = Field(default_factory=datetime.utcnow)

    author: "User" = Relationship()
    project: "Project" = Relationship()


class Project(SQLModel, table=True):
    id: int = Field(primary_key=True)
    name: str
    description: str
    owner_id: int = Field(foreign_key="user.id")
    archived: bool = False
    inbox: bool = False

    owner: "User" = Relationship()

    async def get_tasks(self, session: AsyncSession) -> list[Task]:
        query = select(Task).where(Task.project_id == self.id)
        result = await session.execute(query)
        return result.scalars().all()

    async def get_completed_tasks(self, session: AsyncSession) -> list[Task]:
        query = select(Task).where(
            Task.project_id == self.id, Task.status == Status.COMPLETED
        )
        result = await session.exec(query)
        return result.all()

    async def get_unfinished_tasks(self, session: AsyncSession) -> list[Task]:
        query = select(Task).where(
            Task.project_id == self.id, Task.status == Status.NOT_COMPLETED
        )
        result = await session.exec(query)
        return result.all()


class User(SQLModel, table=True):
    id: int = Field(primary_key=True)
    name: str
    joined: datetime = Field(default_factory=datetime.utcnow)
    last_login: datetime = Field(default_factory=datetime.utcnow)

    projects: Project = Relationship()

    async def get_inbox(self, session: AsyncSession) -> Project:
        query = select(Project).where(Project.inbox, Project.owner_id == self.id)
        if project := (await session.execute(query)).scalars().first():
            return project

        if projects := await self.get_projects(session):
            return projects[0]

        raise ValueError(
            f"{self!r} doesn't have any projects. Could not find an inbox."
        )

    async def get_active_projects(self, session: AsyncSession) -> Iterator[Project]:
        query = select(Project).where(
            Project.owner_id == self.id, Project.archived == False
        )
        result = await session.exec(query)
        return result.scalars().all()

    async def get_archived_projects(self, session: AsyncSession) -> Iterator[Project]:
        query = select(Project).where(
            Project.owner_id == self.id, Project.archived == True
        )
        result = await session.exec(query)
        return result.all()

    async def get_projects(self, session: AsyncSession) -> list[Project]:
        query = select(Project).where(Project.owner_id == self.id)
        result = await session.execute(query)
        return result.scalars().all()
