from datetime import datetime
from typing import Iterator
from sqlalchemy.ext.asyncio import AsyncSession, AsyncResult, AsyncScalarResult
from sqlmodel import SQLModel, Field, Relationship, select
from sqlmodel.engine.result import Result, ScalarResult
from sqlmodel.sql.expression import Select, SelectOfScalar
from sqlalchemy import util
from todo_app.status import Status
from sqlmodel.sql.base import Executable


from typing import Optional, Union, Any, Sequence, Mapping, TypeVar, overload


_TSelectParam = TypeVar("_TSelectParam")


class Session(AsyncSession):
    @overload
    async def exec(
        self,
        statement: Select[_TSelectParam],
        *,
        params: Optional[Union[Mapping[str, Any], Sequence[Mapping[str, Any]]]] = None,
        execution_options: Mapping[str, Any] = util.EMPTY_DICT,
        bind_arguments: Optional[Mapping[str, Any]] = None,
        _parent_execute_state: Optional[Any] = None,
        _add_event: Optional[Any] = None,
        **kw: Any,
    ) -> Result[_TSelectParam]:
        ...

    @overload
    async def exec(
        self,
        statement: SelectOfScalar[_TSelectParam],
        *,
        params: Optional[Union[Mapping[str, Any], Sequence[Mapping[str, Any]]]] = None,
        execution_options: Mapping[str, Any] = util.EMPTY_DICT,
        bind_arguments: Optional[Mapping[str, Any]] = None,
        _parent_execute_state: Optional[Any] = None,
        _add_event: Optional[Any] = None,
        **kw: Any,
    ) -> ScalarResult[_TSelectParam]:
        ...

    async def exec(
        self,
        statement: Union[
            Select[_TSelectParam],
            SelectOfScalar[_TSelectParam],
            Executable[_TSelectParam],
        ],
        *,
        params: Optional[Union[Mapping[str, Any], Sequence[Mapping[str, Any]]]] = None,
        execution_options: Mapping[str, Any] = util.EMPTY_DICT,
        bind_arguments: Optional[Mapping[str, Any]] = None,
        _parent_execute_state: Optional[Any] = None,
        _add_event: Optional[Any] = None,
        **kw: Any,
    ) -> Union[Result[_TSelectParam], ScalarResult[_TSelectParam]]:
        results = await super().execute(
            statement,
            params=params,
            execution_options=execution_options,
            bind_arguments=bind_arguments,
            _parent_execute_state=_parent_execute_state,
            _add_event=_add_event,
            **kw,
        )
        if isinstance(statement, SelectOfScalar):
            return results.scalars()  # type: ignore

        return results  # type: ignore


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
    tasks: list[Task] = Relationship()

    @property
    def completed_tasks(self) -> Iterator[Task]:
        return (task for task in self.tasks if task.status == Status.COMPLETED)

    @property
    def unfinished_tasks(self) -> Iterator[Task]:
        return (task for task in self.tasks if task.status == Status.NOT_COMPLETED)


class User(SQLModel, table=True):
    id: int = Field(primary_key=True)
    name: str
    joined: datetime = Field(default_factory=datetime.utcnow)
    last_login: datetime = Field(default_factory=datetime.utcnow)

    async def get_inbox(self, session: Session) -> Project:
        query = select(Project).where(Project.inbox, Project.owner_id == self.id)
        if project := await (await session.exec(query)).first():
            return project

        if self.projects:
            return (await self.get_projects(session))[0]

        raise ValueError(
            f"{self!r} doesn't have any projects. Could not find an inbox."
        )

    async def get_active_projects(self, session: Session) -> Iterator[Project]:
        query = select(Project).where(
            Project.owner_id == self.id, Project.archived == False
        )
        result = await session.exec(query)
        return result.all()

    async def get_archived_projects(self, session: Session) -> Iterator[Project]:
        query = select(Project).where(
            Project.owner_id == self.id, Project.archived == True
        )
        result = await session.exec(query)
        return result.all()

    async def get_projects(self, session: Session) -> list[Project]:
        query = select(Project).where(Project.owner_id == self.id)
        result = await session.exec(query)
        return result.all()
