from fastapi import APIRouter, Depends, Body
from sqlalchemy.orm.attributes import flag_modified
from ert_storage.database import Session, get_db
from ert_storage import database_schema as ds, json_schema as js
from typing import Any, Mapping

router = APIRouter(tags=["ensemble"])


@router.post("/experiments/{experiment_id}/ensembles", response_model=js.EnsembleOut)
def post_ensemble(
    *, db: Session = Depends(get_db), ens_in: js.EnsembleIn, experiment_id: int
) -> js.EnsembleOut:

    experiment = db.query(ds.Experiment).get(experiment_id)
    ens = ds.Ensemble(inputs=ens_in.parameters, experiment=experiment)
    db.add(ens)

    if ens_in.update_id:
        update_obj = db.query(ds.Update).get(ens_in.update_id)
        update_obj.ensemble_result = ens
    db.commit()

    return js.EnsembleOut(
        id=ens.id,
        children=[child.ensemble_result_id for child in ens.children],
        parent=ens.parent.ensemble_reference_id if ens.parent else None,
    )


@router.get("/ensembles/{ensemble_id}", response_model=js.EnsembleOut)
def get_ensemble(*, db: Session = Depends(get_db), ensemble_id: int) -> js.EnsembleOut:
    ens = db.query(ds.Ensemble).get(ensemble_id)

    return js.EnsembleOut(
        id=ens.id,
        children=[child.ensemble_result_id for child in ens.children],
        parent=ens.parent.ensemble_reference_id if ens.parent else None,
    )


@router.put("/ensembles/{ensemble_id}/metadata")
async def replace_ensemble_metadata(
    *,
    db: Session = Depends(get_db),
    ensemble_id: int,
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
    ensemble_id: int,
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
    ensemble_id: int,
) -> Mapping[str, Any]:
    """
    Get metadata json
    """
    ensemble = db.query(ds.Ensemble).filter_by(id=ensemble_id).one()
    return ensemble.metadata_dict
