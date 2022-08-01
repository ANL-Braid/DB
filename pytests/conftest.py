import os

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from braid_db import BraidDB

sqlite_file_name = "pytests.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"
# sqlite_url = "sqlite://"
create_engine_kwargs = {
    "echo": True,
    "poolclass": StaticPool,
    "connect_args": {"check_same_thread": False},
}


@pytest.fixture
def db_engine():
    engine = create_engine(sqlite_url, **create_engine_kwargs)

    SQLModel.metadata.create_all(engine)
    yield engine


@pytest.fixture
def session(db_engine) -> Session:
    with Session(db_engine) as session:
        yield session


@pytest.fixture(scope="function")
def braid_db() -> BraidDB:
    db = BraidDB(
        sqlite_file_name,
        echo_sql=True,
        create_engine_kwargs=create_engine_kwargs,
    )
    db.create()
    yield db
    os.remove(sqlite_file_name)
