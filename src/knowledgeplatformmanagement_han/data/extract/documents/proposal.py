from typing import ClassVar

# TODO: See https://github.com/DS4SD/docling/issues/614
from docling_core.types.doc import DoclingDocument  # type: ignore[attr-defined]
from knowledgeplatformmanagement_generic.data.extract.documents.document import Document
from knowledgeplatformmanagement_generic.settings import Configuration
from loguru import logger


class Proposal(Document):
    LENGTH_MINIMAL_PROJECTNAME: ClassVar[int] = 3

    def __init__(self, *, configuration: Configuration, doclingdocument: DoclingDocument) -> None:
        super().__init__(configuration=configuration, doclingdocument=doclingdocument)
        self.projectname: str | None
        self._extract_projectname()
        self.summarize()

    def _extract_projectname(self) -> None:
        """
        Extract the Project name from a Research Project Proposal using the first non-summary, non-structural section
        title. Otherwise, use the text on the frontpage.
        """
        if not (sectiontitles := tuple(self.sectiontitle_to_flatsection.keys())):
            self.projectname = None
            return
        if (
            # The number two is logical, since `sectiontitles[1]` is accessed.
            len(sectiontitles) >= 2  # noqa: PLR2004
            and (
                # Remove punctuation from section title to increase chances of a match.
                sectiontitle_projectname := "".join(
                    character
                    for character in " ".join(sectiontitles[1 if not sectiontitles[0] else 0].split())
                    if character.isalnum() or character == " "
                )
            )
            and len(sectiontitle_projectname) > self.LENGTH_MINIMAL_PROJECTNAME
            and not any(
                sectiontitle_summary in sectiontitle_projectname for sectiontitle_summary in self.SECTIONTITLES_SUMMARY
            )
            and not any(
                sectiontitle_structural in sectiontitle_projectname
                for sectiontitle_structural in self.SECTIONTITLES_STRUCTURAL
            )
        ):
            logger.debug("Extracting project name ‘{}’ from first section heading.", sectiontitle_projectname)
            self.projectname = sectiontitle_projectname or None
            return
        # Guess that the first text on the front page is the project name.
        if text_frontpage := self.sectiontitle_to_flatsection[sectiontitles[0]].text:
            paragraph_first, _, _ = text_frontpage.partition("\n")
            if len(paragraph_first) > self.LENGTH_MINIMAL_PROJECTNAME:
                logger.debug(
                    "No potentially relevant frontpage section heading. Extracting project name ‘{}’ from frontpage "
                    "text.",
                    paragraph_first,
                )
                self.projectname = paragraph_first or None
                return
        line_first = self.text_full.partition("\n")[0].strip()
        projectname = line_first if len(line_first) > self.LENGTH_MINIMAL_PROJECTNAME else None
        logger.debug(
            "No potentially relevant frontpage section heading or frontpage text of at least the minimal project name "
            "length. Extracting project name ‘{}’ as first line of full document text, or the empty string if there’s "
            "none.",
            projectname,
        )
        self.projectname = projectname or None
