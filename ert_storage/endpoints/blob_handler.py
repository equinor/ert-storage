from typing import Optional, List
from fastapi import UploadFile, Request
from uuid import uuid4, UUID

from ert_storage.database import HAS_AZURE_BLOB_STORAGE
from ert_storage import database_schema as ds
from ert_storage.database import Session

if HAS_AZURE_BLOB_STORAGE:
    from ert_storage.database import azure_blob_container


class GeneralBlobHandler:
    def __init__(
        self,
        db: Session,
        name: str,
        ensemble_id: UUID,
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


def get_handler(
    db: Session, name: str, ensemble_id: UUID, realization_index: Optional[int]
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
