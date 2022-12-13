# BRAID DB

import datetime
import logging
import subprocess
from enum import Enum, unique
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional, TypeVar, Union
from uuid import UUID

from sqlalchemy.exc import ArgumentError
from sqlmodel import Session, SQLModel, create_engine, select
from sqlmodel.engine.result import ScalarResult
from sqlmodel.sql.expression import Select

from .gen_tools import substitute_vals
from .models import (
    BraidDerivationModel,
    BraidInvalidationAction,
    BraidInvalidationModel,
    BraidModelBase,
    BraidRecordModel,
    BraidTagsModel,
    BraidUrisModel,
    InvalidationActionParamsType,
    InvalidationActionType,
)

SCHEMA_FILE_NAME = "braid-db.sql"
DEFAULT_SCHEMA_FILE_PATH = Path(__file__).parent / SCHEMA_FILE_NAME

SQLITE_URL_PREFIX = "sqlite:///"


@unique
class BraidTagType(Enum):
    # Cf braid-db.sql
    NONE = 0
    STRING = 1
    INTEGER = 2
    FLOAT = 3

    @classmethod
    def type_for_value(cls):
        if isinstance(cls, int):
            return cls.INTEGER
        elif isinstance(cls, float):
            return cls.FLOAT
        elif isinstance(cls, str):
            return cls.STRING
        else:
            return cls.NONE

    def to_python_type(self):
        type_map = {"STRING": str, "INTEGER": int, "FLOAT": float}
        name = self.name
        return type_map.get(name)


BraidModelTypeVar = TypeVar("BraidModelTypeVar", bound=BraidModelBase)
TagValueType = Union[str, int, float]


class BraidTagValue:
    def __init__(self, value, type_):
        self.value = value
        self.type_ = type_


