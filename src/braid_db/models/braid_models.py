import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlmodel import JSON, Column
from sqlmodel import Enum as SqlmodelEnum
from sqlmodel import Field, Relationship, SQLModel

# InvalidationActionParamsType = Dict[str, Union[str, int, float, bool]]
InvalidationActionParamsType = Dict[str, Any]


def datetime_now() -> datetime:
    return datetime.utcnow()


timestamp_now_field = Field(default_factory=datetime_now)


class BraidModelBase(SQLModel):
    ...


class BraidDerivationModel(BraidModelBase, table=True):
    __tablename__: str = "derivations"
    record_id: Optional[int] = Field(
        default=None, primary_key=True, foreign_key="records.record_id"
    )
    derivation: Optional[int] = Field(
        default=None, primary_key=True, foreign_key="records.record_id"
    )
    time: datetime = timestamp_now_field


class BraidInvalidationModel(BraidModelBase, table=True):
    __tablename__ = "invalidations"
    id: Optional[UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    records: List["BraidRecordModel"] = Relationship(
        back_populates="invalidation"
    )
    root_invalidation: Optional[UUID] = Field(foreign_key="invalidations.id")
    cause: str
    time: datetime = timestamp_now_field


class InvalidationActionType(str, Enum):
    SHELL_COMMAND = "shell"
    AUTOMATE_EVENT = "automate_event"


class BraidInvalidationAction(BraidModelBase, table=True):
    __tablename__ = "invalidation_actions"

    class Config:
        arbitrary_types_allowed = True

    id: Optional[UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str

    action_type: InvalidationActionType = Field(
        sa_column=Column(SqlmodelEnum(InvalidationActionType))
    )
    cmd: str
    # params: str = Field(default_factory=dict, sa_column=Column(JSON))
    params: InvalidationActionParamsType = Field(
        default_factory=dict, sa_column=Column(JSON)
    )
    records: List["BraidRecordModel"] = Relationship(
        back_populates="invalidation_action"
    )


class BraidUrisModel(BraidModelBase, table=True):
    __tablename__: str = "uris"
    id: Optional[int] = Field(default=None, primary_key=True)
    record_id: int = Field(foreign_key="records.record_id", index=True)
    uri: str
    record: "BraidRecordModel" = Relationship(back_populates="uris")


class BraidRecordModel(BraidModelBase, table=True):
    __tablename__: str = "records"
    record_id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    time: datetime = timestamp_now_field
    invalidation_id: Optional[UUID] = Field(
        default=None, foreign_key="invalidations.id"
    )
    invalidation: Optional[BraidInvalidationModel] = Relationship(
        back_populates="records"
    )
    invalidation_action_id: Optional[UUID] = Field(
        default=None, foreign_key="invalidation_actions.id"
    )
    invalidation_action: Optional[BraidInvalidationAction] = Relationship(
        back_populates="records"
    )

    uris: List[BraidUrisModel] = Relationship(back_populates="record")

    # So, we define a property for looking at the single uri as well
    @property
    def uri(self) -> Optional[BraidUrisModel]:
        return self.uris[0] if len(self.uris) > 0 else None

    tags: List["BraidTagsModel"] = Relationship(back_populates="record")

    """
    parent_records: List["BraidRecordModel"] = Relationship(
        back_populates="dependent_resords",
        link_model=BraidDependencyModel,
        sa_relationship_kwargs={
            "primaryjoin": "records.record_id==dependencies.dependency",
            "secondaryjoin": "records.record_id==dependencies.record_id",
        },
    )
    dependent_records: List["BraidRecordModel"] = Relationship(
        back_populates="parent_resords",
        link_model=BraidDependencyModel,
        sa_relationship_kwargs={
            "primaryjoin": "records.record_id==dependencies.record_id",
            "secondaryjoin": "records.record_id==dependencies.dependency",
        },
    )
    """


class BraidTagsModel(BraidModelBase, table=True):
    __tablename__: str = "tags"
    id: Optional[int] = Field(default=None, primary_key=True)
    record_id: int = Field(foreign_key="records.record_id")
    key: str
    value: str
    tag_type: int
    record: BraidRecordModel = Relationship(back_populates="tags")
