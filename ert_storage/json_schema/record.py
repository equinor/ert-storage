from typing import List, Any
from pydantic import BaseModel


class _Record(BaseModel):
    pass


class RecordOut(_Record):
    id: int
    name: str
    data: Any

    class Config:
        orm_mode = True
