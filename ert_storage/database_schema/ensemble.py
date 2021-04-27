from enum import Enum
from typing import Any, Iterable
from uuid import uuid4
import sqlalchemy as sa
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ert_storage.database import Base
from .metadatafield import MetadataField
from .record import RecordClass, Record
from ert_storage.ext.uuid import UUID
from ert_storage.ext.sqlalchemy_arrays import StringArray


class Ensemble(Base, MetadataField):
    __tablename__ = "ensemble"

    pk = sa.Column(sa.Integer, primary_key=True)
    id = sa.Column(UUID, unique=True, default=uuid4, nullable=False)
    time_created = sa.Column(sa.DateTime, server_default=func.now())
    time_updated = sa.Column(
        sa.DateTime, server_default=func.now(), onupdate=func.now()
    )
    inputs = sa.Column(StringArray)
    records = relationship(
        "Record",
        foreign_keys="[Record.ensemble_pk]",
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
    def parameters(self) -> Iterable["Record"]:
        return self.records.filter_by(record_class=RecordClass.parameter)
