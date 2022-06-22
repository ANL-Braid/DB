from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Union
from uuid import UUID

from pydantic import BaseModel, Field


class APIBraidTagType(str, Enum):
    NONE = "NONE"
    STRING = "STRING"
    INTEGER = "INT"
    FLOAT = "FLOAT"


class APITagValue(BaseModel):
    value: Union[int, float, str]
    typ: APIBraidTagType = Field(alias="type")


class APIBraidRecordCommon(BaseModel):
    name: str
    invalidation_id: Optional[UUID]
    uris: Optional[List[str]]
    tags: Optional[Dict[str, APITagValue]]


class APIBraidRecordInput(APIBraidRecordCommon):
    derivations: Optional[List["APIBraidRecordInput"]]
    derived_from_record_id: Optional[int]


class APIInvalidationCommon(BaseModel):
    ...


class APIInvalidationInput(APIInvalidationCommon):
    ...


class APIInvalidationOutput(APIInvalidationCommon):
    ...


class APIBraidRecordOutput(APIBraidRecordCommon):
    time: datetime
    record_id: int
    derivations: Optional[List["APIBraidRecordOutput"]]
    invalidation: Optional[APIInvalidationOutput]
