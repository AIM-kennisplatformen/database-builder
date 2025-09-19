from anyio import Path
from knowledgeplatformmanagement_generic.data.extract.documents.pipeline.documents.pipeline_documents import (
    PipelineDocuments,
    PipelineDocumentsConversionFailedError,
)
from loguru import logger
from pytest import mark

from knowledgeplatformmanagement_han.data.dao.datalayer import Datalayer
from knowledgeplatformmanagement_han.settings import Configuration


# @mark.sensitive(reason="The dataset is real and not sanitized.")
# @mark.slow(reason="Runs pipeline over substantial dataset.")
# @mark.anyio(scope="module")
# async def test_pipeline_documents_store_real(configuration: Configuration, datalayer: Datalayer) -> None:
#     pipelinedocuments = PipelineDocuments(configuration=configuration)
#     assert configuration.paths.path_dir_testdata is not None
#     path_dir_document = Path(configuration.paths.path_dir_testdata) / "documents"
#     logger.debug("Reading test dataset from '{!s}'.", path_dir_document)
#     assert await path_dir_document.exists()
#     doclingdocuments = pipelinedocuments.produce_doclingdocuments(
#         sources=[
#             path_file_document._path
#             async for path_file_document in path_dir_document.glob("**/*.*")
#             if await path_file_document.is_file()
#             and path_file_document.suffix in {".docx", ".html", ".md", ".pdf", ".pptx", ".xlsx"}
#         ],
#     )
#     async with datalayer.dataaccessor_qdrant as connection_qdrant:
#         for doclingdocument in doclingdocuments:
#             if not isinstance(doclingdocument, PipelineDocumentsConversionFailedError):
#                 await connection_qdrant.insert_document(doclingdocument=doclingdocument)


# @mark.sensitive(reason="The dataset is real and not sanitized.")
# @mark.slow(reason="In the worst case, depends on a fresh test_pipeline_documents_store() run, which is slow.")
# @mark.anyio(scope="module")
# async def test_pipeline_documents_load_real(configuration: Configuration, datalayer: Datalayer) -> None:
#     # TODO: Encode as dependency, instead of re-running this test?
#     await test_pipeline_documents_store_real(configuration=configuration, datalayer=datalayer)
#     hashvalue = 12868311516057950368
#     async with datalayer.dataaccessor_qdrant as connection_qdrant:
#         doclingdocument = await connection_qdrant.fetch_full_document(hashvalue_document=hashvalue)
#     assert doclingdocument
#     assert doclingdocument.origin
#     assert doclingdocument.origin.binary_hash == hashvalue
