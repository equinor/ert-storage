from typing import List, Mapping, Optional, Any
from pydantic import BaseModel


class _Experiment(BaseModel):
    name: str


class ExperimentIn(_Experiment):
    pass


class ExperimentOut(_Experiment):
    id: int
    ensembles: List[int]
    metadata: Mapping[str, Any] = {}

    class Config:
        orm_mode = True
