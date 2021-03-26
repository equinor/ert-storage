from typing import TYPE_CHECKING
import graphene as gr
from graphene_sqlalchemy.utils import get_session

from ert_storage.ext.graphene_sqlalchemy import SQLAlchemyObjectType, SQLAlchemyMutation
from ert_storage.graphql.ensembles import CreateEnsemble
from ert_storage import database_schema as ds


if TYPE_CHECKING:
    from graphql.execution.base import ResolveInfo


class Experiment(SQLAlchemyObjectType):
    class Meta:
        model = ds.Experiment


class CreateExperiment(SQLAlchemyMutation):
    class Arguments:
        name = gr.String()

    class Meta:
        model = ds.Experiment

    create_ensemble = CreateEnsemble.Field()

    @staticmethod
    def mutate(root: None, info: "ResolveInfo", name: str) -> ds.Experiment:
        db = get_session(info.context)

        experiment = ds.Experiment(name=name)

        db.add(experiment)
        db.commit()

        return experiment
