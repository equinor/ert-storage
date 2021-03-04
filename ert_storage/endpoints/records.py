import numpy as np
from urllib.parse import quote_plus
from enum import Enum
from typing import Any, Mapping, Optional, List
import sqlalchemy as sa
from fastapi import (
    APIRouter,
    Body,
    Depends,
    File,
    HTTPException,
    Header,
    Query,
    Request,
    Response,
    UploadFile,
    status,
)
from pydantic import BaseModel
from sqlalchemy.orm.exc import NoResultFound
from ert_storage.database import Session, get_db
from ert_storage import database_schema as ds, json_schema as js


router = APIRouter(tags=["record"])


class ListRecords(BaseModel):
    ensemble: Mapping[str, Mapping[str, str]]
    forward_model: Mapping[str, Mapping[str, str]]


@router.get("/ensembles/{ensemble_id}/records", response_model=ListRecords)
async def list_records(
    *, db: Session = Depends(get_db), ensemble_id: int
) -> ListRecords:
    types = {
        1: "matrix",
        2: "file",
    }

    return ListRecords(
        ensemble=dict(
            consuming={
                rec.name: types[rec._record_type]
                for rec in (
                    db.query(ds.Record)
                    .filter_by(consumer_id=ensemble_id)
                    .filter(ds.Record.realization_index == None)
                    .all()
                )
            },
            producing={
                rec.name: types[rec._record_type]
                for rec in (
                    db.query(ds.Record)
                    .filter_by(producer_id=ensemble_id)
                    .filter(ds.Record.realization_index == None)
                    .all()
                )
            },
        ),
        forward_model=dict(
            consuming={
                rec.name: types[rec._record_type]
                for rec in (
                    db.query(ds.Record)
                    .filter_by(consumer_id=ensemble_id)
                    .filter(ds.Record.realization_index != None)
                    .all()
                )
            },
            producing={
                rec.name: types[rec._record_type]
                for rec in (
                    db.query(ds.Record)
                    .filter_by(producer_id=ensemble_id)
                    .filter(ds.Record.realization_index != None)
                    .all()
                )
            },
        ),
    )


@router.post("/ensembles/{ensemble_id}/records/{name}/file")
async def post_ensemble_record_file(
    *,
    db: Session = Depends(get_db),
    ensemble_id: int,
    name: str,
    realization_index: Optional[int] = None,
    record_class: ds.RecordClass = ds.RecordClass.normal,
    file: UploadFile = File(...),
) -> None:
    """
    Assign an arbitrary file to the given `name` record.
    """
    ensemble = _get_and_assert_ensemble(db, ensemble_id, name, realization_index)

    file_obj = ds.File(
        content=await file.read(),
        filename=file.filename,
        mimetype=file.content_type,
    )
    db.add(file_obj)
    record_obj = ds.Record(
        name=name,
        record_type=ds.RecordType.file,
        realization_index=realization_index,
        record_class=record_class,
        file=file_obj,
    )

    if record_class == ds.RecordClass.parameter:
        record_obj.consumer = ensemble
    else:
        record_obj.producer = ensemble
    db.add(record_obj)


@router.post("/ensembles/{ensemble_id}/records/{name}/matrix")
async def post_ensemble_record_matrix(
    *,
    db: Session = Depends(get_db),
    ensemble_id: int,
    name: str,
    realization_index: Optional[int] = None,
    record_class: ds.RecordClass = ds.RecordClass.normal,
    body: Any = Body(...),
) -> None:
    """
    Assign an n-dimensional float matrix, encoded in JSON, to the given `name` record.
    """
    ensemble = _get_and_assert_ensemble(db, ensemble_id, name, realization_index)

    try:
        content = np.array(body, dtype=np.float64)
    except ValueError:
        if realization_index is None:
            message = f"Ensemble-wide record '{name}' for ensemble '{ensemble_id}' needs to be a matrix"
        else:
            message = f"Forward-model record '{name}' for ensemble '{ensemble_id}', realization {realization_index} needs to be a matrix"

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": message,
                "name": name,
                "ensemble_id": ensemble_id,
                "realization_index": realization_index,
            },
        )

    matrix_obj = ds.F64Matrix(
        content=content.tolist(),
    )
    db.add(matrix_obj)

    record_obj = ds.Record(
        name=name,
        record_type=ds.RecordType.float_vector,
        record_class=record_class,
        f64_matrix=matrix_obj,
        realization_index=realization_index,
    )
    if record_class == ds.RecordClass.parameter:
        record_obj.consumer = ensemble
    else:
        record_obj.producer = ensemble
    db.add(record_obj)


