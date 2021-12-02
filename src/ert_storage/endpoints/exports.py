from uuid import uuid4, UUID
from typing import Dict,List, Optional

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
            "description": "Exports emsemble responses as csv",
        }
    },
)
async def get_eclipse_summary_vectors(
    *,
    db: Session = Depends(get_db),
    ensemble_id: UUID,
    column_list: Optional[List[str]] = Query(None)
) -> Response:
    """
    Export responses for an ensemble.
    """

    ensemble = db.query(ds.Ensemble).filter_by(id=ensemble_id).one()

    # Base record info filter
    filter = [
        ds.RecordInfo.ensemble_pk == ensemble.pk,
        ds.RecordInfo.record_class == ds.RecordClass.response,
    ]

    # Add column name filter
    if column_list is not None:
        # Maybe only use LIKE when wildcards are actually present
        # And use = for explicit names to make resulting query more efficent
        filter_group = [
            ds.RecordInfo.name.like(x.replace("*", "%").replace("?", "_"))
            for x in column_list
        ]

        filter.append(or_(*filter_group))

    records = (
        db.query(ds.Record)
        .filter(ds.Record.realization_index != None)
        .join(ds.RecordInfo)
        .filter(and_(*filter))
    ).all()

    if len(records) == 0:
        return Response(content="No data found", status_code=status.HTTP_404_NOT_FOUND)

    # Flatten data into required shape
    # May be more efficent to do this as part of query

    # Keep track of columns so they can be appended
    column_map: dict[str,DataFrame] = {}

    for record in records:
        labels = record.f64_matrix.labels
        data = {
            "REAL": record.realization_index,
            "DATE": labels[0],
            record.record_info.name: record.f64_matrix.content[0],
        }
        data_frame = pd.DataFrame(data)
        column_name = record.record_info.name
        if column_name in column_map:
            column_map[column_name] = column_map[column_name].append(
                data_frame, ignore_index=True
            )
        else:
            column_map[column_name] = data_frame

    # Index
    data_frame_list = [df.set_index(["REAL", "DATE"]) for df in column_map.values()]
    return Response(
        content=pd.concat(data_frame_list, axis=1, join="outer").to_csv(index=True),
        media_type="text/csv",
    )
