from enum import Enum

import sqlalchemy as sa
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.schema import UniqueConstraint

from ert_storage.database import Base


class RecordType(Enum):
    parameters = 0
    float_vector = 1
    file = 2

    @staticmethod
    def from_str(other: str) -> "RecordType":
        return {
            "parameters": RecordType.parameters,
            "float_vector": RecordType.float_vector,
            "file": RecordType.file,
        }[other]


class Ensemble(Base):
    __tablename__ = "ensemble"

    id = sa.Column(sa.Integer, primary_key=True)
    time_created = sa.Column(sa.DateTime, server_default=func.now())
    time_updated = sa.Column(
        sa.DateTime, server_default=func.now(), onupdate=func.now()
    )

    parameters = sa.Column(sa.ARRAY(sa.FLOAT), nullable=False)
    num_realizations = sa.Column(sa.Integer, nullable=False)


class Record(Base):
    __tablename__ = "record"
    __table_args__ = (UniqueConstraint("ensemble_id", "realization_index", "name"),)

    id = sa.Column(sa.Integer, primary_key=True)
    time_created = sa.Column(sa.DateTime, server_default=func.now())
    time_updated = sa.Column(
        sa.DateTime, server_default=func.now(), onupdate=func.now()
    )

    name = sa.Column(sa.String, nullable=False)
    realization_index = sa.Column(sa.Integer, nullable=True)
    _record_type = sa.Column("record_type", sa.Integer, nullable=False)
    data = sa.Column(sa.PickleType, nullable=False)
    is_response = sa.Column(sa.Boolean, nullable=False)

    ensemble_id = sa.Column(sa.Integer, sa.ForeignKey("ensemble.id"), nullable=False)

    ensemble = relationship("Ensemble")

    @property
    def record_type(self) -> RecordType:
        return RecordType(self._record_type)

    @record_type.setter
    def record_type(self, other: RecordType) -> None:
        self._record_type = other.value
