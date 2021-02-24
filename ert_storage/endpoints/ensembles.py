from fastapi import APIRouter, Depends
from ert_storage.database import Session, get_db
from ert_storage import database_schema as ds, json_schema as js


router = APIRouter(tags=["ensemble"])


@router.post("/ensembles", response_model=js.EnsembleOut)
def post_ensemble(
    *, db: Session = Depends(get_db), ensemble_in: js.EnsembleIn
) -> js.EnsembleOut:
    ens = ds.Ensemble(
        num_realizations=len(ensemble_in.parameters),
        parameters=ensemble_in.parameters,
    )
    db.add(ens)
    db.commit()

    return ens
