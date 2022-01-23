from pytest import raises, mark
from pytest_asyncio import fixture as async_fixture
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel
from typing import Type, TypeVar
import todo_app.models as models


T = TypeVar("T")


@async_fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(SQLModel.metadata.create_all)

        async with async_session() as s:
            yield s

        await connection.close()

    await engine.dispose()


async def _add_model(session, model: Type[T], **kwargs) -> T:
    session.add(obj := model(**kwargs))
    await session.commit()
    await session.refresh(obj)
    return obj


async def add_user(session, **kwargs) -> models.User:
    return await _add_model(session, models.User, **kwargs)


async def add_project(session, **kwargs) -> models.Project:
    return await _add_model(session, models.Project, **kwargs)


async def add_task(session, **kwargs) -> models.Task:
    return await _add_model(session, models.Task, **kwargs)


@mark.asyncio
async def test_user_projects(session):
    user = await add_user(session, name="Bob")
    await add_project(
        session, name="Test", description="Test project", owner_id=user.id
    )

    projects = await user.get_projects(session)
    assert len(projects) == 1
    print(projects)
    assert isinstance(projects[0], models.Project)


@mark.asyncio
async def test_user_multiple_projects(session):
    user = await add_user(session, name="Bob")
    await add_project(
        session, name="Test", description="Test project", owner_id=user.id
    )
    await add_project(
        session, name="Test 2", description="Test project 2", owner_id=user.id
    )

    projects = await user.get_projects(session)
    assert len(projects) == 2
    assert isinstance(projects[0], models.Project)
    assert isinstance(projects[1], models.Project)
    assert projects[0].name == "Test"
    assert projects[1].name == "Test 2"


@mark.asyncio
async def test_user_inbox_project(session):
    user = await add_user(session, name="Bob")
    project = await add_project(
        session,
        name="Inbox",
        description="Bob's inbox",
        owner_id=user.id,
        inbox=True,
    )

    assert (await user.get_inbox(session)).id == project.id


@mark.asyncio
async def test_user_no_inbox_project(session):
    user = await add_user(session, name="Bob")
    project = await add_project(
        session,
        name="Inbox",
        description="Bob's inbox",
        owner_id=user.id,
    )

    assert (await user.get_inbox(session)).id == project.id


@mark.asyncio
async def test_user_inbox_no_projects(session):
    user = await add_user(session, name="Bob")

    with raises(ValueError):
        await user.get_inbox(session)


@mark.asyncio
async def test_project_owner(session):
    user = await add_user(session, name="Bob")
    project = await add_project(
        session, name="Test", description="Test project", owner_id=user.id
    )

    assert project.owner.id is not None
    assert project.owner.id == user.id


@mark.asyncio
async def test_project_tasks(db):
    async with AsyncSession(db) as session:
        user = await add_user(session, name="Bob")
        project = await add_project(
            session, name="Test", description="Test project", owner_id=user.id
        )
        await add_task(
            session,
            name="Test",
            description="Test task",
            author_id=user.id,
            project_id=project.id,
        )

        assert len(project.tasks) == 1


@mark.asyncio
async def test_task_author(db):
    async with AsyncSession(db) as session:
        user = await add_user(session, name="Bob")
        project = await add_project(
            session, name="Test", description="Test project", owner_id=user.id
        )
        task = await add_task(
            session,
            name="Test",
            description="Test task",
            author_id=user.id,
            project_id=project.id,
        )

        assert task.author.id is not None
        assert task.author.id == user.id


@mark.asyncio
async def test_task_project(db):
    async with AsyncSession(db) as session:
        user = await add_user(session, name="Bob")
        project = await add_project(
            session, name="Test", description="Test project", owner_id=user.id
        )
        task = await add_task(
            session,
            name="Test",
            description="Test task",
            author_id=user.id,
            project_id=project.id,
        )

        task_project_id = int(task.projects.id)
        project_id = int(project.id)

        assert task_project_id is not None
        assert task_project_id == project_nid
