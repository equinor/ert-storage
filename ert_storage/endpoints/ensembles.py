from fastapi import APIRouter, Depends
from ert_storage.database import Session, get_db
from ert_storage import database_schema as ds, json_schema as js


router = APIRouter(tags=["ensemble"])


@router.post("/experiments/{experiment_id}/ensembles", response_model=js.EnsembleOut)
def post_ensemble(
    *, db: Session = Depends(get_db), ens_in: js.EnsembleIn, experiment_id: int
) -> js.EnsembleOut:

    experiment = db.query(ds.Experiment).get(experiment_id)
    ens = ds.Ensemble(inputs=ens_in.parameters, experiment=experiment)
    db.add(ens)
    db.commit()
    return ens
