from ert_storage.database_schema.record import RecordClass
from typing import Iterable, List, Optional, TYPE_CHECKING
import graphene as gr
from graphene_sqlalchemy.utils import get_session

from ert_storage.ext.graphene_sqlalchemy import SQLAlchemyObjectType, SQLAlchemyMutation
from ert_storage import database_schema as ds


if TYPE_CHECKING:
    from graphql.execution.base import ResolveInfo
    from ert_storage.graphql.experiments import Experiment


class Ensemble(SQLAlchemyObjectType):
    class Meta:
        model = ds.Ensemble

    child_ensembles = gr.List(lambda: Ensemble)
    parent_ensemble = gr.Field(lambda: Ensemble)
    response_names = gr.List(gr.String)
    responses = gr.List("ert_storage.graphql.responses.Response")
    parameter_names = gr.List(gr.String)
    parameters = gr.List("ert_storage.graphql.parameters.Parameter")

    def resolve_child_ensembles(
        root: ds.Ensemble, info: "ResolveInfo"
    ) -> List[ds.Ensemble]:
        return [x.ensemble_result for x in root.children]

    def resolve_parent_ensemble(
        root: ds.Ensemble, info: "ResolveInfo"
    ) -> Optional[ds.Ensemble]:
        update = root.parent
        if update is not None:
            return update.ensemble_reference
        return None

    def resolve_response_names(
        root: ds.Ensemble, info: "ResolveInfo"
    ) -> Iterable[ds.Prior]:
        session = info.context["session"]
        return [
            x[0]
            for x in session.query(ds.Record.name)
            .filter_by(ensemble_pk=root.pk, record_class="other")
            .filter(ds.Record.realization_index != None)
            .distinct()
        ]

    def resolve_parameter_names(
        root: ds.Ensemble, info: "ResolveInfo"
    ) -> Iterable[ds.Prior]:
        session = info.context["session"]
        return [
            x[0]
            for x in session.query(ds.Record.name)
            .filter_by(ensemble_pk=root.pk, record_class="parameter")
            .filter(ds.Record.realization_index != None)
            .distinct()
        ]

    def resolve_parameters(
        root: ds.Ensemble, info: "ResolveInfo"
    ) -> Iterable[ds.Prior]:
        return root.parameters

    def resolve_responses(root: ds.Ensemble, info: "ResolveInfo") -> Iterable[ds.Prior]:
        return root.records.filter_by(record_class="parameter")


class CreateEnsemble(SQLAlchemyMutation):
    class Meta:
        model = ds.Ensemble

    class Arguments:
        parameters = gr.List(gr.String)

    @staticmethod
    def mutate(
        root: Optional["Experiment"],
        info: "ResolveInfo",
        parameters: List[str],
        experiment_id: Optional[str] = None,
    ) -> ds.Ensemble:
        db = get_session(info.context)

        if experiment_id is not None:
            experiment = db.query(ds.Experiment).filter_by(id=experiment_id).one()
        elif hasattr(root, "id"):
            experiment = root
        else:
            raise ValueError("ID is required")

        ensemble = ds.Ensemble(inputs=parameters, experiment=experiment)

        db.add(ensemble)
        db.commit()
        return ensemble
