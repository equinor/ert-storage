import json
from enum import Enum
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, Header, Request, HTTPException
from sqlalchemy.orm.exc import NoResultFound
from ert_storage.database import Session, get_db
from ert_storage import database_schema as ds, json_schema as js


router = APIRouter(tags=["record"])


class RecordType(str, Enum):
    parameters = "parameters"
    float_vector = "float_vector"
    file = "file"


@router.get("/ensembles/{ensemble_id}/records", response_model=List[str])
async def list_records(*, db: Session = Depends(get_db), ensemble_id: int) -> List[str]:
    return [
        rec.name
        for rec in (
            db.query(ds.Record.name)
            .filter_by(ensemble_id=ensemble_id, realization_index=None)
            .all()
        )
    ]


@router.get("/ensembles/{ensemble_id}/records/{name}")
async def get_ensemble_record(
    *, db: Session = Depends(get_db), ensemble_id: int, name: str
) -> Any:
    try:
        bundle = (
            db.query(ds.Record)
            .filter_by(ensemble_id=ensemble_id, name=name, realization_index=None)
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

    type_ = bundle.record_type
    if type_ == ds.RecordType.parameters:
        return bundle.ensemble.parameters
    if type_ == ds.RecordType.float_vector:
        return bundle.data
    if type_ == ds.RecordType.file:
        pass


@router.post("/ensembles/{ensemble_id}/records/{name}")
async def post_ensemble_record(
    *,
    db: Session = Depends(get_db),
    ensemble_id: int,
    name: str,
    recordtype: Optional[RecordType] = Header(None),
    is_response: bool = Header(False),
    request: Request,
) -> None:
    if recordtype is None:
        recordtype = RecordType.file

    # Check that no record with the given name exists
    if (
        db.query(ds.Record)
        .filter_by(ensemble_id=ensemble_id, name=name, realization_index=None)
        .count()
        > 0
    ):
        raise HTTPException(
            status_code=404,
            detail={
                "error": f"Ensemble-wide record '{name}' for ensemble '{ensemble_id}' already exists",
                "name": name,
                "ensemble_id": ensemble_id,
            },
        )

    # Check that the ensemble exists and is valid
    ensemble = db.query(ds.Ensemble).filter_by(id=ensemble_id).one()

    record_type = ds.RecordType.from_str(recordtype.value)
    content: Any = b"-"
    if record_type is ds.RecordType.file:
        pass
    elif record_type == ds.RecordType.float_vector:
        try:
            content = [float(x) for x in json.loads(await request.body())]
        except ValueError:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": f"Ensemble-wide record '{name}' for ensemble '{ensemble_id}' needs to contain numbers only!",
                    "name": name,
                    "ensemble_id": ensemble_id,
                },
            )
    elif record_type == ds.RecordType.parameters:
        pass

    record = ds.Record(
        ensemble=ensemble,
        name=name,
        _record_type=record_type.value,
        is_response=is_response,
        data=content,
    )
    db.add(record)
    db.commit()


@router.get("/ensembles/{ensemble_id}/records/{name}/{realization_index}")
async def get_realization_record(
    *,
    db: Session = Depends(get_db),
    ensemble_id: int,
    realization_index: int,
    name: str,
) -> Any:
    try:
        bundle = (
            db.query(ds.Record)
            .filter_by(
                ensemble_id=ensemble_id, name=name, realization_index=realization_index
            )
            .one()
        )
    except NoResultFound:
        try:
            bundle = (
                db.query(ds.Record)
                .filter_by(ensemble_id=ensemble_id, name=name, realization_index=None)
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

    type_ = bundle.record_type
    if type_ == ds.RecordType.parameters:
        return bundle.ensemble.parameters[realization_index]
    if type_ == ds.RecordType.float_vector:
        return bundle.data
    if type_ == ds.RecordType.file:
        pass


@router.post("/ensembles/{ensemble_id}/records/{name}/{realization_index}")
async def post_realization_record(
    *,
    db: Session = Depends(get_db),
    ensemble_id: int,
    name: str,
    realization_index: Optional[int] = None,
    record_type: str = Header("file"),
    response: str = Header("false"),
) -> None:
    pass
