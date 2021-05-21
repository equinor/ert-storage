import io
from typing import Optional, List, AsyncGenerator
from uuid import uuid4, UUID

import numpy as np
import pandas as pd
from fastapi import (
    Request,
    UploadFile,
)
from fastapi.logger import logger
from fastapi.responses import Response, StreamingResponse

from ert_storage import database_schema as ds
from ert_storage.database import Session, HAS_AZURE_BLOB_STORAGE

if HAS_AZURE_BLOB_STORAGE:
    from ert_storage.database import azure_blob_container


class GeneralBlobHandler:
    def __init__(
        self,
        db: Session,
        name: Optional[str],
        ensemble_id: Optional[UUID],
        realization_index: Optional[int],
    ):
        self._db = db
        self._name = name
        self._ensemble_id = ensemble_id
        self._realization_index = realization_index

    async def upload_blob(
        self,
        file: UploadFile,
    ) -> ds.File:
        file_obj = ds.File(
            filename=file.filename,
            mimetype=file.content_type,
        )
        file_obj.content = await file.read()

        return file_obj

    async def stage_blob(
        self,
        request: Request,
        block_index: int,
    ) -> ds.FileBlock:
        ensemble = self._db.query(ds.Ensemble).filter_by(id=self._ensemble_id).one()
        block_id = str(uuid4())

        file_block_obj = ds.FileBlock(
            ensemble=ensemble,
            block_id=block_id,
            block_index=block_index,
            record_name=self._name,
            realization_index=self._realization_index,
        )
        file_block_obj.content = await request.body()

        return file_block_obj

    def create_blob(self) -> ds.File:
        file_obj = ds.File(
            filename="test",
            mimetype="mime/type",
        )

        return file_obj

    async def finalize_blob(self) -> None:
        ensemble = self._db.query(ds.Ensemble).filter_by(id=self._ensemble_id).one()

        record_obj = self._get_record(
            ensemble_pk=ensemble.pk,
        )

        submitted_blocks = self._get_submitted_blocks(
            ensemble_pk=ensemble.pk,
        )

        data = b"".join([block.content for block in submitted_blocks])
        record_obj.file.content = data

    async def extract_content(
        self, record: ds.Record, accept: Optional[str], realization_index: Optional[int]
    ) -> Response:
        type_ = record.record_info.record_type
        if type_ == ds.RecordType.f64_matrix:
            if realization_index is None:
                content = record.f64_matrix.content
            else:
                content = record.f64_matrix.content[realization_index]

            if accept == "application/x-numpy":
                return self._wrap_x_numpy(content=content)
            elif accept == "text/csv":
                return self._wrap_csv(
                    record=record, content=content, realization_index=realization_index
                )
            elif accept == "application/x-dataframe":
                logger.warning(
                    "Accept with 'application/x-dataframe' is deprecated. Use 'text/csv' instead."
                )
                return self._wrap_csv(
                    record=record, content=content, realization_index=realization_index
                )

            return content

        if type_ == ds.RecordType.file:
            file = record.file
            if file.content is not None:
                return self._wrap_file(file=file)
            elif self._is_azure_content(file=file):
                return await self._wrap_blob(file=file)

        raise NotImplementedError(
            f"Getting record data for type {type_} and Accept header {accept} not implemented"
        )

    async def _wrap_blob(self, file: ds.File) -> Response:
        raise Exception("Azure blob storage not configured")

    def _wrap_file(self, file: ds.File) -> Response:
        return Response(
            content=file.content,
            media_type=file.mimetype,
            headers={"Content-Disposition": f'attachment; filename="{file.filename}"'},
        )

    def _wrap_csv(
        self, record: ds.Record, content: ds.F64Matrix, realization_index: Optional[int]
    ) -> Response:
        data = pd.DataFrame(content)
        labels = record.f64_matrix.labels
        if labels is not None and realization_index is None:
            data.columns = labels[0]
            data.index = labels[1]
        elif labels is not None and realization_index is not None:
            # The output is such that rows are realizations. Because
            # `content` is a 1d list in this case, it treats each element as
            # its own row. We transpose the data so that all of the data
            # falls on the same row.
            data = data.T
            data.columns = labels[0]
            data.index = [realization_index]

        return Response(
            content=data.to_csv().encode(),
            media_type="text/csv",
        )

    def _wrap_x_numpy(self, content: ds.F64Matrix) -> Response:
        from numpy.lib.format import write_array

        stream = io.BytesIO()
        write_array(stream, np.array(content))

        return Response(
            content=stream.getvalue(),
            media_type="application/x-numpy",
        )

    def _is_azure_content(self, file: ds.File) -> bool:
        return file.az_container is not None and file.az_blob is not None

    def _get_record(self, ensemble_pk: int) -> ds.Record:
        return (
            self._db.query(ds.Record)
            .filter_by(realization_index=self._realization_index)
            .join(ds.RecordInfo)
            .filter_by(ensemble_pk=ensemble_pk, name=self._name)
            .one()
        )

    def _get_submitted_blocks(self, ensemble_pk: int) -> List[ds.FileBlock]:
        return list(
            self._db.query(ds.FileBlock)
            .filter_by(
                record_name=self._name,
                ensemble_pk=ensemble_pk,
                realization_index=self._realization_index,
            )
            .all()
        )


