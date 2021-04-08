from typing import List, Optional
from pydantic import BaseModel


class _Ensemble(BaseModel):
    pass


class EnsembleIn(_Ensemble):
    parameters: List[str]
    update_id: Optional[int] = None


class EnsembleOut(_Ensemble):
    id: int
    children: List[int]
    parent: Optional[int] = None

    class Config:
        orm_mode = True
