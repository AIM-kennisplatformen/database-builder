from collections.abc import AsyncIterator
from io import BytesIO
from os import environ
from pathlib import Path as PathSync
from uuid import SafeUUID, uuid4
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

from anyio import Path
from fastapi.testclient import TestClient
from knowledgeplatformmanagement_generic.data.extract.documents.pipeline.documents.pipeline_documents import (
    PipelineDocuments,
)
from knowledgeplatformmanagement_generic.data.services.llm.dataaccessor_llm import DataaccessorLlm
from knowledgeplatformmanagement_generic.data.services.qdrant.dataaccessor_qdrant import DataaccessorQdrant
from knowledgeplatformmanagement_generic.data.services.typedb.dataaccessor_typedb import DataaccessorTypedb
from knowledgeplatformmanagement_generic.installer.exceptions import DirectoryNotFoundError
from knowledgeplatformmanagement_generic.logger import configure_logger
from loguru import logger
from openai import OpenAI
from pytest import fixture
from sentence_transformers import SentenceTransformer

from knowledgeplatformmanagement_han.data.dao.datalayer import Datalayer
from knowledgeplatformmanagement_han.data.dao.datasink_documents import DatasinkDocuments
from knowledgeplatformmanagement_han.data.dao.datasink_microsoft365 import DatasinkMicrosoft365
from knowledgeplatformmanagement_han.data.dao.datasink_ubwfris import DatasinkUbwfris
from knowledgeplatformmanagement_han.data.dao.datasinks import Datasinks
from knowledgeplatformmanagement_han.data.extract.documents import Documents
from knowledgeplatformmanagement_han.data.extract.ubwfris import Ubwfris
from knowledgeplatformmanagement_han.settings import Configuration
from knowledgeplatformmanagement_han.settings.paths import Paths
from knowledgeplatformmanagement_han.web.__main__ import create_fastapi


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
            path_dir_testdata=PathSync("../confidential-data-han").resolve(strict=True),
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


@fixture(name="datalayer", scope="function")
async def fixture_datalayer(
    *,
    configuration: Configuration,
    dataaccessor_llm: DataaccessorLlm,
    dataaccessor_typedb: DataaccessorTypedb,
    dataaccessor_qdrant: DataaccessorQdrant,
    model_encoder: SentenceTransformer,
) -> AsyncIterator[Datalayer]:
    datasinks = Datasinks(
        microsoft365=DatasinkMicrosoft365(),
        ubwfris=DatasinkUbwfris(),
        documents=DatasinkDocuments(),
    )

    datalayer = Datalayer(
        configuration=configuration,
        dataaccessor_llm=dataaccessor_llm,
        dataaccessor_typedb=dataaccessor_typedb,
        dataaccessor_qdrant=dataaccessor_qdrant,
        model_encoder=model_encoder,
        datasinks=datasinks,
    )
    await datalayer.init()
    yield datalayer
    await datalayer.clear()


@fixture(name="testclient", scope="function")
async def fixture_testclient(
    *,
    configuration: Configuration,
    datalayer: Datalayer,
) -> AsyncIterator[TestClient]:
    # TODO: Get configuration from config file.
    for path_dir in (configuration.paths.path_dir_user_data, configuration.paths.path_dir_user_cache):
        if not path_dir.exists():
            raise DirectoryNotFoundError(path_dir=path_dir)
    configure_logger(configuration=configuration)
    ubwfris = Ubwfris(datasink=datalayer.datasinks.ubwfris)
    microsoft365graph = None
    documents = Documents(
        datasink=datalayer.datasinks.documents,
        pipelinedocuments=PipelineDocuments(configuration=configuration),
    )
    fastapi = create_fastapi(
        configuration=configuration,
        datalayer=datalayer,
        microsoft365graph=microsoft365graph,
        ubwfris=ubwfris,
        documents=documents,
    )
    with TestClient(app=fastapi) as testclient:
        yield testclient


async def _bytesio_zipfile_from_directory(path_dir_workbook: Path) -> BytesIO:
    bytesio_zip = BytesIO()
    assert await path_dir_workbook.is_dir()
    with ZipFile(file=bytesio_zip, mode="a", compression=ZIP_DEFLATED, allowZip64=True) as zipfile:
        async for path_file_component, _, names_file in path_dir_workbook.walk(
            on_error=logger.exception,
        ):
            for name_file in names_file:
                path_file_zipinfo = path_file_component.relative_to(path_dir_workbook) / name_file
                zipinfo = ZipInfo(filename=str(path_file_zipinfo))
                logger.trace(
                    "Adding {path_file_component!s} to workbook ZIP archive ...",
                    path_file_component=zipinfo.filename,
                )
                data = await (path_file_component / name_file).read_bytes()
                zipfile.writestr(zinfo_or_arcname=zipinfo, data=data)
    return bytesio_zip


@fixture(name="file_workbook_ib630_withoutbooked", scope="function")
async def fixture_file_workbook_ib630_withoutbooked() -> BytesIO:
    return await _bytesio_zipfile_from_directory(
        path_dir_workbook=Path(__file__).parent / "data" / "extract" / "ubwfris" / "IB630_without_booked",
    )


@fixture(name="file_workbook_rha025a", scope="function")
async def fixture_file_workbook_rha025a() -> BytesIO:
    return await _bytesio_zipfile_from_directory(
        path_dir_workbook=Path(__file__).parent / "data" / "extract" / "ubwfris" / "RHA025A",
    )


@fixture(name="file_workbook_ib630_withoutbooked_real", scope="function")
async def fixture_file_workbook_ib630_withoutbooked_real(configuration: Configuration) -> BytesIO:
    assert configuration.paths.path_dir_testdata is not None
    path_dir_workbook = Path(configuration.paths.path_dir_testdata / "IB629")
    return await _bytesio_zipfile_from_directory(
        path_dir_workbook=path_dir_workbook,
    )


@fixture(name="file_workbook_rha025a_real", scope="function")
async def fixture_file_workbook_rha025a_real(configuration: Configuration) -> BytesIO:
    assert configuration.paths.path_dir_testdata is not None
    path_dir_workbook = Path(configuration.paths.path_dir_testdata / "rha025a_6200")
    return await _bytesio_zipfile_from_directory(
        path_dir_workbook=path_dir_workbook,
    )
