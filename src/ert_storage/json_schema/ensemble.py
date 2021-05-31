from uuid import UUID
from typing import List, Optional, Any, Mapping
from pydantic import BaseModel, Field, root_validator


class _Ensemble(BaseModel):
    size: int
    parameter_names: List[str]
    response_names: List[str]


class EnsembleIn(_Ensemble):
    update_id: Optional[UUID] = None
    metadata: Optional[Any]

    @root_validator
    def _check_names_no_overlap(cls, values: Mapping[str, Any]) -> Mapping[str, Any]:
        """
        Verify that `parameter_names` and `response_names` don't overlap. Ie, no
        record can be both a parameter and a response.
        """
        if not set(values["parameter_names"]).isdisjoint(set(values["response_names"])):
            raise ValueError("parameters and responses cannot have a name in common")
        return values


class EnsembleOut(_Ensemble):
    id: UUID
    children: List[UUID] = Field(alias="child_ensemble_ids")
    parent: Optional[UUID] = Field(alias="parent_ensemble_id")
    experiment_id: Optional[UUID] = None
    metadata: Mapping[str, Any] = Field(alias="metadata_dict")

    class Config:
        orm_mode = True
