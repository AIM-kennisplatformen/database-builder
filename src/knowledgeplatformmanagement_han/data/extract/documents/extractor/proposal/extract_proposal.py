from typing import Annotated

from docling_core.types.doc.document import Uint64
from pydantic import RootModel, StringConstraints
from pydantic.dataclasses import dataclass

from knowledgeplatformmanagement_han.data.extract.documents.extractor.partner.extractor_partner import Entitysource


@dataclass(kw_only=True, order=True)
class ExtractProposal:
    """
    A structured representation of Research Project Proposal extraction results.

    Attributes:
        `hashvalue_proposal`: Integer hash value of Proposal Docling document.
        `partners`: A semicolon-separated list of Partners, or `None`, if the document turned out unsuitable for Partner
        extraction (see `ExtractorPartner`.)
        `projectname`: The name of the Project.
    """

    hashvalue_proposal: Uint64
    partners: Entitysource | None = None
    projectname: Annotated[str, StringConstraints(min_length=1)] | None = None

    def __str__(self) -> str:
        return (
            f"Project: {self.projectname or '<None>'}; "
            f"Partners: {self.partners}; "
            f"Proposal integer hash value: {self.hashvalue_proposal}."
        )


ExtractProposals = RootModel[list[ExtractProposal]]
