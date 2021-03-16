from enum import Enum
from typing import Any, Optional

import sqlalchemy as sa
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ert_storage.database import Base, IS_POSTGRES


if IS_POSTGRES:
    FloatArray = sa.ARRAY(sa.FLOAT)
    StringArray = sa.ARRAY(sa.String)

else:
    FloatArray = sa.PickleType
    StringArray = sa.PickleType


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
    inputs = sa.Column(StringArray)
    records = relationship("Record", foreign_keys="[Record.ensemble_id]")


class Record(Base):
    __tablename__ = "record"

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

    file_id = sa.Column(sa.Integer, sa.ForeignKey("file.id"))
    f64_matrix_id = sa.Column(sa.Integer, sa.ForeignKey("f64_matrix.id"))

    file = relationship("File")
    f64_matrix = relationship("F64Matrix")
    ensemble_id = sa.Column(sa.Integer, sa.ForeignKey("ensemble.id"), nullable=True)
    ensemble = relationship("Ensemble", back_populates="records")

    @property
    def record_type(self) -> RecordType:
        return RecordType(self._record_type)

    @record_type.setter
    def record_type(self, other: RecordType) -> None:
        self._record_type = other.value

    @property
    def data(self) -> Any:
        if self.record_type == RecordType.file:
            return self.file.content
        elif self.record_type == RecordType.float_vector:
            return self.f64_matrix.content
        else:
            raise NotImplementedError(
                f"The record type {self.record_type} is not yet implemented"
            )


class File(Base):
    __tablename__ = "file"

    id = sa.Column(sa.Integer, primary_key=True)
    time_created = sa.Column(sa.DateTime, server_default=func.now())
    time_updated = sa.Column(
        sa.DateTime, server_default=func.now(), onupdate=func.now()
    )

    filename = sa.Column(sa.String, nullable=False)
    mimetype = sa.Column(sa.String, nullable=False)

    content = sa.Column(sa.LargeBinary)
    az_container = sa.Column(sa.String)
    az_blob = sa.Column(sa.String)


class F64Matrix(Base):
    __tablename__ = "f64_matrix"

    id = sa.Column(sa.Integer, primary_key=True)
    time_created = sa.Column(sa.DateTime, server_default=func.now())
    time_updated = sa.Column(
        sa.DateTime, server_default=func.now(), onupdate=func.now()
    )

    content = sa.Column(FloatArray, nullable=False)
