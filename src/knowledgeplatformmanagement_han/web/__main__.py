from os import environ

from anyio import run
from asapi import bind, serve
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
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
from sentence_transformers import SentenceTransformer

from knowledgeplatformmanagement_han.data.dao.datalayer import Datalayer
from knowledgeplatformmanagement_han.data.dao.datasink_documents import DatasinkDocuments
from knowledgeplatformmanagement_han.data.dao.datasink_microsoft365 import DatasinkMicrosoft365
from knowledgeplatformmanagement_han.data.dao.datasink_ubwfris import DatasinkUbwfris
from knowledgeplatformmanagement_han.data.dao.datasinks import Datasinks
from knowledgeplatformmanagement_han.data.extract.documents import Documents
from knowledgeplatformmanagement_han.data.extract.microsoft365 import Microsoft365
from knowledgeplatformmanagement_han.data.extract.ubwfris import Ubwfris
from knowledgeplatformmanagement_han.settings import Configuration
from knowledgeplatformmanagement_han.web.common import router as router_common
from knowledgeplatformmanagement_han.web.documents import router as router_documents
from knowledgeplatformmanagement_han.web.microsoft365 import router as router_microsoft365
from knowledgeplatformmanagement_han.web.ubwfris import router as router_timesheets


def create_fastapi(
    configuration: Configuration,
    datalayer: Datalayer,
    microsoft365graph: Microsoft365 | None,
    ubwfris: Ubwfris,
    documents: Documents,
) -> FastAPI:
    fastapi = FastAPI(
        debug=configuration.fastapi_debug,
        title="Knowledge Platform Management App",
    )
    bind(fastapi, Configuration, configuration)
    bind(fastapi, Datalayer, datalayer)
    if microsoft365graph is not None:
        bind(fastapi, Microsoft365, microsoft365graph)
    bind(fastapi, Ubwfris, ubwfris)
    bind(fastapi, Documents, documents)
    fastapi.add_middleware(CORSMiddleware)
    fastapi.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=("localhost", "localhost.localdomain", "127.0.0.1", "[::1]"),
    )
    fastapi.add_middleware(GZipMiddleware)
    # TODO: (infosec) Add CSRF protection middleware.
    # TODO: (infosec) Add authentication middleware.
    # TODO: (infosec) Add rate limiting middleware.
    # TODO: (infosec) Add upload limit middleware. See: https://github.com/encode/starlette/issues/2155
    fastapi.include_router(router_timesheets)
    fastapi.include_router(router_microsoft365)
    fastapi.include_router(router_documents)
    fastapi.include_router(router_common)
    return fastapi


async def main() -> None:
    # TODO: Get configuration from config file.
    configuration = Configuration(name_database="knowledgeplatform")
    # Work around Pylint defect. See https://github.com/pylint-dev/pylint/issues/4899
    # pylint: disable-next=no-member
    for path_dir in (configuration.paths.path_dir_user_data, configuration.paths.path_dir_user_cache):
        if not path_dir.exists():
            raise DirectoryNotFoundError(path_dir=path_dir)
    configure_logger(configuration=configuration)
    openai = OpenAI(api_key=environ["OPENAI_API_KEY"])
    model_encoder = SentenceTransformer(
        model_name_or_path=configuration.name_model_encoder,
        local_files_only=True,
        # TODO: infosec. Otherwise, fails with No module named 'custom_st'.
        trust_remote_code=True,
    )
    dataaccessor_llm = DataaccessorLlm(configuration=configuration, openai=openai)
    dataaccessor_typedb = DataaccessorTypedb(configuration=configuration)
    dataaccessor_qdrant = DataaccessorQdrant(configuration=configuration, model_encoder=model_encoder)
    pipelinedocuments = PipelineDocuments(configuration=configuration)
    datasinkubwfris = DatasinkUbwfris()
    datasinkmicrosoft365 = DatasinkMicrosoft365()
    datasinkdocuments = DatasinkDocuments()
    datasinks = Datasinks(ubwfris=datasinkubwfris, microsoft365=datasinkmicrosoft365, documents=datasinkdocuments)
    datalayer = Datalayer(
        configuration=configuration,
        dataaccessor_typedb=dataaccessor_typedb,
        dataaccessor_qdrant=dataaccessor_qdrant,
        dataaccessor_llm=dataaccessor_llm,
        datasinks=datasinks,
        model_encoder=model_encoder,
    )
    ubwfris = Ubwfris(datasink=datasinkubwfris)
    documents = Documents(
        datasink=datasinkdocuments,
        pipelinedocuments=pipelinedocuments,
    )
    if not (microsoft365_id_client := environ.get("MICROSOFT365_ID_CLIENT")):
        logger.warning("`MICROSOFT365_ID_CLIENT` not set, so not enabling Microsoft 365 functionality.")
    microsoft365_id_client = microsoft365_id_client or None
    microsoft365_scopes_user = environ.get("MICROSOFT365_SCOPES_USER") or ""
    microsoft365graph = Microsoft365(
        datasink=datasinkmicrosoft365,
        microsoft365_id_client=microsoft365_id_client,
        microsoft365_id_tenant=environ.get("MICROSOFT365_ID_TENANT"),
        microsoft365_scopes_user=microsoft365_scopes_user.split(),
    )
    fastapi = create_fastapi(
        configuration=configuration,
        datalayer=datalayer,
        documents=documents,
        microsoft365graph=microsoft365graph,
        ubwfris=ubwfris,
    )
    await serve(app=fastapi, port=configuration.port)


if __name__ == "__main__":
    run(main)
