from typing import List
from pydantic import BaseModel


class _Ensemble(BaseModel):
    pass


class EnsembleIn(_Ensemble):
    parameters: List[str]


class EnsembleOut(_Ensemble):
    id: int

    class Config:
        orm_mode = True
