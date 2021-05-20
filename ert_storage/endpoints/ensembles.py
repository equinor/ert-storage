from uuid import UUID

from fastapi import APIRouter, Depends, Body
from sqlalchemy.orm.attributes import flag_modified
from ert_storage.database import Session, get_db
from ert_storage import database_schema as ds, json_schema as js
from typing import Any, Mapping

router = APIRouter(tags=["ensemble"])


@router.post("/experiments/{experiment_id}/ensembles", response_model=js.EnsembleOut)
def post_ensemble(
    *, db: Session = Depends(get_db), ens_in: js.EnsembleIn, experiment_id: UUID
) -> ds.Ensemble:

    experiment = db.query(ds.Experiment).filter_by(id=experiment_id).one()
    ens = ds.Ensemble(
        parameter_names=ens_in.parameter_names,
        response_names=ens_in.response_names,
        experiment=experiment,
        size=ens_in.size,
        _metadata=ens_in.metadata,
    )
    db.add(ens)

    if ens_in.update_id:
        update_obj = db.query(ds.Update).filter_by(id=ens_in.update_id).one()
        update_obj.ensemble_result = ens
    db.commit()

    return ens


@router.get("/ensembles/{ensemble_id}", response_model=js.EnsembleOut)
def get_ensemble(*, db: Session = Depends(get_db), ensemble_id: UUID) -> ds.Ensemble:
    return db.query(ds.Ensemble).filter_by(id=ensemble_id).one()


@router.put("/ensembles/{ensemble_id}/metadata")
async def replace_ensemble_metadata(
    *,
    db: Session = Depends(get_db),
    ensemble_id: UUID,
    body: Any = Body(...),
) -> None:
    """
    Assign new metadata json
    """
    ensemble = db.query(ds.Ensemble).filter_by(id=ensemble_id).one()
    ensemble._metadata = body
    db.commit()


@router.patch("/ensembles/{ensemble_id}/metadata")
async def patch_ensemble_metadata(
    *,
    db: Session = Depends(get_db),
    ensemble_id: UUID,
    body: Any = Body(...),
) -> None:
    """
    Update metadata json
    """
    ensemble = db.query(ds.Ensemble).filter_by(id=ensemble_id).one()
    ensemble._metadata.update(body)
    flag_modified(ensemble, "_metadata")
    db.commit()


@router.get("/ensembles/{ensemble_id}/metadata", response_model=Mapping[str, Any])
async def get_ensemble_metadata(
    *,
    db: Session = Depends(get_db),
    ensemble_id: UUID,
) -> Mapping[str, Any]:
    """
    Get metadata json
    """
    ensemble = db.query(ds.Ensemble).filter_by(id=ensemble_id).one()
    return ensemble.metadata_dict
