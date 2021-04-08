from typing import List, Optional
from pydantic import BaseModel


class _Experiment(BaseModel):
    name: str


class ExperimentIn(_Experiment):
    pass


class ExperimentOut(_Experiment):
    id: int
    ensembles: List[int]

    class Config:
        orm_mode = True
