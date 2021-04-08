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


@router.post("/ensembles/{id}/updates", response_model=js.UpdateOut)
def create_update(
    *,
    db: Session = Depends(get_db),
    id: int,
    update: js.UpdateIn,
) -> js.UpdateOut:

    update_obj = ds.Update(
        algorithm=update.algorithm,
        ensemble_reference_id=update.ensemble_reference_id,
    )
    db.add(update_obj)
    transformations = (
        update.observation_transformations if update.observation_transformations else []
    )
    observation_ids = [trans.observation_id for trans in transformations]
    observations = (
        db.query(ds.Observation).filter(ds.Observation.id.in_(observation_ids)).all()
    )

    observation_transformations = [
        ds.ObservationTransformation(
            active_list=observation_transformation.active,
            scale_list=observation_transformation.scale,
            observation=observation,
            update=update_obj,
        )
        for observation_transformation, observation in zip(
            transformations, observations
        )
    ]

    db.add_all(observation_transformations)
    db.commit()
    return update_obj