@router.get("/ensembles/{ensemble_id}/records/{name}")
async def get_record(
    *,
    db: Session = Depends(get_db),
    ensemble_id: int,
    realization_index: Optional[int] = None,
    name: str,
) -> Any:
    """
    Get record with a given `name`. If `realization_index` is not set, look for
    the ensemble-wide record. If it is set, look first for one created by a
    forward-model for the given realization index and then the ensemble-wide
    record.

    Records support multiple data formats. In particular:
    - Matrix:
      Will return n-dimensional float matrix, where n is arbitrary.
    - File:
      Will return the file that was uploaded.
    """
    if realization_index is None:
        bundle = _get_ensemble_record(db, ensemble_id, name)
    else:
        bundle = _get_forward_model_record(db, ensemble_id, name, realization_index)

    type_ = bundle.record_type
    if type_ == ds.RecordType.float_vector:
        return bundle.f64_matrix.content
    if type_ == ds.RecordType.file:
        f = bundle.file
        return Response(
            content=f.content,
            media_type=f.mimetype,
            headers={"Content-Disposition": f'attachment; filename="{f.filename}"'},
        )


def _get_ensemble_record(db: Session, ensemble_id: int, name: str) -> ds.Record:
    try:
        return (
            db.query(ds.Record)
            .filter(
                sa.and_(
                    sa.or_(
                        ds.Record.producer_id == ensemble_id,
                        ds.Record.consumer_id == ensemble_id,
                    ),
                    ds.Record.name == name,
                    ds.Record.realization_index == None,
                )
            )
            .one()
        )
    except NoResultFound:
        raise HTTPException(
            status_code=404,
            detail={
                "error": f"Ensemble-wide record '{name}' for ensemble '{ensemble_id}' not found!",
                "name": name,
                "ensemble_id": ensemble_id,
            },
        )


def _get_forward_model_record(
    db: Session, ensemble_id: int, name: str, realization_index: int
) -> ds.Record:
    try:
        return (
            db.query(ds.Record)
            .filter(
                sa.and_(
                    sa.or_(
                        ds.Record.producer_id == ensemble_id,
                        ds.Record.consumer_id == ensemble_id,
                    ),
                    ds.Record.name == name,
                    ds.Record.realization_index == realization_index,
                )
            )
            .one()
        )
    except NoResultFound:
        raise HTTPException(
            status_code=404,
            detail={
                "error": f"Forward-model record '{name}' for ensemble '{ensemble_id}', realization {realization_index} not found!",
                "name": name,
                "ensemble_id": ensemble_id,
            },
        )


def _get_and_assert_ensemble(
    db: Session, ensemble_id: int, name: str, realization_index: Optional[int]
) -> ds.Ensemble:
    """
    Get ensemble and verify that no record with the name `name` exists
    """
    ensemble = db.query(ds.Ensemble).filter_by(id=ensemble_id).one()

    q = db.query(ds.Record).filter_by(producer_id=ensemble_id, name=name)
    if realization_index is not None:
        q = q.filter(
            (ds.Record.realization_index == None)
            | (ds.Record.realization_index == realization_index)
        )

    if q.count() > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": f"Ensemble-wide record '{name}' for ensemble '{ensemble_id}' already exists",
                "name": name,
                "ensemble_id": ensemble_id,
            },
        )

    return ensemble


@router.get(
    "/ensembles/{ensemble_id}/input_records", response_model=Mapping[str, js.RecordOut]
)
def get_ensemble_parameters(
    *, db: Session = Depends(get_db), ensemble_id: int
) -> Mapping[str, js.RecordOut]:
    ensemble = db.query(ds.Ensemble).get(ensemble_id)
    return {rec.name: rec for rec in ensemble.inputs}


@router.get(
    "/ensembles/{ensemble_id}/output_records", response_model=Mapping[str, js.RecordOut]
)
def get_ensemble_records(
    *, db: Session = Depends(get_db), ensemble_id: int
) -> Mapping[str, js.RecordOut]:
    ensemble = db.query(ds.Ensemble).get(ensemble_id)
    return {
        rec.name: js.RecordOut(id=rec.id, name=rec.name, data=rec.data)
        for rec in ensemble.outputs
    }
