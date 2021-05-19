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
    responses = gr.Field(
        gr.List("ert_storage.graphql.responses.Response"),
        names=gr.Argument(gr.List(gr.String), required=False, default_value=None),
    )
    unique_responses = gr.List("ert_storage.graphql.responses.Response")

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

    def resolve_unique_responses(
        root: ds.Ensemble, info: "ResolveInfo"
    ) -> Iterable[ds.Record]:
        session = info.context["session"]  # type: ignore
        response_names = [
            x[0]
            for x in session.query(ds.Record.name)
            .filter_by(ensemble_pk=root.pk, record_class=ds.RecordClass.response)
            .filter(ds.Record.realization_index != None)
            .distinct()
        ]
        return [
            root.records.filter_by(name=response_name)[0]
            for response_name in response_names
        ]

    def resolve_responses(
        root: ds.Ensemble, info: "ResolveInfo", names: Optional[Iterable[str]] = None
    ) -> Iterable[ds.Record]:
        if names is None:
            return root.records.filter_by(record_class=ds.RecordClass.response)
        return root.records.filter_by(record_class=ds.RecordClass.response).filter(
            ds.Record.name.in_(names)
        )

    def resolve_parameters(
        root: ds.Ensemble, info: "ResolveInfo"
    ) -> Iterable[ds.Prior]:
        return root.parameters


class CreateEnsemble(SQLAlchemyMutation):
    class Meta:
        model = ds.Ensemble

    class Arguments:
        parameters = gr.List(gr.String)
        size = gr.Int()

    @staticmethod
    def mutate(
        root: Optional["Experiment"],
        info: "ResolveInfo",
        parameters: List[str],
        size: int,
        experiment_id: Optional[str] = None,
    ) -> ds.Ensemble:
        db = get_session(info.context)

        if experiment_id is not None:
            experiment = db.query(ds.Experiment).filter_by(id=experiment_id).one()
        elif hasattr(root, "id"):
            experiment = root
        else:
            raise ValueError("ID is required")

        ensemble = ds.Ensemble(inputs=parameters, experiment=experiment, size=size)

        db.add(ensemble)
        db.commit()
        return ensemble
