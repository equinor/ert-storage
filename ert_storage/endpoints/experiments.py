from fastapi import APIRouter, Depends
from ert_storage.database import Session, get_db
from ert_storage import database_schema as ds, json_schema as js
from typing import Any, Mapping, Optional, List


router = APIRouter(tags=["experiment"])


@router.get("/experiments", response_model=List[js.ExperimentOut])
def get_experiments(
    *,
    db: Session = Depends(get_db),
) -> List[js.ExperimentOut]:
    return [
        js.ExperimentOut(
            id=exp.id, name=exp.name, ensembles=[ens.id for ens in exp.ensembles]
        )
        for exp in db.query(ds.Experiment).all()
    ]


@router.post("/experiments", response_model=js.ExperimentOut)
def post_experiments(
    *,
    db: Session = Depends(get_db),
    ens_in: js.ExperimentIn,
) -> js.ExperimentOut:
    experiment = ds.Experiment(name=ens_in.name)
    db.add(experiment)
    db.commit()
    return experiment


@router.get(
    "/experiments/{experiment_id}/ensembles", response_model=List[js.EnsembleOut]
)
def get_experiment_ensembles(
    *, db: Session = Depends(get_db), experiment_id: int
) -> List[js.EnsembleOut]:
    experiment = db.query(ds.Experiment).get(experiment_id)
    return experiment.ensembles
