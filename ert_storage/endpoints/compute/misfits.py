import numpy as np
import pandas as pd
from uuid import UUID
from typing import Any, Optional, List
import sqlalchemy as sa
from fastapi.responses import Response
from fastapi import APIRouter, Depends, HTTPException, status
from ert_storage.database import Session, get_db
from ert_storage import database_schema as ds, json_schema as js
from ert_storage.compute import calculate_misfits_from_pandas, misfits

router = APIRouter(tags=["misfits"])


@router.get(
    "/compute/misfits",
    responses={
        status.HTTP_200_OK: {
            "content": {"application/x-dataframe": {}},
            "description": "Return misfits as csv, where columns are realizations.",
        }
    },
)
async def get_response_misfits(
    *,
    db: Session = Depends(get_db),
    ensemble_id: UUID,
    response_name: str,
    realization_index: Optional[int] = None,
    summary_misfits: bool = False,
) -> Response:
    """
    Compute univariate misfits for response(s)
    """

    ensemble = db.query(ds.Ensemble).filter_by(id=ensemble_id).one()
    reponse_query = (
        db.query(ds.Record)
        .filter_by(
            ensemble_pk=ensemble.pk,
            name=response_name,
            _record_type=1,
        )
        .filter(ds.Record.observations != None)
    )
    if realization_index is not None:
        responses = [reponse_query.filter_by(realization_index=realization_index).one()]
    else:
        responses = reponse_query.all()

    observation_df = None
    response_dict = {}
    for response in responses:
        data_df = pd.DataFrame(response.f64_matrix.content)
        labels = response.f64_matrix.labels
        if labels is not None:
            data_df.columns = labels[0]
            data_df.index = labels[1]
        response_dict[response.realization_index] = data_df.copy()
        if observation_df is None:
            # currently we expect only a single observation object, while
            # later in the future this might change
            obs = response.observations[0]
            observation_df = pd.DataFrame(
                data={"values": obs.values, "errors": obs.errors}, index=obs.x_axis
            )

    try:
        result_df = calculate_misfits_from_pandas(
            response_dict, observation_df, summary_misfits
        )
    except Exception as misfits_exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": f"Unable to compute misfits: {misfits_exc}",
                "name": response_name,
                "ensemble_id": str(ensemble_id),
            },
        )
    return Response(
        content=result_df.to_csv().encode(),
        media_type="application/x-dataframe",
    )
