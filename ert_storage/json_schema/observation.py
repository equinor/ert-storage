from typing import List, Optional, Any
from pydantic import BaseModel
from .record import RecordOut


class _Observation(BaseModel):
    name: str
    errors: List[float]
    values: List[float]
    x_axis: List[Any]
    records: Optional[List[int]] = None


class ObservationIn(_Observation):
    pass


class ObservationOut(_Observation):
    id: int

    class Config:
        orm_mode = True
