from pytest import fixture
from sqlmodel import create_engine, Session, SQLModel, select
import todo_app.models as models


@fixture(scope="module")
def db():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    return engine


def add_user(session, *, name, **kwargs):
    session.add(models.User(name=name, **kwargs))
    return get_user(session, name)


def get_user(session, name) -> models.User:
    return session.exec(select(models.User).where(models.User.name == name)).first()


def add_project(session, *, name, **kwargs):
    session.add(models.Project(name=name, **kwargs))
    return get_project(session, name)


def get_project(session, name):
    statement = select(models.Project).where(models.Project.name == name)
    return session.exec(statement).first()


def add_task(session, *, name, **kwargs):
    session.add(models.Task(name=name, **kwargs))
    return get_task(session, name)


def get_task(session, name):
    statement = select(models.Task).where(models.Project.name == name)
    return session.exec(statement).first()


def test_user_projects(db):
    with Session(db) as session:
        user = add_user(session, name="Bob")
        session.add(
            models.Project(name="Test", description="Test project", owner_id=user.id)
        )

        assert len(user.projects) == 1
        session.rollback()


def test_user_inbox_project(db):
    with Session(db) as session:
        user = add_user(session, name="Bob")
        project = add_project(
            session,
            name="Inbox",
            description="Bob's inbox",
            owner_id=user.id,
            inbox=True,
        )

        assert user.get_inbox().id == project.id
        session.rollback()


def test_user_no_inbox_project(db):
    with Session(db) as session:
        user = add_user(session, name="Bob")
        project = add_project(
            session,
            name="Inbox",
            description="Bob's inbox",
            owner_id=user.id,
        )

        assert user.get_inbox().id == project.id
        session.rollback()


def test_project_owner(db):
    with Session(db) as session:
        user = add_user(session, name="Bob")
        project = add_project(
            session, name="Test", description="Test project", owner_id=user.id
        )

        assert project.owner.id is not None
        assert project.owner.id == user.id
        session.rollback()


def test_project_tasks(db):
    with Session(db) as session:
        user = add_user(session, name="Bob")
        project = add_project(
            session, name="Test", description="Test project", owner_id=user.id
        )
        add_task(
            session,
            name="Test",
            description="Test task",
            author_id=user.id,
            project_id=project.id,
        )

        assert len(project.tasks) == 1
        session.rollback()


def test_task_author(db):
    with Session(db) as session:
        user = add_user(session, name="Bob")
        project = add_project(
            session, name="Test", description="Test project", owner_id=user.id
        )
        task = add_task(
            session,
            name="Test",
            description="Test task",
            author_id=user.id,
            project_id=project.id,
        )

        assert task.author.id is not None
        assert task.author.id == user.id
        session.rollback()


def test_task_project(db):
    with Session(db) as session:
        user = add_user(session, name="Bob")
        project = add_project(
            session, name="Test", description="Test project", owner_id=user.id
        )
        task = add_task(
            session,
            name="Test",
            description="Test task",
            author_id=user.id,
            project_id=project.id,
        )

        assert task.project.id is not None
        assert task.project.id == project.id
        session.rollback()
