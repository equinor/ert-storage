from typing import List
from uuid import uuid4, UUID as PyUUID
import sqlalchemy as sa
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ert_storage.database import Base
from .metadatafield import MetadataField
from ert_storage.ext.uuid import UUID as UUID
from ert_storage.ext.sqlalchemy_arrays import StringArray


class Ensemble(Base, MetadataField):
    __tablename__ = "ensemble"

    pk = sa.Column(sa.Integer, primary_key=True)
    id = sa.Column(UUID, unique=True, default=uuid4, nullable=False)
    size = sa.Column(sa.Integer, nullable=False)
    time_created = sa.Column(sa.DateTime, server_default=func.now())
    time_updated = sa.Column(
        sa.DateTime, server_default=func.now(), onupdate=func.now()
    )
    parameter_names = sa.Column(StringArray, nullable=False)
    response_names = sa.Column(StringArray, nullable=False)
    record_infos = relationship(
        "RecordInfo",
        foreign_keys="[RecordInfo.ensemble_pk]",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )
    experiment_pk = sa.Column(
        sa.Integer, sa.ForeignKey("experiment.pk"), nullable=False
    )
    experiment = relationship("Experiment", back_populates="ensembles")
    children = relationship(
        "Update",
        foreign_keys="[Update.ensemble_reference_pk]",
    )
    parent = relationship(
        "Update",
        uselist=False,
        foreign_keys="[Update.ensemble_result_pk]",
        cascade="all, delete-orphan",
    )

    @property
    def parent_ensemble_id(self) -> PyUUID:
        return self.parent.ensemble_reference.id

    @property
    def child_ensemble_ids(self) -> List[PyUUID]:
        return [x.ensemble_result.id for x in self.children]