class BraidDB:
    def __init__(
        self,
        db_url: str,
        log=False,
        debug=False,
        mpi=False,
        echo_sql=False,
        create_engine_kwargs: Optional[Dict] = None,
    ):
        """Initialze a new BraidDB object. All parameters are used for
        connecting to and establishing communication with a
        database. Underlying operations are performed using the SQLModel tool,
        so many parameters take a form to be compatible with SQLModel.

        Typically, other than creating an instance of this class representing
        the DB and for creating sessions (like transactions) against the
        database, other operations should be performed using the BraidRecord
        class. Thus, most of the methods documented on this class will not
        commonly be used.

        :param db_url: An SQLModel compatible url for connecting to the
            database.

        :param log: boolean indicating whether informational logging should be
            performed.

        :param debug: boolean indicating whether debug logging should be
            performed.

        :param mpi: (Not presently implemented) boolean whether processes
            should communicate via MPI with all database operations performed
            by the rank 0 process.

        :param echo_sql: boolean indicating whether SQL operations performed on
            the database should be output to standard output. Useful primarily
            for debugging the BraidDB library.

        :param create_engine_kwargs: Additional SQLModel compatible arguments
            to be passed to the create engine operation.
        """
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

    def create_engine(
        self,
        db_url: str,
        echo_sql=False,
        create_engine_kwargs: Optional[Dict] = None,
    ):
        """Create an SQLModel engine object for communicating with the
        database. End-users should typically not make use of this method and,
        instead, should use the get_session method to instantiate a particular
        session object for (transactional) operations on the database.

        :param db_url: An SQLModel compatible url for connecting to the
            database.

        :param echo_sql: A flag indicating whether operations on the database
            should be echoed to standard output of the process running the
            operation. Typically only useful for debugging.

        :param create_engine_kwargs: Additional SQLModel compatible arguments
            to be passed to the create engine operation.

        :returns: An SQLModel "engine" which is used connect to and perform
            operations on the database.
        """
        try:
            if create_engine_kwargs is None:
                create_engine_kwargs = {}
            if echo_sql:
                create_engine_kwargs["echo"] = True
            return create_engine(db_url, echo=echo_sql)
        except ArgumentError:
            return create_engine(SQLITE_URL_PREFIX + db_url, echo=echo_sql)

    def create(self):
        """Create the DB tables used by the BraidDB. This should typically
        only be run one time as it may cause data to be deleted in some cases
        if called on a database containing data already.
        """
        if self.mpi and self.sql.rank != 0:
            return
        SQLModel.metadata.create_all(self.engine)

    def get_session(self, **kwargs) -> Session:
        """
        Returns an SQLModel Session object which can be thought of as an
        open transaction. Note that all other methods that perform DB
        operations take a Session as an optional parameter. The session for
        these methods can be created using this method. When the session is
        provided, the operations will be performed within a DB transaction and
        the session.commit() method must be used to persist the set of
        operations performed via the session. Note that if no session is passed
        to the other methods, those methods will perform their DB operations
        under a local session and will commit the results.

        :returns: An SQLModel Session object that may be passed to other
            methods of the BraidDB class.
        """
        return Session(self.engine, **kwargs)

    def run_query(
        self,
        stmt: Select,
        session: Optional[Session] = None,
        filter_func=ScalarResult.all,
    ):
        """Internal function for executing SQL statements against the
        DB. Typically should not be called by end-users.

        :param stmt: The SQLModel Select statement to be executed.

        :param session: The SQLModel session to use when running the query. If
            session is None, a new session will be created for this single
            operation.

        :param filter_func: The filtering function (e.g. one_or_none) for
            returning results. Returning all results is the default.

        :returns: Results from the query as defined by the filter_func
        """
        func_name = filter_func.__name__
        if session is not None:
            result = session.exec(stmt)
            func_to_call = getattr(result, func_name)
            return func_to_call()
        else:
            with self.get_session(expire_on_commit=False) as session:
                result = session.exec(stmt)
                func_to_call = getattr(result, func_name)
                return func_to_call()

    def query_all(self, stmt: Select, session: Optional[Session] = None):
        """Return all results from an SQLModel query

        :param stmt: The SQLModel Select statement to be executed.

        :param session: The SQLModel session to use when running the query. If
            session is None, a new session will be created for this single
            operation.

        :returns: An iterable of SQLModel model objects satsifying the query.
        """
        return self.run_query(stmt, session=session)

    def query_one_or_none(
        self, stmt: Select, session: Optional[Session] = None
    ):
        """Return a single result from a query, of None if no rows satisfy the
        query.

        :param stmt: The SQLModel Select statement to be executed.

        :param session: The SQLModel session to use when running the query. If
            session is None, a new session will be created for this single
            operation.

        :returns: A single SQLModel model object satsifying the query or None
            if no rows match the query.
        """
        return self.run_query(
            stmt, session=session, filter_func=ScalarResult.one_or_none
        )

    def get_record_model_by_id(
        self, record_id: int, session: Optional[Session] = None
    ) -> Optional[BraidRecordModel]:
        """Retrieve a single record from the database. This returns the
        internally used model object. End-users should typically not use this
        method, but instead should use the BraidRecord.by_record_id() class
        method providing this BraidDB object as a parameter.

        :param record_id: The id of the record to be retrieved.

        :param session: The SQLModel session to use when running the query. If
            session is None, a new session will be created for this single
            operation.

        :returns: An instance of the SQLModel for the record if it exists in
            the DB.
        """
        return self.query_one_or_none(
            select(BraidRecordModel).where(
                BraidRecordModel.record_id == record_id
            ),
            session=session,
        )

    def insert(self, record):
        """
        Deprecated and does nothing. Use add_model()
        """
        pass

    def add_model(
        self,
        model: BraidModelBase,
        session: Optional[Session] = None,
    ) -> BraidModelBase:
        """Add an entry into the DB using the SQLModel rendering of a
        record. Typically, end-users will use BraidRecord rather than the
        SQLModel reorientation, so this will not usually be needed by users.

        :param model: The SQLModel object to be added

        :param session: The SQLModel session to use when running the query. If
            session is None, a new session will be created for this single
            operation.

        :returns: The same BraidModel passed as input
        """
        self.trace(f"Adding model {model} to session {str(session)}")
        if session is not None:
            session.add(model)
            return model
        else:
            with Session(self.engine, expire_on_commit=False) as session:
                session.add(model)
                session.commit()
                return model

    def print(self, session: Optional[Session] = None) -> None:
        """Provide a rudimentary dump of the database to standard
        out. Suitable only for debugging. Can lead to huge amounts of output if
        the database is large.

        :param session: The SQLModel session to use when running the query. If
            session is None, a new session will be created for this single
            operation.
        """
        with Session(self.engine) as session:
            records = session.exec(select(BraidRecordModel))
            for record in records:
                record_id = record.record_id
                # text = "%5s : %-16s %s" % ("[%i]" % record_id, name, time)
                text = (
                    f"[{record.record_id:5}] : {record.name:16} {record.time}"
                )
                derivatives = self.get_derivations(record_id, session=session)
                text = text + " <- " + str([d.record_id for d in derivatives])
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

        """TODO describe function

        :param records:
        :returns:

        """
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

    def get_predecessors(
        self, record_id, session: Optional[Session] = None
    ) -> Iterable[BraidRecordModel]:
        """Return list of predecessor records in the derivation hierarchy of a
        record based on its id

        :param record_id: The id of the BraidDB record to search for
            predecessors from

        :param session: An open SQLModel session object. If none is provided,
            a temporary session will be created for only this database
            operation.

        :returns: A list of SQLModel representations of the records that
            proceed the input record id in derivation hierarchy.
        """

        self.trace(f"DB.get_predecssors({record_id}) ...")
        predecessors = self.query_all(
            select(BraidDerivationModel).where(
                BraidDerivationModel.derivation == record_id
            ),
            session=session,
        )

        pred_recs: List[BraidRecordModel] = []

        for pred in predecessors:
            pred_id = pred.record_id
            pred_rec = self.query_one_or_none(
                select(BraidRecordModel).where(
                    BraidRecordModel.record_id == pred_id
                ),
                session=session,
            )
            pred_recs.append(pred_rec)

        return pred_recs

    def get_derivations(
        self, record_id, session: Optional[Session] = None
    ) -> Iterable[BraidRecordModel]:

        """Get a list of SQLModel records that are derived from the record
        based on the record id.

        :param record_id: The id of the BraidDB record to search for
            predecessors from

        :param session: An open SQLModel session object. If none is provided,
            a temporary session will be created for only this database
            operation.

        :returns: list of derived records of a record based on its id
        """
        self.trace(f"DB.get_derivations({record_id}) ...")
        derivations = self.query_all(
            select(BraidDerivationModel).where(
                BraidDerivationModel.record_id == record_id
            ),
            session=session,
        )

        dep_recs: List[BraidRecordModel] = []

        for dep in derivations:
            derivation_id = dep.derivation
            dep_rec = self.query_one_or_none(
                select(BraidRecordModel).where(
                    BraidRecordModel.record_id == derivation_id
                ),
                session=session,
            )
            dep_recs.append(dep_rec)

        return dep_recs

    def get_uris(
        self, record_id: int, session: Optional[Session] = None
    ) -> List[str]:
        """Get a list of URIs associated with a record based on the record id.

        :param record_id: The id of the BraidDB record to retrieve uris for

        :param session: An open SQLModel session object. If none is provided,
            a temporary session will be created for only this database
            operation.

        :returns: list of strings of associated URIs

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
        """Get a dictionary of tags associated with a record

        :param record_id: The id of the BraidDB record to get the tags for

        :param session: An open SQLModel session object. If none is provided,
            a temporary session will be created for only this database
            operation.

        :returns: dict of string->BraidTagValue key->value pairs
        """
        self.trace(f"DB.get_tags({record_id}) ...")
        tag_models = self.query_all(
            select(BraidTagsModel).where(
                BraidTagsModel.record_id == record_id
            ),
            session=session,
        )
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
        """Internal method used for calculating the total number of records,
        of all types, stored in the DB. Used for debugging and performance
        computing purposes.
        """
        result = 0
        tables = ["records", "derivations", "uris", "tags"]
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
        session: Optional[Session] = None,
    ):
        """A BraidRecord is the common, base type for recording information
        into the BraidDB. Most operations on the BraidDB are performed by
        operating on a BraidRecord.

        :param db: An instance of a BraidDB to be used when operating on this
            BraidRecord. When provided, operations on an object of this class
            will be persisted to the provided BraidDB including the persistence
            of this record as a result of its creation.

        :param name: The name for this record which will be stored into the
            database.

        :param timestamp: A timestamp associated with this record. If not
            provided, the current system time will be used.

        :param debug: A boolean flag indicating whether debugging logging
            should be performed for the various operations.

        :param session: A session on the BraidDB to use when persisting this
            object. If not provided, a one-time session will be created to
            persist this object.
        """

        self.db = db
        self.name = name
        self.derivations = []
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
        if self.db is not None:
            self.db.add_model(self.model, session=session)

    @classmethod
    def from_orm(
        cls,
        orm_model: BraidRecordModel,
        db: Optional[BraidDB] = None,
        session: Optional[Session] = None,
    ) -> "BraidRecord":
        """This method creates a BraidRecord from the underlying database
        model representation. Typically not needed by end users.

        :param orm_model: The database ORM/SQLModel representation of the
            BraidRecord to be returned.

        :param db: The database object used when instantiating the BraidRecord
            to return.

        :param session: A session on the BraidDB to use when instantiating the
            BraidRecord. The returned record will be associated with this
            BraidDB.

        :returns: A BraidRecord with the same information as stored in the ORM
            model object passed in.
        """

        # Pass DB as none to prevent the init from adding a newly created,
        # duplicate BraidRecordModel to the DB.
        rec = cls(
            db=None,
            name=orm_model.name,
            timestamp=orm_model.time,
            session=session,
        )
        rec.db = db
        rec.model = orm_model
        return rec

    @classmethod
    def by_record_id(
        cls, db: BraidDB, record_id: int, session: Optional[Session] = None
    ) -> Optional["BraidRecord"]:
        """This method creates a BraidRecord by looking it up based on a record
        id.

        :param db: The database object used when looking up or instantiating
            the BraidRecord to return.

        :param session: A session on the BraidDB to use when instantiating the
            BraidRecord. The returned record will be associated with this
            BraidDB.

        :returns: A BraidRecord found in the database or None if no record with
            the provided record_id is found in the DB.
        """

        model_rec: BraidRecordModel = db.query_one_or_none(
            select(BraidRecordModel).where(
                BraidRecordModel.record_id == record_id
            ),
            session=session,
        )
        if model_rec is not None:
            return cls.from_orm(model_rec, db=db)
        else:
            return None

    @classmethod
    def for_tag_value(
        cls,
        db: BraidDB,
        key: str,
        value: TagValueType,
        session: Optional[Session] = None,
    ) -> Iterator["BraidRecord"]:
        """This method returns a list of BraidRecord objects which have a tag
        value corresponding to the tag name and input value provided.

        :param db: The database object used when looking up or instantiating
            the BraidRecords to return.

        :param key: The key for the tag to be looked up.

        :param value: The value associated with the tag to be looked up.

        :param session: A session on the BraidDB to use when instantiating the
            BraidRecords. The returned records will be associated with this
            BraidDB.

        :returns: A BraidRecord found in the database or None if no record with
            the provided record_id is found in the DB. If no records are found
            with the tag value, an empty list is returned.
        """

        model_tags: Iterable[BraidTagsModel] = db.query_all(
            select(BraidTagsModel).where(
                BraidTagsModel.key == key
                and BraidTagsModel.value == str(value)
            ),
            session=session,
        )
        return (
            cls.from_orm(model_tag.record, db=db) for model_tag in model_tags
        )

    @classmethod
    def invalidate_by_tag_value(
        cls,
        db: BraidDB,
        key: str,
        value: TagValueType,
        session: Session,
        cascade: bool = False,
        cause: Optional[str] = None,
    ) -> Iterator["BraidRecord"]:
        """This method returns a list of BraidRecord objects which have a tag
        value corresponding to the tag name and input value provided.

        :param db: The database object used when looking up or instantiating
            the BraidRecords to return.

        :param key: The key for the tag to be looked up.

        :param value: The value associated with the tag to be looked up.

        :param session: A session on the BraidDB to use when instantiating the
            BraidRecords. The returned records will be associated with this
            BraidDB.

        :returns: A BraidRecord found in the database or None if no record with
            the provided record_id is found in the DB.
        """

        if cause is None:
            cause = f"Invalidated because of tag {key} having value {value}"
        invalidates = (
            rec.invalidate(cause=cause, cascade=cascade, session=session)
            for rec in cls.for_tag_value(db, key, value, session)
        )
        return [i for i in invalidates if i is not None]

    @property
    def record_id(self) -> Optional[int]:

        if self.model.record_id is None:
            if self.db is not None:
                self.db.add_model(self.model)
        return self.model.record_id

    def add_derivation(
        self,
        record: "BraidRecord",
        session: Optional[Session] = None,
    ):
        """Add another BraidRecord as a "derivation" of this record. That is,
        the record provided as an argument is assumed to have been created or
        exist at least partially due to the existence of this record. For
        example, this record may represent a dataset which has been used to
        train a model represented by the record provided as input.

        :param record: The BraidRecord to be set as a "derivative" of this
            BraidRecord.

        :param session: A session on the BraidDB to use when persisting this
            operation. If not provided, a one-time session will be created to
            persist this object.
        """
        self.derivations.append(record)
        dep_model = BraidDerivationModel(
            record_id=self.record_id, derivation=record.model.record_id
        )
        if self.db is not None:
            dep_model = self.db.add_model(dep_model, session=session)
        return dep_model

    def add_uri(
        self,
        uri: str,
        session: Optional[Session] = None,
    ):
        """Add a URI association to this BraidRecord. URI's represent a linkage
        to a resource outside the BraidDB which may be useful for accessing or
        otherwise referencing the entity represented by this BraidRecord. Note
        that more than one URI may be associated with a single BraidRecord.

        :param uri: The URI string to associate with this BraidRecord.

        :param session: A session on the BraidDB to use when persisting this
            operation. If not provided, a one-time session will be created to
            persist this object.
        """
        self.uris.append(uri)
        uri_model = BraidUrisModel(record_id=self.record_id, uri=uri)
        if self.db is not None:
            self.db.add_model(uri_model, session=session)

    def get_uris(self) -> List[str]:
        """Return the list of all URIs associated with this BraidRecord. If no
        URIs are associated, an empty list will be returned.
        """
        return [u.uri for u in self.model.uris]

    def add_tag(
        self,
        key,
        value,
        type_=BraidTagType.STRING,
        session: Optional[Session] = None,
    ) -> int:
        """Add a key/value tag to this BraidRecord.

        :param key:   a string key name

        :param value: a string value

        :param type_: The data type of the tag as defined by the BraidTagType.

        :param session: A session on the BraidDB to use when persisting this
            operation. If not provided, a one-time session will be created to
            persist this object.

        :returns: The tag ID.
        """
        if not isinstance(type_, BraidTagType):
            raise Exception(
                "type must be a BraidTagType! "
                f"received: {str(type_)} type: {type(type_)}"
            )
        self.tags[key] = value
        tag_model = BraidTagsModel(
            record_id=self.record_id,
            key=key,
            value=value,
            tag_type=type_.value,
        )
        if self.db is not None:
            self.db.add_model(tag_model, session=session)
        return tag_model.id

    def tags_as_dict(
        self, session: Optional[Session] = None
    ) -> Dict[str, TagValueType]:
        """Return the tags on this BraidRecord as a dictionary.

        :param session: A session on the BraidDB to use when persisting this
            operation. If not provided, a one-time session will be created to
            persist this object.

        :returns: Dictionary containing the tags associated with this
            BraidRecord.
        """
        tags: Iterable[BraidTagsModel] = self.db.query_all(
            select(BraidTagsModel).where(
                BraidTagsModel.record_id == self.record_id
            ),
            session=session,
        )
        ret_dict: Dict[str, TagValueType] = {}
        for tag in tags:
            key = tag.key
            value = tag.value
            # tag_type = tag.tag_type
            # TODO: Use tag_type to coerce value to the proper python type
            ret_dict[key] = value

        return ret_dict

    def set_invalidation_action(
        self,
        invalidation_action_id: str,
        session: Optional[Session] = None,
    ) -> Optional[BraidInvalidationAction]:
        """Set the invalidation action to be performed if this BraidRecord
        should be flagged as invalid.

        :param invalidation_action_id: The id of the invalidation action to
            associate with this BraidRecord. Commonly, this invalidation action
            will be crated by setting it on another BraidRecord using the
            add_invalidation_action method. If the invalidation action with
            this id is not found, no invalidation action will be associated
            with this BraidRecord and the method will return None.

        :param session: A session on the BraidDB to use when persisting this
            operation. If not provided, a one-time session will be created to
            persist this object.

        :returns: The BraidInvalidationAction object corresponding to the
            action set on this BraidRecord. If no invalidation action with the
            provided id is found, None will be returned.
        """
        ia = self.db.query_one_or_none(
            select(BraidInvalidationAction).where(
                BraidInvalidationAction.id == invalidation_action_id
            ),
            session=session,
        )
        if ia is not None:
            self.model.invalidation_action = ia
        return ia

    def add_invalidation_action(
        self,
        action_type: InvalidationActionType,
        name: str,
        cmd: str,
        params: InvalidationActionParamsType,
        session: Optional[Session] = None,
    ) -> BraidInvalidationAction:
        """Add an invalidation action to be performed if this BraidRecord
        should be flagged as invalid.

        :param action_type: The type of action to be performed. This can be
            either running a shell command locally, or starting a Globus
            Automate Action.

        :param name: The name for this action

        :param cmd: The command to execute. The format for this various
            depending on whether a shell command or Globus Automate action type
            is used.

        :param params: Parameters to the action to perform. Format for the
            parameters depends on the type of the invalidation action.

        :param session: A session on the BraidDB to use when persisting this
            operation. If not provided, a one-time session will be created to
            persist this object.

        :returns: The BraidInvalidationAction object corresponding to the
            action set on this BraidRecord. If no invalidation action with the
            provided id is found, None will be returned.
        """
        # TODO: Some validation that the paramters are correct
        invalidation_action = BraidInvalidationAction(
            action_type=action_type,
            name=name,
            cmd=cmd,
            params=params,
            record_id=self.model.record_id,
        )
        self.model.invalidation_action = invalidation_action
        if self.db is not None:
            self.db.add_model(invalidation_action, session=session)
        return invalidation_action

    def invalidate(
        self,
        cause: Optional[str] = None,
        root_invalidation: Optional[Union[str, UUID]] = None,
        cascade=True,
        perform_invalidation_action=True,
        perform_invalidation_action_on_cascade=True,
        session: Optional[Session] = None,
    ) -> Optional["BraidRecord"]:
        """Mark this BraidRecord as invalid.

        :param cause: A string describing the reason this record is considered
            to be invalid at this point.

        :param root_invalidation: A reference to another invalidation which is
            considered to be the root cause that made this record
            invalid. Typically, this will be due an invalidation on a record
            that this record was derived from.

        :param cascade: A boolean flag indicating whether any records which are
            derived from this record will also be marked as invalid. When these
            derived records are marked invalid, the invalidation of this record
            will be marked as the root cause of the derived record's
            invalidation.

        :param perform_invalidation_action: A boolean flag indicating whether
            the invalidation action associated with this record (if any) should
            be invoked.

        :param perform_invalidation_action_on_cascade: A boolean flag
            indicating whether invalidations performed on derived records
            should cause their invalidation actions (if any) to be invoked.

        :param session: A session on the BraidDB to use when persisting this
            operation. If not provided, a one-time session will be created to
            persist this object.

        :returns: The same record itself.
        """
        if self.model.invalidation_id is not None:
            return None
        if cause is None and root_invalidation is None:
            raise ValueError(
                "At least one of the cause or "
                "root_invalidation must be provided"
            )
        if cause is None:
            cause = f"As a result of Invalidation id {str(root_invalidation)}"
        invalid_model = BraidInvalidationModel(cause=cause)
        if root_invalidation is not None:
            invalid_model.root_invalidation = UUID(str(root_invalidation))
        if self.db is not None:
            self.db.add_model(invalid_model, session=session)
            self.model.invalidation = invalid_model
            if cascade:
                derivations = self.db.get_derivations(
                    self.model.record_id, session=session
                )
                for derivation in derivations:
                    dep_rec = BraidRecord.from_orm(derivation, db=self.db)
                    dep_rec.invalidate(
                        cause=cause,
                        root_invalidation=invalid_model.id,
                        cascade=cascade,
                        perform_invalidation_action=(
                            perform_invalidation_action_on_cascade
                        ),
                        perform_invalidation_action_on_cascade=(
                            perform_invalidation_action_on_cascade
                        ),
                        session=session,
                    )
        self.perform_invalidation_action(session=session)
        return self

    def perform_invalidation_action(
        self, session: Optional[Session] = None
    ) -> None:
        """Perform the invalidation action associated with this
        BraidRecord. Typically, this method is not invoked directly but rather
        is called internally as a result of the invalidate method.

        :param session: A session on the BraidDB to use when persisting this
            operation. If not provided, a one-time session will be created to
            persist this object.
        """
        invalidation_action = self.model.invalidation_action
        if invalidation_action is None:
            return

        return

        substitution_vals = self.tags_as_dict(session)
        substitution_vals["name"] = self.model.name
        substitution_vals["uri"] = self.model.uri

        cmd = substitute_vals(invalidation_action.cmd, substitution_vals)
        params = substitute_vals(invalidation_action.params, substitution_vals)

        if (
            invalidation_action.action_type
            is InvalidationActionType.SHELL_COMMAND
        ):
            cmd_line = [cmd]
            cmd_line.extend(params.get("args", []))
            action_run = subprocess.run(cmd_line)
            self.debug(
                f"Return of command {cmd} {params} was: "
                f"{action_run.returncode}"
            )
        elif (
            invalidation_action.action_type
            is InvalidationActionType.AUTOMATE_EVENT
        ):
            ...
        else:
            ...

    def is_valid(self, session: Optional[Session] = None) -> bool:
        """Return whether the record is valid or has been marked as invalid.

        :returns: True if the record is valid or False if it has been marked
            invalid.
        """
        return self.model.invalidation_id is None

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
    """BraidFact is a specialization of a BraidRecord representing an
    immutable or pre-determined piece of information. Examples: pre-existing
    data, software, etc.
    """

    def __init__(self, db=None, name=None):
        super().__init__(db=db, name=name)

    def add_derivation(self, record):
        """record: a BraidRecord"""
        raise Exception("BraidFacts do not have derivatives!")

    def store(self) -> int:
        self.db.add_model(self.model)
        self.debug(f"stored Fact: {self.model.record_id}")
        return self.model.record_id


class BraidData(BraidRecord):
    """BraidData is a specialization of a BraidRecord intended to represent
    data generated during an experiment. A BraidData record will typically be
    associated with another record as a derivative record. Examples: data in
    the system with derivatives: Simulation outputs, data analyses, experiment
    outputs
    """

    def __init__(self, db=None, name=None):
        super().__init__(db=db, name=name)

    def store(self) -> int:
        self.db.add_model(self.model)
        self.debug(f"stored Data: {self.model.record_id}")
        return self.model.record_id


class BraidModel(BraidRecord):
    """BraidModel is a specialization of a BraidRecord intended to represent
    the result of a computation or model training operation. It will typically
    be derived from a set of BraidData records representing the computation
    input (or training data sets), BraidFacts representing software or
    immutable inputs and will have derived records representing artifacts such
    as resulting datasets. Examples: an ML model that is trained on
    BraidRecords
    """

    def __init__(self, db=None, name=None):
        super().__init__(db=db, name=name)

    def update(self, record):
        """record: a BraidRecord"""
        super().add_derivation(record)

    def store(self) -> int:
        self.db.add_model(self.model)
        self.debug(f"stored Model: {self.model.record_id}")
        return self.model.record_id
