from email.message import Message
from io import BytesIO
from itertools import chain
from pathlib import Path

from asapi import FromHeader, FromPath, Injected
from docling.datamodel.document import DoclingDocument  # type: ignore[attr-defined]
from docling_core.types.doc.document import Uint64
from fastapi import APIRouter, HTTPException, Request, Response, status
from pathvalidate import sanitize_filename
from pydantic import BaseModel, PositiveInt

from knowledgeplatformmanagement_han.data.dao.datalayer import Datalayer
from knowledgeplatformmanagement_han.data.extract.documents import Documents
from knowledgeplatformmanagement_han.data.extract.documents.pipeline.classifier import (
    ClassifyKeyareas,
    ProposalKeyareaClassifier,
)
from knowledgeplatformmanagement_han.data.extract.documents.proposal import Proposal
from knowledgeplatformmanagement_han.data.model.description import Description
from knowledgeplatformmanagement_han.data.model.document import Document
from knowledgeplatformmanagement_han.data.model.namelike_name import NamelikeName
from knowledgeplatformmanagement_han.data.model.provenant import Source
from knowledgeplatformmanagement_han.data.model.universityofappliedsciences import Universityofappliedsciences
from knowledgeplatformmanagement_han.settings import Configuration

TEMPLATE_QUERY = (
    "$documents\n"
    "QUERY: $query\n"
    "INSTRUCTIONS: Answer the user’s query using only the sources before `QUERY:`. "
    "If the documents don’t contain the facts to answer the query return `NONE`. "
    "Use the IEEE reference style. "
    "Add a bibliography in Markdown format. "
    "Start with `# References` and make a list with `*` for each bibliography item. "
    "If you make a reference more than once, just reuse the number and make sure you don’t add a reference multiple"
    " times."
)

router = APIRouter(prefix="/documents")


class ResponseHashvalue(BaseModel, frozen=True):
    hashvalue: Uint64


# The parameters are all needed here.
@router.post("/insert")
async def insert(  # noqa: PLR0913
    *,
    configuration: Injected[Configuration],
    content_disposition: FromHeader[str],
    content_length: FromHeader[PositiveInt],
    datalayer: Injected[Datalayer],
    documents: Injected[Documents],
    request: Request,
) -> ResponseHashvalue:
    """Supports documents in formats:
    - `application/pdf`
    - `application/vnd.openxmlformats-officedocument.presentationml.presentation`
    - `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
    - `application/vnd.openxmlformats-officedocument.wordprocessingml.document`
    - `text/csv`
    - `text/html`
    - `text/markdown`
    """
    if content_length and content_length < configuration.size_max_document:
        message = Message()
        message.add_header(_name="Content-Disposition", _value=content_disposition)
        if filename := message.get_filename():
            # TODO: (infosec): test
            filename_sanitized = sanitize_filename(Path(filename).name)
            doclingdocument = documents.pipelinedocuments.produce_doclingdocument(
                data_document=BytesIO(await request.body()),
                name_document=filename_sanitized,
            )
            if not isinstance(doclingdocument, DoclingDocument):
                raise HTTPException(
                    detail="A fault occurred during document processing.",
                    status_code=status.HTTP_400_BAD_REQUEST,
                ) from doclingdocument
            async with datalayer.dataaccessor_qdrant as connection_qdrant:
                hashvalue = await connection_qdrant.insert_document(doclingdocument=doclingdocument)
            hashvalue_str = str(hashvalue)
            documents.datasink.hashvalue_to_document[hashvalue_str] = Document(
                hashvalue=hashvalue_str,
                namelike_name=doclingdocument.name,
            )
            return ResponseHashvalue(hashvalue=hashvalue, status_code=status.HTTP_204_NO_CONTENT)
    raise HTTPException(
        detail=f"One or more files had a zero or unspecified length ({content_length}), or incorrect content type "
        f"({message.get_content_type()}).",
        status_code=status.HTTP_400_BAD_REQUEST,
    )


@router.put("/classify/keyareas/{hashvalue_proposal}")
async def classify_keyareas(
    *,
    configuration: Injected[Configuration],
    datalayer: Injected[Datalayer],
    hashvalue_proposal: FromPath[Uint64],
) -> ClassifyKeyareas:
    async with datalayer.dataaccessor_qdrant as connection_qdrant:
        if doclingdocument := await connection_qdrant.fetch_full_document(hashvalue_document=hashvalue_proposal):
            proposal = Proposal(configuration=configuration, doclingdocument=doclingdocument)
            proposalkeyareaclassifier = ProposalKeyareaClassifier(
                configuration=configuration,
                dataaccessor_llm=datalayer.dataaccessor_llm,
            )
            return await proposalkeyareaclassifier.run_pipeline(proposal=proposal)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document (integer hash value: {hashvalue_proposal}) not found.",
        )


@router.put("/extract/partners/{hashvalue_proposal}")
async def extract_partners(
    *,
    configuration: Injected[Configuration],
    datalayer: Injected[Datalayer],
    documents: Injected[Documents],
    hashvalue_proposal: FromPath[Uint64],
) -> Response:
    async with datalayer.dataaccessor_qdrant as connection_qdrant:
        doclingdocument = await connection_qdrant.fetch_full_document(hashvalue_document=hashvalue_proposal)
    if doclingdocument:
        proposal = Proposal(configuration=configuration, doclingdocument=doclingdocument)
        # TODO: Parameterize extractorpartner.
        if entitysource := documents.extractorpartner.run(proposal=proposal):
            for entity in chain(
                entitysource.ner_text,
                entitysource.ner_title,
                entitysource.partners_known_text,
                entitysource.partnertable,
            ):
                # TODO: Differentiate by entity type.
                namelike_name = NamelikeName(
                    confidence=0.2,
                    source=Source.documents,
                    value=entity.value,
                )
                documents.datasink.namelike_name_to_universityofappliedsciences[namelike_name.value] = (
                    Universityofappliedsciences(
                        description=Description(
                            confidence=0.3,
                            source=Source.documents,
                            value=proposal.summary,
                        ),
                        namelike_name=namelike_name,
                    )
                )
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Document (integer hash value: {hashvalue_proposal}) not found.",
    )