class AzureBlobHandler(GeneralBlobHandler):
    async def upload_blob(
        self,
        file: UploadFile,
    ) -> ds.File:
        file_obj = ds.File(
            filename=file.filename,
            mimetype=file.content_type,
        )
        key = f"{self._name}@{self._realization_index}@{uuid4()}"
        blob = azure_blob_container.get_blob_client(key)
        await blob.upload_blob(file.file)

        file_obj.az_container = azure_blob_container.container_name
        file_obj.az_blob = key

        return file_obj

    async def stage_blob(
        self,
        request: Request,
        block_index: int,
    ) -> ds.FileBlock:
        ensemble = self._db.query(ds.Ensemble).filter_by(id=self._ensemble_id).one()

        record_obj = self._get_record(
            ensemble_pk=ensemble.pk,
        )

        key = record_obj.file.az_blob
        blob = azure_blob_container.get_blob_client(key)

        block_id = str(uuid4())
        await blob.stage_block(block_id, await request.body())

        file_block_obj = ds.FileBlock(
            ensemble=ensemble,
            block_id=block_id,
            block_index=block_index,
            record_name=self._name,
            realization_index=self._realization_index,
        )
        return file_block_obj

    def create_blob(self) -> ds.File:
        key = f"{self._name}@{self._realization_index}@{uuid4()}"
        blob = azure_blob_container.get_blob_client(key)

        file_obj = ds.File(
            filename="test",
            mimetype="mime/type",
        )
        file_obj.az_container = (azure_blob_container.container_name,)
        file_obj.az_blob = (key,)

        return file_obj

    async def finalize_blob(self) -> None:
        ensemble = self._db.query(ds.Ensemble).filter_by(id=self._ensemble_id).one()

        record_obj = self._get_record(
            ensemble_pk=ensemble.pk,
        )

        submitted_blocks = self._get_submitted_blocks(
            ensemble_pk=ensemble.pk,
        )

        key = record_obj.file.az_blob
        blob = azure_blob_container.get_blob_client(key)
        block_ids = [
            block.block_id
            for block in sorted(submitted_blocks, key=lambda x: x.block_index)
        ]
        await blob.commit_block_list(block_ids)

    async def _wrap_blob(self, file: ds.File) -> Response:
        blob = azure_blob_container.get_blob_client(file.az_blob)
        download = await blob.download_blob()

        async def chunk_generator() -> AsyncGenerator[bytes, None]:
            async for chunk in download.chunks():
                yield chunk

        return StreamingResponse(
            chunk_generator(),
            media_type=file.mimetype,
            headers={"Content-Disposition": f'attachment; filename="{file.filename}"'},
        )


def get_handler(
    db: Session,
    name: Optional[str],
    ensemble_id: Optional[UUID],
    realization_index: Optional[int],
) -> GeneralBlobHandler:
    if HAS_AZURE_BLOB_STORAGE:
        return AzureBlobHandler(
            db=db,
            name=name,
            ensemble_id=ensemble_id,
            realization_index=realization_index,
        )
    return GeneralBlobHandler(
        db=db, name=name, ensemble_id=ensemble_id, realization_index=realization_index
    )
