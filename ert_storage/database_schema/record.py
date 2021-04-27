from enum import Enum
from typing import Any, Optional
import sqlalchemy as sa
from ert_storage.database import Base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ert_storage.ext.uuid import UUID
from uuid import uuid4

from .metadatafield import MetadataField
from .observation import observation_record_association
from ert_storage.ext.sqlalchemy_arrays import FloatArray


class RecordType(Enum):
    float_vector = 1
    file = 2


class RecordClass(Enum):
    parameter = 1
    response = 2
    other = 3


class Record(Base, MetadataField):
    __tablename__ = "record"

    def __init__(
        self, *args: Any, record_type: Optional[RecordType] = None, **kwargs: Any
    ) -> None:
        if record_type is not None:
            kwargs.setdefault("_record_type", record_type.value)
        super().__init__(*args, **kwargs)

    pk = sa.Column(sa.Integer, primary_key=True)
    id = sa.Column(UUID, unique=True, default=uuid4, nullable=False)
    time_created = sa.Column(sa.DateTime, server_default=func.now())
    time_updated = sa.Column(
        sa.DateTime, server_default=func.now(), onupdate=func.now()
    )

    name = sa.Column(sa.String, nullable=False)
    realization_index = sa.Column(sa.Integer, nullable=True)
    _record_type = sa.Column("record_type", sa.Integer, nullable=False)

    file_pk = sa.Column(sa.Integer, sa.ForeignKey("file.pk"))
    f64_matrix_pk = sa.Column(sa.Integer, sa.ForeignKey("f64_matrix.pk"))

    file = relationship("File", cascade="all")
    f64_matrix = relationship("F64Matrix", cascade="all")
    ensemble_pk = sa.Column(sa.Integer, sa.ForeignKey("ensemble.pk"), nullable=True)
    ensemble = relationship("Ensemble", back_populates="records")
    observations = relationship(
        "Observation",
        secondary=observation_record_association,
        back_populates="records",
    )
    record_class = sa.Column(sa.Enum(RecordClass))

    prior_pk = sa.Column(sa.Integer, sa.ForeignKey("prior.pk"), nullable=True)
    prior = relationship("Prior")

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

    pk = sa.Column(sa.Integer, primary_key=True)
    id = sa.Column(UUID, unique=True, default=uuid4, nullable=False)
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

    pk = sa.Column(sa.Integer, primary_key=True)
    id = sa.Column(UUID, unique=True, default=uuid4, nullable=False)
    time_created = sa.Column(sa.DateTime, server_default=func.now())
    time_updated = sa.Column(
        sa.DateTime, server_default=func.now(), onupdate=func.now()
    )
    content = sa.Column(FloatArray, nullable=False)
    labels = sa.Column(sa.PickleType)


class FileBlock(Base):
    __tablename__ = "file_block"

    pk = sa.Column(sa.Integer, primary_key=True)
    id = sa.Column(UUID, unique=True, default=uuid4, nullable=False)
    time_created = sa.Column(sa.DateTime, server_default=func.now())
    time_updated = sa.Column(
        sa.DateTime, server_default=func.now(), onupdate=func.now()
    )
    block_id = sa.Column(sa.String, nullable=False)
    block_index = sa.Column(sa.Integer, nullable=False)
    record_name = sa.Column(sa.String, nullable=False)
    realization_index = sa.Column(sa.Integer, nullable=True)
    ensemble_pk = sa.Column(sa.Integer, sa.ForeignKey("ensemble.pk"), nullable=True)
    ensemble = relationship("Ensemble")
    content = sa.Column(sa.LargeBinary, nullable=True)
