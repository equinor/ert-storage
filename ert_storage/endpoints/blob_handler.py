from typing import Optional, List
from fastapi import UploadFile, Request
from uuid import uuid4, UUID

from ert_storage.database import HAS_AZURE_BLOB_STORAGE
from ert_storage import database_schema as ds
from ert_storage.database import Session

if HAS_AZURE_BLOB_STORAGE:
    from ert_storage.database import azure_blob_container


class GeneralBlobHandler:
    async def upload_blob(
        self,
        file: UploadFile,
        name: str,
        realization_index: Optional[int],
    ) -> ds.File:
        file_obj = ds.File(
            filename=file.filename,
            mimetype=file.content_type,
        )
        file_obj.content = await file.read()

        return file_obj

    async def stage_blob(
        self,
        db: Session,
        ensemble_id: UUID,
        name: str,
        realization_index: Optional[int],
        request: Request,
        block_index: int,
    ) -> ds.FileBlock:
        ensemble = db.query(ds.Ensemble).filter_by(id=ensemble_id).one()
        block_id = str(uuid4())

        file_block_obj = ds.FileBlock(
            ensemble=ensemble,
            block_id=block_id,
            block_index=block_index,
            record_name=name,
            realization_index=realization_index,
        )
        file_block_obj.content = await request.body()

        return file_block_obj

    def create_blob(
        self, name: str, realization_index: Optional[int], file_obj: ds.File
    ) -> None:
        pass

    async def finalize_blob(
        self, record_obj: ds.Record, submitted_blocks: List[ds.FileBlock]
    ) -> None:
        data = b"".join([block.content for block in submitted_blocks])
        record_obj.file.content = data


class AzureBlobHandler(GeneralBlobHandler):
    async def upload_blob(
        self,
        file: UploadFile,
        name: str,
        realization_index: Optional[int],
    ) -> ds.File:
        file_obj = ds.File(
            filename=file.filename,
            mimetype=file.content_type,
        )
        key = f"{name}@{realization_index}@{uuid4()}"
        blob = azure_blob_container.get_blob_client(key)
        await blob.upload_blob(file.file)

        file_obj.az_container = azure_blob_container.container_name
        file_obj.az_blob = key

        return file_obj

    async def stage_blob(
        self,
        db: Session,
        ensemble_id: UUID,
        name: str,
        realization_index: Optional[int],
        request: Request,
        block_index: int,
    ) -> ds.FileBlock:
        ensemble = db.query(ds.Ensemble).filter_by(id=ensemble_id).one()

        record_obj = (
            db.query(ds.Record)
            .filter_by(realization_index=realization_index)
            .join(ds.RecordInfo)
            .filter_by(ensemble_pk=ensemble.pk, name=name)
            .one()
        )

        key = record_obj.file.az_blob
        blob = azure_blob_container.get_blob_client(key)

        block_id = str(uuid4())
        await blob.stage_block(block_id, await request.body())

        file_block_obj = ds.FileBlock(
            ensemble=ensemble,
            block_id=block_id,
            block_index=block_index,
            record_name=name,
            realization_index=realization_index,
        )
        return file_block_obj

    def create_blob(
        self, name: str, realization_index: Optional[int], file_obj: ds.File
    ) -> None:
        key = f"{name}@{realization_index}@{uuid4()}"
        blob = azure_blob_container.get_blob_client(key)
        file_obj.az_container = (azure_blob_container.container_name,)
        file_obj.az_blob = (key,)

    async def finalize_blob(
        self, record_obj: ds.Record, submitted_blocks: List[ds.FileBlock]
    ) -> None:
        key = record_obj.file.az_blob
        blob = azure_blob_container.get_blob_client(key)
        block_ids = [
            block.block_id
            for block in sorted(submitted_blocks, key=lambda x: x.block_index)
        ]
        await blob.commit_block_list(block_ids)


def get_handler() -> GeneralBlobHandler:
    if HAS_AZURE_BLOB_STORAGE:
        return AzureBlobHandler()
    return GeneralBlobHandler()
