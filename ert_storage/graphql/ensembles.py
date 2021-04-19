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
    responses = gr.Field("ert_storage.graphql.responses.Response")
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

    def resolve_parameters(
        root: ds.Ensemble, info: "ResolveInfo"
    ) -> Iterable[ds.Prior]:
        return root.parameters


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
