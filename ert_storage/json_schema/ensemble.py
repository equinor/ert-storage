from uuid import UUID
from typing import List, Optional
from pydantic import BaseModel


class _Ensemble(BaseModel):
    pass


class EnsembleIn(_Ensemble):
    parameters: List[str]
    update_id: Optional[UUID] = None


class EnsembleOut(_Ensemble):
    id: UUID
    children: List[UUID]
    parent: Optional[UUID] = None

    class Config:
        orm_mode = True
