from uuid import UUID
from typing import List, Mapping, Any
from pydantic import BaseModel


class _Experiment(BaseModel):
    name: str


class ExperimentIn(_Experiment):
    pass


class ExperimentOut(_Experiment):
    id: UUID
    ensembles: List[UUID]
    metadata: Mapping[str, Any] = {}

    class Config:
        orm_mode = True
