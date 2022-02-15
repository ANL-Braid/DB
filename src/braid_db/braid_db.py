# BRAID DB

import datetime
import logging
from enum import Enum, unique
from pathlib import Path
from typing import Dict, Iterable, List, Optional, TypeVar

from sqlalchemy.exc import ArgumentError
from sqlmodel import Session, SQLModel, create_engine, select
from sqlmodel.sql.expression import Select

from .models import (
    BraidDependencyModel,
    BraidModelBase,
    BraidRecordModel,
    BraidTagsModel,
    BraidUrisModel,
)

SCHEMA_FILE_NAME = "braid-db.sql"
DEFAULT_SCHEMA_FILE_PATH = Path(__file__).parent / SCHEMA_FILE_NAME

SQLITE_URL_PREFIX = "sqlite:///"


def digits(c):
    """Return c random digits (for random names)"""
    import random

    n = random.randint(0, 10 ** c)
    s = "%0*i" % (c, n)
    return s


@unique
class BraidTagType(Enum):
    # Cf braid-db.sql
    NONE = 0
    STRING = 1
    INTEGER = 2
    FLOAT = 3


BraidModelTypeVar = TypeVar("BraidModelTypeVar", bound=BraidModelBase)


class BraidTagValue:
    def __init__(self, value, type_):
        self.value = value
        self.type_ = type_


class BraidDB:
    def __init__(
        self, db_url: str, log=False, debug=False, mpi=False, echo_sql=False
    ):
        self.db_url = db_url
        self.logger = logging.getLogger("BraidDB")
        level = logging.WARN
        if log:
            level = logging.INFO
        if debug:
            level = logging.DEBUG
        self.logger.setLevel(level)
        self.mpi = mpi

        if not self.mpi:
            self.sql = self  # Backward compatible with clients that access the
            # sql property directly. To be deprecated.
        else:
            from db_tools_mpi import BraidSQL_MPI

            self.sql = BraidSQL_MPI(db_url, log, debug)
        self.engine = self.create_engine(db_url, echo_sql=echo_sql)

    def create_engine(self, db_url: str, echo_sql=False):
        try:
            return create_engine(db_url, echo=echo_sql)
        except ArgumentError:
            return create_engine(SQLITE_URL_PREFIX + db_url, echo=echo_sql)

    def create(self):
        """Set up the tables defined in the SQL file"""
        if self.mpi and self.sql.rank != 0:
            return
        SQLModel.metadata.create_all(self.engine)

    def run_query(self, stmt: Select, session: Optional[Session] = None):
        if session is not None:
            return session.exec(stmt)
        else:
            with Session(self.engine) as session:
                return session.exec(stmt)

    def query_all(self, stmt: Select, session: Optional[Session] = None):
        return self.run_query(stmt, session=session)

    def query_one_or_none(
        self, stmt: Select, session: Optional[Session] = None
    ):
        return self.run_query(stmt, session=session).one_or_none()

    def get_record_model_by_id(
        self, record_id: int, session: Optional[Session] = None
    ) -> Optional[BraidRecordModel]:
        return self.query_one_or_none(
            select(BraidRecordModel).where(
                BraidRecordModel.record_id == record_id
            ),
            session=session,
        )

    def insert(self, record):
        pass

    def add_model(
        self,
        model: BraidModelBase,
        session: Optional[Session] = None,
    ) -> BraidModelBase:
        self.trace(f"Adding model {model} to session {str(session)}")
        if session is not None:
            session.add(model)
            return model
        else:
            with Session(self.engine, expire_on_commit=False) as session:
                session.add(model)
                session.commit()
                return model

    def print(self, session: Optional[Session] = None):
        with Session(self.engine) as session:
            records = session.exec(select(BraidRecordModel))
            for record in records:
                record_id = record.record_id
                # text = "%5s : %-16s %s" % ("[%i]" % record_id, name, time)
                text = (
                    f"[{record.record_id:5}] : {record.name:16} {record.time}"
                )
                deps = self.get_dependencies(record_id, session=session)
                text = text + " <- " + str([d.record_id for d in deps])
                uris = self.get_uris(record_id, session=session)
                if uris is not None:
                    for uri in uris:
                        text += "\n\t\t\t URI: "
                        text += uri
                tags = self.get_tags(record_id, session=session)
                for key, tag in tags.items():
                    text += "\n\t\t\t TAG: "
                    quote = (
                        "'" if tags[key].type_ is BraidTagType.STRING else ""
                    )
                    text += f"{key} = {quote}{tags[key].value}{quote}"

                print(text)

    def extract_tags(self, records):
        """Append tags data to records"""
        tags = {}  # In case there are no records
        for record_id in list(records.keys()):
            tags = self.get_tags(record_id)
            text = records[record_id]
        for key in tags.keys():
            text += "\n\t\t\t TAG: "
            if (
                tags[key].type_ == BraidTagType.INTEGER
                or tags[key].type_ == BraidTagType.FLOAT
            ):
                text += "%s = %s" % (key, tags[key].value)
            else:
                text += "%s = '%s'" % (key, tags[key].value)
            records[record_id] = text

    def get_dependencies(
        self, record_id, session: Optional[Session] = None
    ) -> Iterable[BraidRecordModel]:
        """
        Return list of dependent records of a record based on its id
        """
        self.trace(f"DB.get_dependencies({record_id}) ...")
        dependencies = self.query_all(
            select(BraidDependencyModel).where(
                BraidDependencyModel.record_id == record_id
            ),
            session=session,
        )

        dep_recs: List[BraidRecordModel] = []

        for dep in dependencies:
            dependency_id = dep.dependency
            dep_rec = self.query_one_or_none(
                select(BraidRecordModel).where(
                    BraidRecordModel.record_id == dependency_id
                ),
                session=session,
            )
            dep_recs.append(dep_rec)

        return dep_recs

    def get_uris(
        self, record_id: int, session: Optional[Session] = None
    ) -> List[str]:
        """
        return list of string URIs
        """
        self.trace(f"DB.get_uris({record_id}) ...")
        rec = self.get_record_model_by_id(record_id, session=session)
        uris = []
        if rec is not None:
            uris = [u.uri for u in rec.uris]
        return uris

    def get_tags(
        self, record_id, session: Optional[Session] = None
    ) -> Dict[str, BraidTagValue]:
        """
        return dict of string->BraidTagValue key->value pairs
        """
        self.trace(f"DB.get_tags({record_id}) ...")
        if session is None:
            session = self.get_session()
        tag_models = session.execute(
            select(BraidTagsModel).where(BraidTagsModel.record_id == record_id)
        ).all()
        tags = {}
        for tag_model in tag_models:
            type_ = BraidTagType(tag_model.tag_type)
            value = BraidTagValue(tag_model.value, type_)
            tags[tag_model.key] = value
        return tags

    def debug(self, msg):
        self.logger.debug(msg)

    def trace(self, msg):
        self.logger.log(level=logging.DEBUG - 5, msg=msg)

    def size(self):
        """
        For performance measurements, etc.
        Just the sum of the table sizes
        """
        result = 0
        tables = ["records", "dependencies", "uris", "tags"]
        for table in tables:
            self.sql.select(table, "count(record_id)")
            row = self.sql.cursor.fetchone()
            assert row is not None
            count = int(row[0])
            print("count: %s = %i" % (table, count))
            result += count

        return result


