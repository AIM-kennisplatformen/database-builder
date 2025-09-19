from anyio import Path
from docling.datamodel.document import DoclingDocument  # type: ignore[attr-defined]
from docling_core.types.doc.document import Uint64
from knowledgeplatformmanagement_generic.data.extract.documents.document import Entities, Entity
from knowledgeplatformmanagement_generic.data.extract.documents.pipeline.documents.pipeline_documents import (
    PipelineDocuments,
)
from pytest import mark, param

from knowledgeplatformmanagement_han.data.dao.datalayer import Datalayer
from knowledgeplatformmanagement_han.data.extract.documents.extractor.partner.extractor_partner import (
    Entitysource,
    ExtractorPartner,
)
from knowledgeplatformmanagement_han.data.extract.documents.extractor.proposal.extract_proposal import (
    ExtractProposal,
)
from knowledgeplatformmanagement_han.data.extract.documents.extractor.proposal.extractor_proposal import (
    ExtractorProposal,
)
from knowledgeplatformmanagement_han.settings import Configuration


# @mark.parametrize(
#     "do_exclude_entities_unknown,entities_known,extractproposal_expected",
#     [
#         # Whether a single known partner is extracted from text while more occur, and all partners from the partner
#         # table because `do_exclude_entities_unknown == False`, and no partners from the text using NER, since
#         # the section titled ‘Samenwerkingsverband’ only contains a sentence without partners, apart from the partner
#         # table.
#         param(
#             False,
#             frozenset({}),
#             ExtractProposal(
#                 projectname="Projecttitel",
#                 hashvalue_proposal=1230198746648155557,
#                 partners=Entitysource(
#                     partners_known_text={},
#                     partnertable={
#                         Entity(entitytype="ORG", value="ABC"): None,
#                         Entity(entitytype="ORG", value="De DEF partner"): None,
#                         Entity(entitytype="ORG", value="GHIJKLMnopQrSTU"): None,
#                     },
#                     ner_text={},
#                     ner_title={},
#                 ),
#             ),
#             id="ner",
#         ),
#         # Whether no known partner is extracted from text while multiple occur, and all partners from the partner table
#         # because `do_exclude_entities_unknown == False`, and no partners from the text using NER, since
#         # the section titled ‘Samenwerkingsverband’ only contains a sentence without partners, apart from the partner
#         # table.
#         param(
#             False,
#             {
#                 Entity(entitytype="ORG", value="ABE"): None,
#                 Entity(entitytype="ORG", value="AFEM"): None,
#                 Entity(entitytype="ORG", value="AIM"): None,
#                 Entity(entitytype="ORG", value="AMM"): None,
#                 Entity(entitytype="ORG", value="AOO"): None,
#                 Entity(entitytype="ORG", value="Fontys"): None,
#                 Entity(entitytype="ORG", value="HAN"): None,
#                 Entity(entitytype="ORG", value="M-BIS"): None,
#                 Entity(entitytype="ORG", value="Saxion"): None,
#             },
#             ExtractProposal(
#                 projectname="Projecttitel",
#                 hashvalue_proposal=1230198746648155557,
#                 partners=Entitysource(
#                     partners_known_text={},
#                     partnertable={
#                         Entity(entitytype="ORG", value="ABC"): None,
#                         Entity(entitytype="ORG", value="De DEF partner"): None,
#                         Entity(entitytype="ORG", value="GHIJKLMnopQrSTU"): None,
#                     },
#                     ner_text={},
#                     ner_title={},
#                 ),
#             ),
#             id="unknown",
#         ),
#         # Whether a single known partner is extracted from the text while multiple occur, all partners from the
#         # partner table because `do_exclude_entities_unknown == False`, and no partners from the text using NER, since
#         # the section titled ‘Samenwerkingsverband’ only contains a sentence without partners, apart from the partner
#         # table.
#         param(
#             False,
#             {
#                 Entity(entitytype="ORG", value="De DEF partner"): None,
#             },
#             ExtractProposal(
#                 projectname="Projecttitel",
#                 hashvalue_proposal=1230198746648155557,
#                 partners=Entitysource(
#                     partners_known_text={Entity(entitytype="ORG", value="De DEF partner"): None},
#                     partnertable={
#                         Entity(entitytype="ORG", value="ABC"): None,
#                         Entity(entitytype="ORG", value="De DEF partner"): None,
#                         Entity(entitytype="ORG", value="GHIJKLMnopQrSTU"): None,
#                     },
#                     ner_text={},
#                     ner_title={},
#                 ),
#             ),
#             id="partial",
#         ),
#         # Whether a single known partner is extracted from the text, but all partners from the partner tables, and no
#         # other partners anywhere because `do_exclude_entities_unknown == True`, and no partners from the text using
#         # NER, since the section titled ‘Samenwerkingsverband’ only contains a sentence without partners, apart from the
#         # partner table.
#         param(
#             True,
#             {
#                 Entity(entitytype="ORG", value="De DEF partner"): None,
#             },
#             ExtractProposal(
#                 projectname="Projecttitel",
#                 hashvalue_proposal=1230198746648155557,
#                 partners=Entitysource(
#                     partners_known_text={Entity(entitytype="ORG", value="De DEF partner"): None},
#                     partnertable={
#                         Entity(
#                             entitytype="ORG",
#                             value="ABC",
#                         ): None,
#                         Entity(entitytype="ORG", value="De DEF partner"): None,
#                         Entity(
#                             entitytype="ORG",
#                             value="GHIJKLMnopQrSTU",
#                         ): None,
#                     },
#                     ner_text={},
#                     ner_title={},
#                 ),
#             ),
#             id="exclude",
#         ),
#     ],
# )
# @mark.anyio(scope="module")
# async def test_extractproposal(
#     *,
#     configuration: Configuration,
#     datalayer: Datalayer,
#     do_exclude_entities_unknown: bool,
#     entities_known: Entities,
#     extractproposal_expected: ExtractProposal,
# ) -> None:
#     path_file_document = await ("ProjectProposalTest.pdf").resolve(strict=True)
#     pipelinedocuments = PipelineDocuments(configuration=configuration)
#     async with datalayer.dataaccessor_qdrant as connection_qdrant:
#         hashvalues_proposal: list[Uint64] = [
#             await connection_qdrant.insert_document(doclingdocument=doclingdocument)
#             for doclingdocument in pipelinedocuments.produce_doclingdocuments(sources=(path_file_document._path,))
#             if isinstance(doclingdocument, DoclingDocument)
#         ]
#     extractorpartner = ExtractorPartner(
#         do_exclude_entities_unknown=do_exclude_entities_unknown,
#         entities_known=entities_known,
#     )
#     extractorproposal = ExtractorProposal(
#         extractorpartner=extractorpartner,
#         dataacccessor_qdrant=datalayer.dataaccessor_qdrant,
#         pipelinedocuments=pipelinedocuments,
#     )
#     extractproposals = [
#         extractproposal
#         async for extractproposal in extractorproposal.extract(
#             hashvalues_document=iter(hashvalues_proposal),
#         )
#     ]
#     assert len(extractproposals) == 1
#     extractproposal_actual = next(iter(extractproposals))
#     assert isinstance(extractproposal_actual, ExtractProposal)
#     # Magic values are sensible in automated test assertions as they directly express a literal value to match.
#     assert extractproposal_actual.hashvalue_proposal == 1230198746648155557  # noqa: PLR2004
#     assert extractproposal_expected == extractproposal_actual
