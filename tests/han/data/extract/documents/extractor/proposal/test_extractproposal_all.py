from anyio import Path
from docling.datamodel.document import DoclingDocument  # type: ignore[attr-defined]
from docling_core.types.doc.document import Uint64
from knowledgeplatformmanagement_generic.data.extract.documents.document import Entity
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


# def _sanitize_extractionproposals(extractionproposals: list[ExtractProposal]) -> list[ExtractProposal]:
#     """Remove potentially sensitive information."""

#     for extractionproposal in extractionproposals:
#         if extractionproposal.partners is not None:
#             extractionproposal.partners.partnertable = {}
#             extractionproposal.partners.ner_text = {}
#             extractionproposal.partners.ner_title = {}
#         extractionproposal.projectname = None
#     return extractionproposals


# @mark.anyio(scope="module")
# @mark.parametrize(
#     "do_exclude_entities_unknown,len_extractionproposals_expected,len_projectnames_nonempty_expected",
#     [
#         param(True, 27, 23, id="ner"),
#     ],
# )
# @mark.sensitive(reason="The dataset is real and not sanitized.")
# @mark.slow(reason="Runs pipeline over substantial dataset.")
# async def test_pipeline_proposalextraction_all_real(
#     *,
#     configuration: Configuration,
#     datalayer: Datalayer,
#     do_exclude_entities_unknown: bool,
#     len_extractionproposals_expected: int,
#     len_projectnames_nonempty_expected: int,
# ) -> None:
#     pipelinedocuments = PipelineDocuments(configuration=configuration)
#     assert configuration.paths.path_dir_testdata is not None
#     path_dir_document = Path(configuration.paths.path_dir_testdata) / "documents"
#     paths_file_proposal = [
#         path_file_document._path
#         async for path_file_document in path_dir_document.glob("**/*.*")
#         if await path_file_document.is_file()
#         and path_file_document.suffix in {".json", ".docx", ".html", ".md", ".pdf", ".pptx", ".xlsx"}
#     ]
#     async with datalayer.dataaccessor_qdrant as connection_qdrant:
#         hashvalues_proposal: list[Uint64] = [
#             await connection_qdrant.insert_document(doclingdocument=doclingdocument)
#             for doclingdocument in pipelinedocuments.produce_doclingdocuments(sources=paths_file_proposal)
#             if isinstance(doclingdocument, DoclingDocument)
#         ]
#     extractorpartner = ExtractorPartner(
#         do_exclude_entities_unknown=do_exclude_entities_unknown,
#         entities_known={
#             Entity(entitytype="ORG", value="ABE"): None,
#             Entity(entitytype="ORG", value="AFEM"): None,
#             Entity(entitytype="ORG", value="AIM"): None,
#             Entity(entitytype="ORG", value="AMM"): None,
#             Entity(entitytype="ORG", value="AOO"): None,
#             Entity(entitytype="ORG", value="Fontys"): None,
#             Entity(entitytype="ORG", value="HAN"): None,
#             Entity(entitytype="ORG", value="M-BIS"): None,
#             Entity(entitytype="ORG", value="Saxion"): None,
#         },
#     )
#     pipelineproposalextraction = ExtractorProposal(
#         extractorpartner=extractorpartner,
#         dataacccessor_qdrant=datalayer.dataaccessor_qdrant,
#         pipelinedocuments=pipelinedocuments,
#     )
#     extractionproposals: list[ExtractProposal] = [
#         result
#         async for result in aiter(pipelineproposalextraction.extract(hashvalues_document=iter(hashvalues_proposal)))
#         if isinstance(result, ExtractProposal)
#     ]
#     assert len(extractionproposals) == len_extractionproposals_expected
#     len_projectnames_nonempty_actual = sum(
#         extractionproposal.projectname is not None for extractionproposal in extractionproposals
#     )
#     assert len_projectnames_nonempty_actual == len_projectnames_nonempty_expected
#     # TODO: Store and use complete unsanitized output along with sensitive data for better verification and debugging.
#     extractionproposals_sanitized_actual = _sanitize_extractionproposals(extractionproposals)
#     extractionproposals_sanitized_actual.sort()
#     extractionproposals_sanitized_expected = [
#         ExtractProposal(
#             hashvalue_proposal=213832331561328109,
#             partners=Entitysource(
#                 ner_text={},
#                 ner_title={},
#                 partners_known_text={Entity(entitytype="ORG", value="HAN"): None},
#                 partnertable={},
#             ),
#             projectname=None,
#         ),
#         ExtractProposal(
#             hashvalue_proposal=789438209138016551,
#             partners=Entitysource(
#                 ner_text={},
#                 ner_title={},
#                 partners_known_text={
#                     Entity(entitytype="ORG", value="AIM"): None,
#                     Entity(entitytype="ORG", value="AOO"): None,
#                     Entity(entitytype="ORG", value="HAN"): None,
#                 },
#                 partnertable={},
#             ),
#             projectname=None,
#         ),
#         ExtractProposal(
#             hashvalue_proposal=1539181222517994919,
#             partners=Entitysource(
#                 ner_text={},
#                 ner_title={},
#                 partners_known_text={Entity(entitytype="ORG", value="HAN"): None},
#                 partnertable={},
#             ),
#             projectname=None,
#         ),
#         ExtractProposal(
#             hashvalue_proposal=1590813886619085518,
#             partners=Entitysource(
#                 ner_text={},
#                 ner_title={},
#                 partners_known_text={
#                     Entity(entitytype="ORG", value="AIM"): None,
#                     Entity(entitytype="ORG", value="HAN"): None,
#                 },
#                 partnertable={},
#             ),
#             projectname=None,
#         ),
#         ExtractProposal(
#             hashvalue_proposal=1674558765661315085,
#             partners=Entitysource(
#                 ner_text={},
#                 ner_title={},
#                 partners_known_text={
#                     Entity(entitytype="ORG", value="HAN"): None,
#                     Entity(entitytype="ORG", value="M-BIS"): None,
#                 },
#                 partnertable={},
#             ),
#             projectname=None,
#         ),
#         ExtractProposal(
#             hashvalue_proposal=1899050717071356914,
#             partners=Entitysource(
#                 ner_text={},
#                 ner_title={},
#                 partners_known_text={
#                     Entity(entitytype="ORG", value="HAN"): None,
#                     Entity(entitytype="ORG", value="Saxion"): None,
#                 },
#                 partnertable={},
#             ),
#             projectname=None,
#         ),
#         ExtractProposal(
#             hashvalue_proposal=2520273719576448581,
#             partners=Entitysource(
#                 ner_text={},
#                 ner_title={},
#                 partners_known_text={
#                     Entity(entitytype="ORG", value="AIM"): None,
#                     Entity(entitytype="ORG", value="Fontys"): None,
#                     Entity(entitytype="ORG", value="HAN"): None,
#                     Entity(entitytype="ORG", value="Saxion"): None,
#                 },
#                 partnertable={},
#             ),
#             projectname=None,
#         ),
#         ExtractProposal(
#             hashvalue_proposal=3581710487380314433,
#             partners=Entitysource(
#                 ner_text={},
#                 ner_title={},
#                 partners_known_text={Entity(entitytype="ORG", value="HAN"): None},
#                 partnertable={},
#             ),
#             projectname=None,
#         ),
#         ExtractProposal(
#             hashvalue_proposal=6008615558467939302,
#             partners=Entitysource(
#                 ner_text={},
#                 ner_title={},
#                 partners_known_text={
#                     Entity(entitytype="ORG", value="AMM"): None,
#                     Entity(entitytype="ORG", value="HAN"): None,
#                     Entity(entitytype="ORG", value="Saxion"): None,
#                 },
#                 partnertable={},
#             ),
#             projectname=None,
#         ),
#         ExtractProposal(
#             hashvalue_proposal=6663550341772802039,
#             partners=Entitysource(
#                 ner_text={},
#                 ner_title={},
#                 partners_known_text={
#                     Entity(entitytype="ORG", value="HAN"): None,
#                     Entity(entitytype="ORG", value="M-BIS"): None,
#                 },
#                 partnertable={},
#             ),
#             projectname=None,
#         ),
#         ExtractProposal(
#             hashvalue_proposal=7644999284643639226,
#             partners=Entitysource(
#                 ner_text={},
#                 ner_title={},
#                 partners_known_text={Entity(entitytype="ORG", value="HAN"): None},
#                 partnertable={},
#             ),
#             projectname=None,
#         ),
#         ExtractProposal(
#             hashvalue_proposal=7735048806561300108,
#             partners=Entitysource(
#                 ner_text={},
#                 ner_title={},
#                 partners_known_text={Entity(entitytype="ORG", value="HAN"): None},
#                 partnertable={},
#             ),
#             projectname=None,
#         ),
#         ExtractProposal(
#             hashvalue_proposal=10330658976642437804,
#             partners=Entitysource(
#                 ner_text={},
#                 ner_title={},
#                 partners_known_text={
#                     Entity(entitytype="ORG", value="AIM"): None,
#                     Entity(entitytype="ORG", value="AOO"): None,
#                     Entity(entitytype="ORG", value="HAN"): None,
#                 },
#                 partnertable={},
#             ),
#             projectname=None,
#         ),
#         ExtractProposal(
#             hashvalue_proposal=10634211516186916710,
#             partners=Entitysource(
#                 ner_text={},
#                 ner_title={},
#                 partners_known_text={Entity(entitytype="ORG", value="HAN"): None},
#                 partnertable={},
#             ),
#             projectname=None,
#         ),
#         ExtractProposal(
#             hashvalue_proposal=11255246253121386277,
#             partners=Entitysource(
#                 ner_text={},
#                 ner_title={},
#                 partners_known_text={Entity(entitytype="ORG", value="HAN"): None},
#                 partnertable={},
#             ),
#             projectname=None,
#         ),
#         ExtractProposal(
#             hashvalue_proposal=12228086479849864284,
#             partners=Entitysource(
#                 ner_text={},
#                 ner_title={},
#                 partners_known_text={
#                     Entity(entitytype="ORG", value="HAN"): None,
#                     Entity(entitytype="ORG", value="Saxion"): None,
#                 },
#                 partnertable={},
#             ),
#             projectname=None,
#         ),
#         ExtractProposal(
#             hashvalue_proposal=12277141746804254125,
#             partners=Entitysource(
#                 ner_text={},
#                 ner_title={},
#                 partners_known_text={
#                     Entity(entitytype="ORG", value="ABE"): None,
#                     Entity(entitytype="ORG", value="AMM"): None,
#                     Entity(entitytype="ORG", value="Fontys"): None,
#                     Entity(entitytype="ORG", value="HAN"): None,
#                     Entity(entitytype="ORG", value="Saxion"): None,
#                 },
#                 partnertable={},
#             ),
#             projectname=None,
#         ),
#         ExtractProposal(
#             hashvalue_proposal=12868311516057950368,
#             partners=Entitysource(
#                 ner_text={},
#                 ner_title={},
#                 partners_known_text={
#                     Entity(entitytype="ORG", value="HAN"): None,
#                     Entity(entitytype="ORG", value="M-BIS"): None,
#                     Entity(entitytype="ORG", value="Saxion"): None,
#                 },
#                 partnertable={},
#             ),
#             projectname=None,
#         ),
#         ExtractProposal(
#             hashvalue_proposal=13005709939125361404,
#             partners=Entitysource(
#                 ner_text={},
#                 ner_title={},
#                 partners_known_text={Entity(entitytype="ORG", value="HAN"): None},
#                 partnertable={},
#             ),
#             projectname=None,
#         ),
#         ExtractProposal(
#             hashvalue_proposal=13570027672830659665,
#             partners=Entitysource(
#                 ner_text={},
#                 ner_title={},
#                 partners_known_text={
#                     Entity(entitytype="ORG", value="Fontys"): None,
#                     Entity(entitytype="ORG", value="HAN"): None,
#                     Entity(entitytype="ORG", value="Saxion"): None,
#                 },
#                 partnertable={},
#             ),
#             projectname=None,
#         ),
#         ExtractProposal(
#             hashvalue_proposal=14189373083231234855,
#             partners=Entitysource(
#                 ner_text={},
#                 ner_title={},
#                 partners_known_text={
#                     Entity(entitytype="ORG", value="AIM"): None,
#                     Entity(entitytype="ORG", value="HAN"): None,
#                 },
#                 partnertable={},
#             ),
#             projectname=None,
#         ),
#         ExtractProposal(
#             hashvalue_proposal=14686230221919554270,
#             partners=Entitysource(
#                 ner_text={},
#                 ner_title={},
#                 partners_known_text={
#                     Entity(entitytype="ORG", value="HAN"): None,
#                     Entity(entitytype="ORG", value="M-BIS"): None,
#                 },
#                 partnertable={},
#             ),
#             projectname=None,
#         ),
#         ExtractProposal(
#             hashvalue_proposal=15252477857689695975,
#             partners=Entitysource(
#                 ner_text={},
#                 ner_title={},
#                 partners_known_text={Entity(entitytype="ORG", value="HAN"): None},
#                 partnertable={},
#             ),
#             projectname=None,
#         ),
#         ExtractProposal(
#             hashvalue_proposal=16478457214566589597,
#             partners=Entitysource(
#                 ner_text={},
#                 ner_title={},
#                 partners_known_text={
#                     Entity(entitytype="ORG", value="Fontys"): None,
#                     Entity(entitytype="ORG", value="HAN"): None,
#                 },
#                 partnertable={},
#             ),
#             projectname=None,
#         ),
#         ExtractProposal(
#             hashvalue_proposal=16498317577571498963,
#             partners=Entitysource(
#                 ner_text={},
#                 ner_title={},
#                 partners_known_text={Entity(entitytype="ORG", value="HAN"): None},
#                 partnertable={},
#             ),
#             projectname=None,
#         ),
#         ExtractProposal(
#             hashvalue_proposal=17540234248362979646,
#             partners=Entitysource(
#                 ner_text={},
#                 ner_title={},
#                 partners_known_text={Entity(entitytype="ORG", value="HAN"): None},
#                 partnertable={},
#             ),
#             projectname=None,
#         ),
#         ExtractProposal(
#             hashvalue_proposal=18033176377441516780,
#             partners=Entitysource(ner_text={}, ner_title={}, partners_known_text={}, partnertable={}),
#             projectname=None,
#         ),
#     ]
#     assert extractionproposals_sanitized_expected == extractionproposals_sanitized_actual
