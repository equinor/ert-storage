from pydantic import BaseModel
from typing import List, Union, Optional
from .observation import (
    ObservationTransformationIn,
)


class _Update(BaseModel):
    algorithm: str
    ensemble_result_id: Union[int, None]
    ensemble_reference_id: Union[int, None]


class UpdateIn(_Update):
    observation_transformations: Optional[List[ObservationTransformationIn]] = None


class UpdateOut(_Update):
    id: int

    class Config:
        orm_mode = True
