from typing import Optional, List
from fastapi import UploadFile, Request
from uuid import uuid4

from ert_storage.database import HAS_AZURE_BLOB_STORAGE
from ert_storage import database_schema as ds

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
        file_block_obj: ds.FileBlock,
        request: Request,
        record_obj: ds.Record,
        block_id: str,
    ) -> None:
        file_block_obj.content = await request.body()

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
        file_block_obj: ds.FileBlock,
        request: Request,
        record_obj: ds.Record,
        block_id: str,
    ) -> None:
        key = record_obj.file.az_blob
        blob = azure_blob_container.get_blob_client(key)
        await blob.stage_block(block_id, await request.body())

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
