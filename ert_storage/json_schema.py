from typing import List, Optional, Any
from pydantic import BaseModel


class _Ensemble(BaseModel):
    pass


class EnsembleIn(_Ensemble):
    parameters: List[str]
    ensemble_id: Optional[int]


class EnsembleOut(_Ensemble):
    id: int

    class Config:
        orm_mode = True


class _Record(BaseModel):
    pass


class RecordOut(_Record):
    id: int
    name: str
    data: Any

    class Config:
        orm_mode = True
