import os

import pytest
from sqlmodel import Session, SQLModel, create_engine

sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"


@pytest.fixture
def db_engine():
    engine = create_engine(sqlite_url, echo=True)

    SQLModel.metadata.create_all(engine)
    yield engine
    os.remove(sqlite_file_name)


@pytest.fixture
def session(db_engine) -> Session:
    with Session(db_engine) as session:
        yield session
