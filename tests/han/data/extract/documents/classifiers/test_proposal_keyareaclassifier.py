# TODO: See https://github.com/DS4SD/docling/issues/614
from docling.datamodel.document import DoclingDocument  # type: ignore[attr-defined]
from pytest import mark

from knowledgeplatformmanagement_han.data.dao.datalayer import Datalayer
from knowledgeplatformmanagement_han.data.extract.documents.pipeline.classifier import ProposalKeyareaClassifier
from knowledgeplatformmanagement_han.data.extract.documents.proposal import Proposal
from knowledgeplatformmanagement_han.settings import Configuration


@mark.slow(reason="Calls remote API.")
@mark.anyio(scope="module")
async def test_proposal_keyarea_classifier(configuration: Configuration, datalayer: Datalayer) -> None:
    async with datalayer.dataaccessor_qdrant as connection_qdrant:
        doclingdocument = await connection_qdrant.fetch_full_document(hashvalue_document=2520273719576448581)
    assert isinstance(doclingdocument, DoclingDocument)
    proposal = Proposal(configuration=configuration, doclingdocument=doclingdocument)
    proposalkeyareaclassifier = ProposalKeyareaClassifier(
        configuration=configuration,
        dataaccessor_llm=datalayer.dataaccessor_llm,
    )
    classifykeyareas = await proposalkeyareaclassifier.run_pipeline(proposal=proposal)
    # The rationale varies between runs, so cannot be matched exactly.
    assert all(keyarea in classifykeyareas.rationale for keyarea in ("SCHOON", "SLIM", "SOCIAAL"))
