from fastapi import APIRouter, Depends
from typing import List
from ert_storage.database import Session, get_db
from ert_storage import database_schema as ds, json_schema as js


router = APIRouter(tags=["ensemble"])


@router.post("/experiments/{experiment_id}/observations")
def post_observation(
    *, db: Session = Depends(get_db), obs_in: js.ObservationIn, experiment_id: int
) -> None:
    experiment = db.query(ds.Experiment).get(experiment_id)
    records = (
        [db.query(ds.Record).get(rec_id) for rec_id in obs_in.records]
        if obs_in.records is not None
        else []
    )
    obs = ds.Observation(
        name=obs_in.name,
        x_axis=obs_in.x_axis,
        errors=obs_in.errors,
        values=obs_in.values,
        experiment=experiment,
        records=records,
    )
    db.add(obs)
    db.commit()


@router.get(
    "/experiments/{experiment_id}/observations", response_model=List[js.ObservationOut]
)
def get_observations(
    *, db: Session = Depends(get_db), experiment_id: int
) -> List[js.ObservationOut]:
    experiment = db.query(ds.Experiment).get(experiment_id)
    return [
        js.ObservationOut(
            id=obs.id,
            name=obs.name,
            x_axis=obs.x_axis,
            errors=obs.errors,
            values=obs.values,
            records=[rec.id for rec in obs.records],
        )
        for obs in experiment.observations
    ]


@router.get(
    "/ensembles/{ensemble_id}/observations", response_model=List[js.ObservationOut]
)
def get_observations_with_transformation(
    *, db: Session = Depends(get_db), ensemble_id: int
) -> List[js.ObservationOut]:
    ens = db.query(ds.Ensemble).get(ensemble_id)
    experiment = ens.experiment
    update = ens.parent
    transformations = {
        trans.observation.name: trans for trans in update.observation_transformations
    }

    return [
        js.ObservationOut(
            id=obs.id,
            name=obs.name,
            x_axis=obs.x_axis,
            errors=obs.errors,
            values=obs.values,
            records=[rec.id for rec in obs.records],
            transformation=js.ObservationTransformationOut(
                id=transformations[obs.name].id,
                name=obs.name,
                observation_id=obs.id,
                scale=transformations[obs.name].scale_list,
                active=transformations[obs.name].active_list,
            )
            if obs.name in transformations
            else None,
        )
        for obs in experiment.observations
    ]
