from typing import List, Optional, Any, Mapping
from pydantic import BaseModel


class _ObservationTransformation(BaseModel):
    name: str
    active: List[bool]
    scale: List[float]
    observation_id: int


class ObservationTransformationIn(_ObservationTransformation):
    pass


class ObservationTransformationOut(_ObservationTransformation):
    id: int

    class Config:
        orm_mode = True


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
    transformation: Optional[ObservationTransformationOut] = None
    metadata: Mapping[str, Any] = {}

    class Config:
        orm_mode = True
