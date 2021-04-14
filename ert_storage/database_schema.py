from enum import Enum
from typing import Any, Mapping, Optional

import sqlalchemy as sa
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ert_storage.database import Base

from ert_storage.ext.sqlalchemy_arrays import StringArray, FloatArray


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

    id = sa.Column(sa.Integer, primary_key=True)
    time_created = sa.Column(sa.DateTime, server_default=func.now())
    time_updated = sa.Column(
        sa.DateTime, server_default=func.now(), onupdate=func.now()
    )
    inputs = sa.Column(StringArray)
    records = relationship(
        "Record", foreign_keys="[Record.ensemble_id]", cascade="all, delete-orphan"
    )
    experiment_id = sa.Column(
        sa.Integer, sa.ForeignKey("experiment.id"), nullable=False
    )
    experiment = relationship("Experiment", back_populates="ensembles")
    children = relationship(
        "Update",
        foreign_keys="[Update.ensemble_reference_id]",
    )
    parent = relationship(
        "Update",
        uselist=False,
        foreign_keys="[Update.ensemble_result_id]",
        cascade="all, delete-orphan",
    )


class Experiment(Base, MetadataField):
    __tablename__ = "experiment"

    id = sa.Column(sa.Integer, primary_key=True)
    time_created = sa.Column(sa.DateTime, server_default=func.now())
    time_updated = sa.Column(
        sa.DateTime, server_default=func.now(), onupdate=func.now()
    )
    name = sa.Column(sa.String)
    ensembles = relationship(
        "Ensemble",
        foreign_keys="[Ensemble.experiment_id]",
        cascade="all, delete-orphan",
    )
    observations = relationship(
        "Observation",
        foreign_keys="[Observation.experiment_id]",
        cascade="all, delete-orphan",
    )


observation_record_association = sa.Table(
    "observation_record_association",
    Base.metadata,
    sa.Column("observation_id", sa.Integer, sa.ForeignKey("observation.id")),
    sa.Column("record_id", sa.Integer, sa.ForeignKey("record.id")),
)


class Record(Base, MetadataField):
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

    file = relationship("File", cascade="all")
    f64_matrix = relationship("F64Matrix", cascade="all")
    ensemble_id = sa.Column(sa.Integer, sa.ForeignKey("ensemble.id"), nullable=True)
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


class FileBlock(Base):
    __tablename__ = "file_block"
    id = sa.Column(sa.Integer, primary_key=True)
    time_created = sa.Column(sa.DateTime, server_default=func.now())
    time_updated = sa.Column(
        sa.DateTime, server_default=func.now(), onupdate=func.now()
    )
    block_id = sa.Column(sa.String, nullable=False)
    block_index = sa.Column(sa.Integer, nullable=False)
    record_name = sa.Column(sa.String, nullable=False)
    realization_index = sa.Column(sa.Integer, nullable=True)
    ensemble_id = sa.Column(sa.Integer, sa.ForeignKey("ensemble.id"), nullable=True)
    ensemble = relationship("Ensemble")
    content = sa.Column(sa.LargeBinary, nullable=True)


class Observation(Base, MetadataField):
    __tablename__ = "observation"
    __table_args__ = (sa.UniqueConstraint("name", name="uq_observation_name"),)

    id = sa.Column(sa.Integer, primary_key=True)
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
    experiment_id = sa.Column(
        sa.Integer, sa.ForeignKey("experiment.id"), nullable=False
    )
    experiment = relationship("Experiment")


class ObservationTransformation(Base):
    __tablename__ = "observation_transformation"
    id = sa.Column(sa.Integer, primary_key=True)
    active_list = sa.Column(sa.PickleType, nullable=False)
    scale_list = sa.Column(sa.PickleType, nullable=False)

    observation_id = sa.Column(
        sa.Integer, sa.ForeignKey("observation.id"), nullable=False
    )
    observation = relationship("Observation")

    update_id = sa.Column(sa.Integer, sa.ForeignKey("update.id"), nullable=False)
    update = relationship("Update", back_populates="observation_transformations")


class Update(Base):
    __tablename__ = "update"
    __table_args__ = (
        sa.UniqueConstraint("ensemble_result_id", name="uq_update_result_id"),
    )

    id = sa.Column(sa.Integer, primary_key=True)
    algorithm = sa.Column(sa.String, nullable=False)
    ensemble_reference_id = sa.Column(
        sa.Integer, sa.ForeignKey("ensemble.id"), nullable=True
    )
    ensemble_result_id = sa.Column(
        sa.Integer, sa.ForeignKey("ensemble.id"), nullable=True
    )

    ensemble_reference = relationship(
        "Ensemble",
        foreign_keys=[ensemble_reference_id],
        back_populates="children",
    )
    ensemble_result = relationship(
        "Ensemble",
        foreign_keys=[ensemble_result_id],
        uselist=False,
        back_populates="parent",
    )
    observation_transformations = relationship(
        "ObservationTransformation",
        foreign_keys="[ObservationTransformation.update_id]",
        cascade="all, delete-orphan",
    )
