from uuid import UUID
from typing import Any, Mapping
from pydantic import BaseModel


class _Record(BaseModel):
    pass


class RecordOut(_Record):
    id: UUID
    name: str
    _metadata: Mapping[str, Any]

    class Config:
        orm_mode = True
