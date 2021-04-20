from enum import Enum
from typing import Any, Optional, Mapping

import sqlalchemy as sa
from uuid import uuid4

from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ert_storage.database import Base

from ert_storage.ext.sqlalchemy_arrays import StringArray, FloatArray
from ert_storage.ext.uuid import UUID


class RecordType(Enum):
    float_vector = 1
    file = 2


class RecordClass(Enum):
    parameter = 1
    response = 2
    other = 3


class MetadataField:
    _metadata = sa.Column("metadata", sa.JSON, nullable=True)

    @property
    def metadata_dict(self) -> Mapping[str, Any]:
        if self._metadata is None:
            return dict()
        return self._metadata


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
        "Record", foreign_keys="[Record.ensemble_pk]", cascade="all, delete-orphan"
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


class Experiment(Base, MetadataField):
    __tablename__ = "experiment"

    pk = sa.Column(sa.Integer, primary_key=True)
    id = sa.Column(UUID, unique=True, default=uuid4, nullable=False)
    time_created = sa.Column(sa.DateTime, server_default=func.now())
    time_updated = sa.Column(
        sa.DateTime, server_default=func.now(), onupdate=func.now()
    )
    name = sa.Column(sa.String)
    ensembles = relationship(
        "Ensemble",
        foreign_keys="[Ensemble.experiment_pk]",
        cascade="all, delete-orphan",
    )
    observations = relationship(
        "Observation",
        foreign_keys="[Observation.experiment_pk]",
        cascade="all, delete-orphan",
    )


observation_record_association = sa.Table(
    "observation_record_association",
    Base.metadata,
    sa.Column("observation_pk", sa.Integer, sa.ForeignKey("observation.pk")),
    sa.Column("record_pk", sa.Integer, sa.ForeignKey("record.pk")),
)


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


class Observation(Base, MetadataField):
    __tablename__ = "observation"
    __table_args__ = (
        sa.UniqueConstraint("name", "experiment_pk", name="uq_observation_name"),
    )

    pk = sa.Column(sa.Integer, primary_key=True)
    id = sa.Column(UUID, unique=True, default=uuid4, nullable=False)
    time_created = sa.Column(sa.DateTime, server_default=func.now())
    time_updated = sa.Column(
        sa.DateTime, server_default=func.now(), onupdate=func.now()
    )
    name = sa.Column(sa.String, nullable=False)
    x_axis = sa.Column(StringArray, nullable=False)
    values = sa.Column(FloatArray, nullable=False)
    errors = sa.Column(FloatArray, nullable=False)

    records = relationship(
        "Record",
        secondary=observation_record_association,
        back_populates="observations",
    )
    experiment_pk = sa.Column(
        sa.Integer, sa.ForeignKey("experiment.pk"), nullable=False
    )
    experiment = relationship("Experiment")


class ObservationTransformation(Base):
    __tablename__ = "observation_transformation"

    pk = sa.Column(sa.Integer, primary_key=True)
    id = sa.Column(UUID, unique=True, default=uuid4, nullable=False)
    active_list = sa.Column(sa.PickleType, nullable=False)
    scale_list = sa.Column(sa.PickleType, nullable=False)

    observation_pk = sa.Column(
        sa.Integer, sa.ForeignKey("observation.pk"), nullable=False
    )
    observation = relationship("Observation")

    update_pk = sa.Column(sa.Integer, sa.ForeignKey("update.pk"), nullable=False)
    update = relationship("Update", back_populates="observation_transformations")


class Update(Base):
    __tablename__ = "update"
    __table_args__ = (
        sa.UniqueConstraint("ensemble_result_pk", name="uq_update_result_pk"),
    )

    pk = sa.Column(sa.Integer, primary_key=True)
    id = sa.Column(UUID, unique=True, default=uuid4, nullable=False)
    algorithm = sa.Column(sa.String, nullable=False)
    ensemble_reference_pk = sa.Column(
        sa.Integer, sa.ForeignKey("ensemble.pk"), nullable=True
    )
    ensemble_result_pk = sa.Column(
        sa.Integer, sa.ForeignKey("ensemble.pk"), nullable=True
    )

    ensemble_reference = relationship(
        "Ensemble",
        foreign_keys=[ensemble_reference_pk],
        back_populates="children",
    )
    ensemble_result = relationship(
        "Ensemble",
        foreign_keys=[ensemble_result_pk],
        uselist=False,
        back_populates="parent",
    )
    observation_transformations = relationship(
        "ObservationTransformation",
        foreign_keys="[ObservationTransformation.update_pk]",
        cascade="all, delete-orphan",
    )
