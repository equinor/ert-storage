from enum import Enum
from typing import Any, List, Optional, TYPE_CHECKING
import graphene as gr

from ert_storage.ext.graphene_sqlalchemy import SQLAlchemyObjectType
from ert_storage import database_schema as ds


if TYPE_CHECKING:
    from graphql.execution.base import ResolveInfo


class Response(SQLAlchemyObjectType):
    class Meta:
        model = ds.Record

    name = gr.String()
    record_type = gr.Enum.from_enum(ds.RecordType)

    def resolve_name(root: ds.Record, info: "ResolveInfo") -> str:
        return root.name

    def resolve_record_type(root: ds.Record, info: "ResolveInfo") -> Enum:
        return root.record_info.record_type
