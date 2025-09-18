from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator, Iterator

from docling_core.types.doc.document import Uint64
from knowledgeplatformmanagement_generic.data.extract.documents.pipeline.documents.pipeline_documents import (
    PipelineDocuments,
    PipelineDocumentsConversionFailedError,
)


# This class is simple, single-responsibility so we don't need many public methods.
# pylint: disable-next=too-few-public-methods
class Extractor[T](ABC):
    """Extract information based on a documents pipeline."""

    def __init__(self, pipelinedocuments: PipelineDocuments) -> None:
        self._pipelinedocuments = pipelinedocuments

    @abstractmethod
    async def extract(
        self,
        hashvalues_document: Iterator[Uint64],
    ) -> AsyncGenerator[T | PipelineDocumentsConversionFailedError, None]: ...
