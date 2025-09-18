from os import environ
from pathlib import Path as PathSync
from uuid import SafeUUID, uuid4

from openai import OpenAI
from pytest import fixture
from sentence_transformers import SentenceTransformer

from knowledgeplatformmanagement_generic.data.services.llm.dataaccessor_llm import DataaccessorLlm
from knowledgeplatformmanagement_generic.data.services.qdrant.dataaccessor_qdrant import DataaccessorQdrant
from knowledgeplatformmanagement_generic.data.services.typedb.dataaccessor_typedb import DataaccessorTypedb
from knowledgeplatformmanagement_generic.settings import Configuration
from knowledgeplatformmanagement_generic.settings.paths import Paths


@fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


@fixture(name="configuration", scope="function")
def fixture_configuration() -> Configuration:
    uuid = uuid4()
    # Regrettably, UUID safety seems to be unknown in practice.
    assert uuid.is_safe != SafeUUID.unsafe
    return Configuration(
        name_database="knowledgeplatform-test-" + str(uuid),
        paths=Paths(
            path_dir_testdata=PathSync("../data"),
        ),
    )


@fixture(name="openai", scope="function")
def fixture_openai() -> OpenAI:
    return OpenAI(api_key=environ["OPENAI_API_KEY"])


@fixture(name="dataaccessor_llm", scope="function")
def fixture_dataaccessor_llm(*, configuration: Configuration, openai: OpenAI) -> DataaccessorLlm:
    return DataaccessorLlm(configuration=configuration, openai=openai)


@fixture(name="dataaccessor_typedb", scope="function")
def fixture_dataaccessor_typedb(*, configuration: Configuration) -> DataaccessorTypedb:
    return DataaccessorTypedb(configuration=configuration)


@fixture(name="model_encoder", scope="function")
def fixture_model_encoder(*, configuration: Configuration) -> SentenceTransformer:
    return SentenceTransformer(
        model_name_or_path=configuration.name_model_encoder,
        local_files_only=True,
        # TODO: infosec. Otherwise, fails with No module named 'custom_st'.
        trust_remote_code=True,
    )


@fixture(name="dataaccessor_qdrant", scope="function")
def fixture_dataaccessor_qdrant(
    *,
    configuration: Configuration,
    model_encoder: SentenceTransformer,
) -> DataaccessorQdrant:
    return DataaccessorQdrant(configuration=configuration, model_encoder=model_encoder)
