from typing import List, Optional, Any
from pydantic import BaseModel


class _Ensemble(BaseModel):
    pass


class EnsembleIn(_Ensemble):
    parameters: List[str]


class EnsembleOut(_Ensemble):
    id: int

    class Config:
        orm_mode = True


class _Experiment(BaseModel):
    name: str


class ExperimentIn(_Experiment):
    pass


class ExperimentOut(_Experiment):
    id: int
    ensembles: Optional[List[int]] = None

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
