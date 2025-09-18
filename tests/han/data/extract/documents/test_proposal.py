from anyio import Path

# TODO: See https://github.com/DS4SD/docling/issues/614
from docling.datamodel.document import DoclingDocument  # type: ignore[attr-defined]
from knowledgeplatformmanagement_generic.data.extract.documents.pipeline.documents.pipeline_documents import (
    PipelineDocuments,
)
from pytest import mark

from knowledgeplatformmanagement_han.data.extract.documents.proposal import Proposal
from knowledgeplatformmanagement_han.settings import Configuration


@mark.anyio(scope="module")
async def test_proposal(configuration: Configuration) -> None:
    pipelinedocuments = PipelineDocuments(configuration=configuration)
    path_file_document = await (Path(__file__).parent / "ProjectProposalTest.pdf").resolve(strict=True)
    doclingdocument = next(pipelinedocuments.produce_doclingdocuments(sources=(path_file_document._path,)))
    assert isinstance(doclingdocument, DoclingDocument)
    proposal = Proposal(configuration=configuration, doclingdocument=doclingdocument)
    projectname_expected = "Projecttitel"
    assert projectname_expected == proposal.projectname
    assert proposal.summary == (
        "Dit is de samenvatting van het project Projecttitel van de bedrijf ABC. "
        "Deze samenvatting bestaat uit meerdere zinnen\n"
        "En misschien wel uit meerdere paragrafen. Hij moet namelijk wel lang genoeg zijn.\n"
    )
