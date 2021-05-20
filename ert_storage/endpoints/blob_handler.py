from typing import Optional
from fastapi import UploadFile, Request
from uuid import uuid4

from ert_storage.database import HAS_AZURE_BLOB_STORAGE
from ert_storage import database_schema as ds

if HAS_AZURE_BLOB_STORAGE:
    from ert_storage.database import azure_blob_container


class GeneralBlobHandler:
    async def upload_blob(
        self,
        file_obj: ds.File,
        file: UploadFile,
        name: str,
        realization_index: Optional[int],
    ) -> None:
        file_obj.content = await file.read()

    async def stage_blob(
        self,
        file_block_obj: ds.FileBlock,
        request: Request,
        record_obj: ds.Record,
        block_id: str,
    ) -> None:
        file_block_obj.content = await request.body()


class AzureBlobHandler(GeneralBlobHandler):
    async def upload_blob(
        self,
        file_obj: ds.File,
        file: UploadFile,
        name: str,
        realization_index: Optional[int],
    ) -> None:
        key = f"{name}@{realization_index}@{uuid4()}"
        blob = azure_blob_container.get_blob_client(key)
        await blob.upload_blob(file.file)

        file_obj.az_container = azure_blob_container.container_name
        file_obj.az_blob = key

    async def stage_blob(
        self,
        file_block_obj: ds.FileBlock,
        request: Request,
        record_obj: ds.Record,
        block_id: str,
    ) -> None:
        key = record_obj.file.az_blob
        blob = azure_blob_container.get_blob_client(key)
        await blob.stage_block(block_id, await request.body())


def get_handler() -> GeneralBlobHandler:
    if HAS_AZURE_BLOB_STORAGE:
        return AzureBlobHandler()
    return GeneralBlobHandler()
