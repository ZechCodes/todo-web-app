from pytest import fixture, raises
from sqlmodel import create_engine, Session, SQLModel, select
import todo_app.models as models


@fixture
def db():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    return engine


def _add_model(session, model, **kwargs):
    session.add(obj := model(**kwargs))
    session.commit()
    session.refresh(obj)
    return obj


def add_user(session, **kwargs):
    return _add_model(session, models.User, **kwargs)


def add_project(session, **kwargs):
    return _add_model(session, models.Project, **kwargs)


def add_task(session, **kwargs):
    return _add_model(session, models.Task, **kwargs)


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

        assert user.inbox.id == project.id
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

        assert user.inbox.id == project.id
        session.rollback()


def test_user_inbox_no_projects(db):
    with Session(db) as session:
        user = add_user(session, name="Bob")

        with raises(ValueError):
            user.inbox

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
