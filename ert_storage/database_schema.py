from enum import Enum
from typing import Any, Optional

import sqlalchemy as sa
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.schema import UniqueConstraint

from ert_storage.database import Base


class RecordType(Enum):
    parameters = 0
    float_vector = 1
    file = 2


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

    def __init__(
        self, *args: Any, record_type: Optional[RecordType] = None, **kwargs: Any
    ) -> None:
        if record_type is not None:
            kwargs.setdefault("_record_type", record_type.value)
        super().__init__(*args, **kwargs)

    id = sa.Column(sa.Integer, primary_key=True)
    time_created = sa.Column(sa.DateTime, server_default=func.now())
    time_updated = sa.Column(
        sa.DateTime, server_default=func.now(), onupdate=func.now()
    )

    name = sa.Column(sa.String, nullable=False)
    realization_index = sa.Column(sa.Integer, nullable=True)
    _record_type = sa.Column("record_type", sa.Integer, nullable=False)
    is_response = sa.Column(sa.Boolean, nullable=False)

    ensemble_id = sa.Column(sa.Integer, sa.ForeignKey("ensemble.id"), nullable=False)
    file_id = sa.Column(sa.Integer, sa.ForeignKey("file.id"))
    f64_matrix_id = sa.Column(sa.Integer, sa.ForeignKey("f64_matrix.id"))

    ensemble = relationship("Ensemble")
    file = relationship("File")
    f64_matrix = relationship("F64Matrix")

    @property
    def record_type(self) -> RecordType:
        return RecordType(self._record_type)

    @record_type.setter
    def record_type(self, other: RecordType) -> None:
        self._record_type = other.value


class File(Base):
    __tablename__ = "file"

    id = sa.Column(sa.Integer, primary_key=True)
    time_created = sa.Column(sa.DateTime, server_default=func.now())
    time_updated = sa.Column(
        sa.DateTime, server_default=func.now(), onupdate=func.now()
    )

    filename = sa.Column(sa.String, nullable=False)
    mimetype = sa.Column(sa.String, nullable=False)

    content = sa.Column(sa.Binary, nullable=False)


class F64Matrix(Base):
    __tablename__ = "f64_matrix"

    id = sa.Column(sa.Integer, primary_key=True)
    time_created = sa.Column(sa.DateTime, server_default=func.now())
    time_updated = sa.Column(
        sa.DateTime, server_default=func.now(), onupdate=func.now()
    )

    content = sa.Column(sa.ARRAY(sa.FLOAT), nullable=False)
