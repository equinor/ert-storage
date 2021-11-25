from uuid import uuid4, UUID
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import Response
import pandas as pd
from pandas.core.frame import DataFrame
from sqlalchemy import and_, or_
from ert_storage.database import Session, get_db
from ert_storage import database_schema as ds


router = APIRouter(tags=["exports"])


@router.get(
    "/ensembles/{ensemble_id}/export/csv",
    responses={
        status.HTTP_200_OK: {
            "content": {"text/csv": {}},
            "description": "Exports csv, where...",
        }
    },
)
async def get_eclipse_summary_vectors(
        *,
        db: Session = Depends(get_db),
        ensemble_id: UUID,
        frequency: Optional[str] = None,
        column_list: Optional[List[str]] = Query(None)

) -> Response:
    # TODO - Preflight checks

    ensemble = db.query(ds.Ensemble).filter_by(id=ensemble_id).one()

    # Base record info filter
    filter =[ds.RecordInfo.ensemble_pk == ensemble.pk,
             ds.RecordInfo.record_class == ds.RecordClass.response]

    # Add column name filter 
    if column_list is not None:
        # Maybe only use LIKE when wildcards are actually present
        # And use = for explicit names to make resulting query more efficent
        filter_group = [ds.RecordInfo.name.like(x.replace("*", "%")
                                                .replace("?", "_"))
                        for x in column_list]
        filter.append(or_(*filter_group))

    records = (
        db.query(ds.Record)
        .filter(ds.Record.realization_index != None)
        .join(ds.RecordInfo)
        .filter(and_(*filter))
    ).all()

    # May be more efficent to do this as part of query
    # TODO deal with frequency 
    df_list = []
    for record in records:
        labels = record.f64_matrix.labels
        data={"DATE": labels[0],
              "REAL": record.realization_index,
              record.record_info.name:record.f64_matrix.content[0]
        }
        data_df = pd.DataFrame(data)
        df_list.append(data_df.set_index(["DATE", "REAL"])
                       )
    # What to return if no columns match??

    return Response(
        content=pd.concat(df_list, axis=1, join="outer").to_csv(),
        media_type="text/csv",
    )
