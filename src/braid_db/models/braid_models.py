from datetime import datetime
from typing import List, Optional

from sqlmodel import Field, Relationship, SQLModel


def datetime_now() -> datetime:
    return datetime.utcnow()


class BraidModelBase(SQLModel):
    ...


class BraidDependencyModel(BraidModelBase, table=True):
    __tablename__: str = "dependencies"
    record_id: Optional[int] = Field(
        default=None, primary_key=True, foreign_key="records.record_id"
    )
    dependency: Optional[int] = Field(
        default=None, primary_key=True, foreign_key="records.record_id"
    )
    time: datetime = Field(default_factory=datetime_now)


class BraidRecordModel(BraidModelBase, table=True):
    __tablename__: str = "records"
    record_id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    time: datetime = Field(default_factory=datetime_now)

    # We have to declare uri as a list even though we know it can only have one
    # value (i.e. one-to-one relationship)
    uris: List["BraidUrisModel"] = Relationship(back_populates="record")

    # So, we define a property for looking at the single uri as well
    @property
    def uri(self) -> Optional["BraidUrisModel"]:
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


class BraidUrisModel(BraidModelBase, table=True):
    __tablename__: str = "uris"
    id: Optional[int] = Field(default=None, primary_key=True)
    record_id: int = Field(foreign_key="records.record_id", index=True)
    uri: str
    record: BraidRecordModel = Relationship(back_populates="uris")


class BraidTagsModel(BraidModelBase, table=True):
    __tablename__: str = "tags"
    id: Optional[int] = Field(default=None, primary_key=True)
    record_id: int = Field(foreign_key="records.record_id")
    key: str
    value: str
    tag_type: int
    record: BraidRecordModel = Relationship(back_populates="tags")
