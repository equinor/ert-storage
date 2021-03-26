import pytest


@pytest.fixture
def gql_client(client, monkeypatch):
    from ert_storage.graphql import schema
    from graphene.test import Client

    monkeypatch.setattr(schema, "override_session", client.session)
    yield Client(schema)
