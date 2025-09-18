from knowledgeplatformmanagement_generic.data.extract.documents.pipeline.documents.pipeline_documents import (
    PipelineDocuments,
)

from knowledgeplatformmanagement_han.data.dao.datasink_documents import DatasinkDocuments
from knowledgeplatformmanagement_han.data.extract.documents.extractor.partner.extractor_partner import ExtractorPartner


# This implements a slim interface.
# pylint: disable-next=too-few-public-methods
class Documents:
    def __init__(
        self,
        datasink: DatasinkDocuments,
        pipelinedocuments: PipelineDocuments,
    ) -> None:
        self.datasink = datasink
        self.pipelinedocuments = pipelinedocuments
        self.extractorpartner = ExtractorPartner(
            do_exclude_entities_unknown=False,
        )
