from fastapi import APIRouter, Depends
from ert_storage.database import Session, get_db
from ert_storage import database_schema as ds, json_schema as js

router = APIRouter(tags=["ensemble"])


@router.post("/updates", response_model=js.UpdateOut)
def create_update(
    *,
    db: Session = Depends(get_db),
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
