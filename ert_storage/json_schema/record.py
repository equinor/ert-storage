from typing import List, Any, Optional, Mapping
from pydantic import BaseModel


class _Record(BaseModel):
    pass


class RecordOut(_Record):
    id: int
    name: str
    data: Any
    metadata: Mapping[str, Any]

    class Config:
        orm_mode = True