serial = 1


def make_serial():
    global serial
    result = serial
    serial += 1
    return result


class BraidRecord:
    def __init__(
        self,
        db: Optional[BraidDB] = None,
        name=None,
        timestamp=None,
        debug=True,
    ):
        self.db = db
        self.dependencies = []
        self.uris = []
        # Dict of string->BraidTagValue
        self.tags = {}

        self.logger = logging.getLogger("BraidRecord")
        if debug:
            self.logger.setLevel(logging.DEBUG)

        if timestamp is None:
            self.timestamp = datetime.datetime.now()
        else:
            self.timestamp = timestamp
        self.model = BraidRecordModel(name=name, time=self.timestamp)

    @property
    def record_id(self) -> Optional[int]:
        if self.model.record_id is None:
            if self.db is not None:
                self.db.add_model(self.model)
        return self.model.record_id

    def add_dependency(self, record: "BraidRecord"):
        """record: a BraidRecord"""
        self.dependencies.append(record)
        dep_model = BraidDependencyModel(
            record_id=self.record_id, dependency=record.model.record_id
        )
        if self.db is not None:
            self.db.add_model(dep_model)

    def add_uri(self, uri: str):
        """uri: a string URI"""
        self.uris.append(uri)
        uri_model = BraidUrisModel(record_id=self.record_id, uri=uri)
        if self.db is not None:
            self.db.add_model(uri_model)

    def add_tag(self, key, value, type_=BraidTagType.STRING):
        """key:   a string key name
        value: a string value
        """
        if not isinstance(type_, BraidTagType):
            raise Exception(
                "type must be a BraidTagType! "
                + "received: '%s' type: %s" % (str(type_), type(type_))
            )
        self.tags[key] = value
        tag_model = BraidTagsModel(
            record_id=self.record_id,
            key=key,
            value=value,
            tag_type=type_.value,
        )
        if self.db is not None:
            self.db.add_model(tag_model)

    def strftime(self):
        return self.timestamp.strftime("%Y-%m-%d %H:%M:%S")

    def __str__(self):
        if self.name is None:
            return f"BraidRecord {self.uri}"
        else:
            return f'BraidRecord("{self.name}")'

    def debug(self, msg):
        self.logger.debug(msg)


class BraidFact(BraidRecord):

    """Examples: pre-existing data, software, etc."""

    def __init__(self, db=None, name=None):
        super().__init__(db=db, name=name)

    def add_dependency(self, record):
        """record: a BraidRecord"""
        raise Exception("BraidFacts do not have dependencies!")

    def store(self):
        self.db.add_model(self.model)
        self.debug(f"stored Fact: {self.model.record_id}")
        return self.model.record_id


class BraidData(BraidRecord):

    """Examples: data in the system with dependencies:
    Simulation outputs, data analyses, experiment outputs
    """

    def __init__(self, db=None, name=None):
        super().__init__(db=db, name=name)

    def store(self):
        self.db.add_model(self.model)
        self.debug(f"stored Data: {self.model.record_id}")
        return self.model.record_id


class BraidModel(BraidRecord):

    """Examples: an ML model that is trained on BraidRecords"""

    def __init__(self, db=None, name=None):
        super().__init__(db=db, name=name)

    def update(self, record):
        """record: a BraidRecord"""
        super().add_dependency(record)

    def store(self):
        self.db.add_model(self.model)
        self.debug(f"stored Model: {self.model.record_id}")
        return self.model.record_id


# class Braid
