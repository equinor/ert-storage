from typing import Any, List, Optional, TYPE_CHECKING
import graphene as gr
from sqlalchemy.orm import Session

from ert_storage.ext.graphene_sqlalchemy import SQLAlchemyObjectType
from ert_storage import database_schema as ds
from ert_storage.endpoints.priors import prior_to_dict


if TYPE_CHECKING:
    from graphql.execution.base import ResolveInfo


class Parameter(SQLAlchemyObjectType):
    class Meta:
        model = ds.Record

    prior = gr.JSONString()

    def resolve_prior(root: ds.Record, info: "ResolveInfo") -> Optional[dict]:
        prior = root.prior
        return prior_to_dict(prior) if prior is not None else None
