from collections.abc import AsyncGenerator, Iterator
from typing import override

from docling_core.types.doc.document import Uint64
from knowledgeplatformmanagement_generic.data.extract.documents.pipeline.documents.pipeline_documents import (
    PipelineDocuments,
    PipelineDocumentsConversionFailedError,
)
from knowledgeplatformmanagement_generic.data.services.qdrant.dataaccessor_qdrant import DataaccessorQdrant

from knowledgeplatformmanagement_han.data.extract.documents.extractor.extractor import Extractor
from knowledgeplatformmanagement_han.data.extract.documents.extractor.partner.extractor_partner import ExtractorPartner
from knowledgeplatformmanagement_han.data.extract.documents.extractor.proposal.extract_proposal import (
    ExtractProposal,
)
from knowledgeplatformmanagement_han.data.extract.documents.proposal import Proposal


class ExtractorProposalNotfoundError(ValueError):
    def __init__(self, *, hashvalue_proposal: Uint64) -> None:
        super().__init__(f"Proposal (integer hash value {hashvalue_proposal}) not found.")


# This class is simple, single-responsibility so we don't need many public methods.
# pylint: disable-next=too-few-public-methods
class ExtractorProposal(Extractor[ExtractProposal]):
    """Extract information from Research Proposal documents."""

    def __init__(
        self,
        *,
        extractorpartner: ExtractorPartner,
        dataacccessor_qdrant: DataaccessorQdrant,
        pipelinedocuments: PipelineDocuments,
    ) -> None:
        super().__init__(pipelinedocuments=pipelinedocuments)
        self._dataacccessor_qdrant = dataacccessor_qdrant
        self.extractorpartner = extractorpartner

    # Work around Mypy defect. See https://github.com/python/mypy/issues/17363.
    @override
    async def extract(  # type: ignore[override]
        self,
        # TODO: Don't fetch documents anew, but pass in-memory objects.
        hashvalues_document: Iterator[Uint64],
    ) -> AsyncGenerator[ExtractProposal | PipelineDocumentsConversionFailedError, None]:
        """From Proposals, extract the relevant details."""
        async with self._dataacccessor_qdrant as connection_qdrant:
            async for doclingdocument in (
                await connection_qdrant.fetch_full_document(hashvalue_document=hashvalue_proposal)
                for hashvalue_proposal in hashvalues_document
            ):
                if doclingdocument:
                    assert doclingdocument.origin
                    hashvalue_proposal = doclingdocument.origin.binary_hash
                    proposal = Proposal(
                        configuration=self._pipelinedocuments.configuration,
                        doclingdocument=doclingdocument,
                    )
                    partners = self.extractorpartner.run(proposal=proposal)
                    yield ExtractProposal(
                        projectname=proposal.projectname,
                        hashvalue_proposal=hashvalue_proposal,
                        partners=partners,
                    )
                else:
                    raise ExtractorProposalNotfoundError(hashvalue_proposal=hashvalue_proposal)
