from collections.abc import Collection, Mapping
from pathlib import Path
from typing import ClassVar
from unicodedata import category, normalize

# TODO: See https://github.com/DS4SD/docling/issues/614
from docling_core.types.doc import DoclingDocument, SectionHeaderItem, TableItem, TextItem  # type: ignore[attr-defined]

# TODO: See https://github.com/pemistahl/lingua/issues/243
# pylint: disable-next=no-name-in-module
from lingua import Language, LanguageDetectorBuilder
from loguru import logger
from pandas import DataFrame
from pydantic.dataclasses import dataclass
from spacy import load
from spacy.language import Language as LanguageSpacy
from span_marker import SpanMarkerModel

from knowledgeplatformmanagement_generic.settings import Configuration

type Entitytype = str
type Entitytypes = set[Entitytype]


# TODO: It seems some Mypy defect requires the ignore.
@dataclass(kw_only=True, order=True, unsafe_hash=True)
# This is a dataclass-like type, so custom public methods aren't expected.
# pylint: disable-next=too-few-public-methods
class Entity:
    entitytype: Entitytype
    value: str


type Entities = dict[Entity, None]


class DocumentLanguageNotdetectedError(ValueError):
    def __init__(self) -> None:
        super().__init__("Language could not be detected.")


class DocumentLanguageUnsupportedError(ValueError):
    def __init__(self, language: Language, languages: Collection[Language]) -> None:
        super().__init__(f"Language detected as {language!s}, which is not supported ({languages!s}).")


class DocumentNermodelError(RuntimeError):
    def __init__(self, *, name_framework: str, name_model: Path | str, language: Language | None) -> None:
        super().__init__(
            f"Failed to load {name_framework} NER model {name_model} for language "
            f"{language.iso_code_639_1 if language else '(not defined)'}.",
        )


# This is a dataclass-like type.
# pylint: disable-next=too-few-public-methods
class Flatsection:
    """Section text and tables in increasing reading order, flattened from a tree into a sequence."""

    def __init__(self, *, text: str = "", tables: list[DataFrame] | None = None) -> None:
        self.tables: list[DataFrame] = [] if tables is None else tables
        self.text = text

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(text={self.text.__repr__()}, "
            f"tables=[{', '.join(table.columns.__repr__() for table in self.tables)}])"
        )


# The instance attributes are constants, and essential. The lack of public methods isn't a problem, since this a data
# class.
# pylint: disable-next=too-few-public-methods,too-many-instance-attributes
class Document:
    @staticmethod
    def normalize_string(*, text: str, keep_newlines: bool = False) -> str:
        """Normalizes strings

        Normalizes to NKFC Unicode Normalization Form, reduces whitespaces to common space character and optionally
        keeps newlines, and excludes noisy (e.g., control) characters based on Unicode General Category. Then compresses
        repeated whitespaces and newlines into single ones.

        See: https://unicode.org/reports/tr15/
        See: https://github.com/DS4SD/docling/issues/682
        """
        return ("\n" if keep_newlines else " ").join(
            character
            for character in " ".join(
                character
                for character in "".join(
                    character if category(character) != "Zl" else "\n"
                    for character in normalize("NFKC", text.replace("\t", " "))
                    if character in (" ", "\n")
                    or category(character) not in {"B", "Cc", "Cf", "Cn", "Co", "Cs", "Zp", "Zs"}
                ).split(sep=" ")
                if character
            ).split(sep="\n")
            if character
        )

    @staticmethod
    def _load_ner_model(
        *,
        modelname_spacy: Path | None,
        language: Language | None,
    ) -> LanguageSpacy | SpanMarkerModel:
        """
        Load the appropriate model for the appropriate framework (spaCy or span_marker) based on language.
        """
        if not modelname_spacy or not language:
            # TODO: parameterize.
            modelname = "tomaarsen/span-marker-mbert-base-multinerd"
            try:
                return SpanMarkerModel.from_pretrained(pretrained_model_name_or_path=modelname, local_files_only=True)
            except (TypeError, ValueError) as exception:
                raise DocumentNermodelError(
                    name_framework="span_marker",
                    name_model=modelname,
                    language=language,
                ) from exception
        try:
            return load(name=modelname_spacy)
        except Exception as exception:
            raise DocumentNermodelError(
                name_framework="spaCy",
                name_model=modelname_spacy,
                language=language,
            ) from exception

    LEN_SUMMARY_MIN: ClassVar[int] = 20
    LENGTH_SECTION_MIN: ClassVar[int] = 2
    SECTIONTITLES_SUMMARY: ClassVar[frozenset[str]] = frozenset(
        {
            "management samenvatting",
            "Management samenvatting",
            "MANAGEMENT SAMENVATTING",
            "managementsamenvatting",
            "Managementsamenvatting",
            "MANAGEMENTSAMENVATTING",
            "samenvatting",
            "Samenvatting",
            "SAMENVATTING",
            "summary",
            "Summary",
            "SUMMARY",
        },
    )
    SECTIONTITLES_STRUCTURAL: ClassVar[frozenset[str]] = frozenset(
        {
            "colofon",
            "Colofon",
            "COLOFON",
            "contents",
            "Contents",
            "CONTENTS",
            "inhoud",
            "Inhoud",
            "INHOUD",
            "inhoudsopgave",
            "Inhoudsopgave",
            "INHOUDSOPGAVE",
            "table of contents",
            "Table of contents",
            "Table of Contents",
            "TABLE OF CONTENTS",
        },
    )

    def __repr__(self) -> str:
        # TODO: enhance
        return f"{self.__class__.__name__}(language={self.language.__repr__()})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Document):
            raise NotImplementedError()
        return (
            self.language.__eq__(other.language)
            and self.summary.__eq__(other.summary)
            and self.text_full.__eq__(
                other.text_full,
            )
            and self.sectiontitle_to_entities_text.__eq__(
                other.sectiontitle_to_entities_text,
            )
            and self.sectiontitle_to_entities_title.__eq__(
                other.sectiontitle_to_entities_title,
            )
        )

    def __init__(self, *, configuration: Configuration, doclingdocument: DoclingDocument) -> None:
        self.configuration = configuration
        self.doclingdocument = doclingdocument
        self.sectiontitle_to_entities_text: dict[str, Entities] = {}
        self.sectiontitle_to_entities_title: dict[str, Entities] = {}
        self.sectiontitle_to_flatsection: dict[str, Flatsection] = {}
        self._language_to_nermodel: dict[Language, LanguageSpacy | SpanMarkerModel] = {
            Language.ENGLISH: self._load_ner_model(
                modelname_spacy=self.configuration.paths._path_dir_model_spacy_en,
                language=Language.ENGLISH,
            ),
            Language.DUTCH: self._load_ner_model(
                modelname_spacy=self.configuration.paths._path_dir_model_spacy_nl,
                language=Language.DUTCH,
            ),
        }
        self._languagedetector = (
            LanguageDetectorBuilder.from_languages(
                *self._language_to_nermodel.keys(),
            )
            .with_preloaded_language_models()
            .build()
        )
        self._is_summarized = False
        self.summary = ""
        self.text_full = Document.normalize_string(
            text=self.doclingdocument.export_to_markdown(strict_text=True),
            keep_newlines=True,
        ).replace(
            "<!-- missing-text -->",
            "",
        )
        try:
            self.language = self._detect_language(text=self.text_full)
        except (DocumentLanguageNotdetectedError, DocumentLanguageUnsupportedError):
            self.language = Language.ENGLISH
            logger.warning(
                "Failed to detect language, using default {language} for document {document}.",
                language=self.language.name,
                document=str(self),
            )
        self.text_tokenized = self._language_to_nermodel[self.language](self.text_full)
        self._extract_texts_and_tables()

    def __str__(self) -> str:
        if self.doclingdocument.origin is not None:
            return (
                f"Document '{self.doclingdocument.origin.filename}, written in {self.language.name} (integer hash value"
                f" {self.doclingdocument.origin.binary_hash})), of type {self.doclingdocument.origin.mimetype}."
            )
        return f"Document '{self.doclingdocument.name}', written in {self.language.name})."

    def _perform_ner(
        self,
        *,
        text: str,
    ) -> Entities:
        """
        Perform Named Entity Recognition (NER) on the text using a spaCy or SpanMarker model.

        Args:
            language: The language of the text.
            text: The text to process.
        """
        nermodel = self._language_to_nermodel[self.language]
        entities: dict[Entity, None] = {}
        if self.language in self._language_to_nermodel and isinstance(
            nermodel,
            LanguageSpacy,
        ):
            logger.debug("Using spaCy for NER.")
            # Use spaCy pipeline for supported languages (e.g., English).
            predictions = nermodel(text)
            for span_spacy in predictions.ents:
                if span_spacy.label_ and span_spacy.text:
                    entities[Entity(entitytype=span_spacy.label_, value=span_spacy.text)] = None
        # The nested blocks are required because of rather dynamic typing.
        # pylint: disable-next=too-many-nested-blocks
        elif isinstance(nermodel, SpanMarkerModel):
            logger.debug("Using span_marker for NER.")
            # Use SpanMarker model for unsupported languages.
            predictions = nermodel.predict(text)
            # Iterate over predictions and collect entities based on 'span' and 'label'.
            for prediction in predictions:
                if isinstance(
                    prediction,
                    Mapping,
                ):
                    if (label := prediction.get("label")) and (span := prediction.get("span")):
                        entities[Entity(entitytype=label, value=span)] = None
                    else:
                        for predictioninner in prediction:
                            if (label := predictioninner.get("label")) and (span := predictioninner.get("span")):
                                entities[Entity(entitytype=label, value=span)] = None
        return entities

    def perform_ner_texts(
        self,
        sectiontitle_selected_to_flatsection: Mapping[str, Flatsection],
    ) -> None:
        """
        Perform NER on the text of the selected sections.
        """
        for sectiontitle, flatsection in sectiontitle_selected_to_flatsection.items():
            if sectiontitle not in self.sectiontitle_to_entities_text:
                self.sectiontitle_to_entities_text[sectiontitle] = self._perform_ner(
                    text=flatsection.text,
                )

    def perform_ner_titles(self) -> None:
        """
        Perform NER on the titles of all sections.
        """
        for sectiontitle in self.sectiontitle_to_flatsection:
            if sectiontitle not in self.sectiontitle_to_entities_title:
                self.sectiontitle_to_entities_title[sectiontitle] = self._perform_ner(
                    text=sectiontitle,
                )

    def _extract_texts_and_tables(
        self,
    ) -> None:
        """
        Extract texts and tables from documents while retaining structure.
        Returns the number of sections extracted.
        """
        index_section = 0
        title_section_current = ""
        for nodeitem, _ in self.doclingdocument.iterate_items():
            match nodeitem:
                case SectionHeaderItem(text=text):
                    if (
                        title_section_current := Document.normalize_string(text=text)
                    ) and title_section_current not in self.sectiontitle_to_flatsection:
                        self.sectiontitle_to_flatsection[title_section_current] = Flatsection()
                    index_section += 1
                case TextItem(text=text) if (
                    # TODO: Why is paragraph text being compared with section titles?
                    text_section_new := Document.normalize_string(text=text)
                ):
                    # Add paragraph text, separated by a newline.
                    if title_section_current in self.sectiontitle_to_flatsection:
                        self.sectiontitle_to_flatsection[title_section_current].text += text_section_new + "\n"
                    else:
                        self.sectiontitle_to_flatsection[title_section_current] = Flatsection(
                            text=text_section_new + "\n",
                        )
                    # At least a couple of words.
                    if (
                        index_section == 1
                        and len(self.sectiontitle_to_flatsection[title_section_current].text) > self.LEN_SUMMARY_MIN
                    ):
                        self.summary += self.sectiontitle_to_flatsection[title_section_current].text
                        logger.debug("Augmented fallback summary with a paragraph from the first section.")
                case TableItem():
                    table = nodeitem.export_to_dataframe()
                    if title_section_current in self.sectiontitle_to_flatsection:
                        self.sectiontitle_to_flatsection[title_section_current].tables.append(table)
                    else:
                        self.sectiontitle_to_flatsection[title_section_current] = Flatsection(
                            tables=[table],
                        )
        logger.debug(
            "Extracted {} sections: {}.",
            len(self.sectiontitle_to_flatsection.keys()),
            tuple(self.sectiontitle_to_flatsection.keys()),
        )

    def summarize(self) -> None:
        """
        Summarizes the document (more than the fall-back summary).
        """
        if not self._is_summarized and (
            sectiontitles_summary_found := [
                sectiontitle
                for sectiontitle_summary in self.SECTIONTITLES_SUMMARY
                for sectiontitle in self.sectiontitle_to_flatsection
                if sectiontitle_summary in sectiontitle
            ]
        ):
            self.summary = "\n".join(
                self.sectiontitle_to_flatsection[sectiontitle].text for sectiontitle in sectiontitles_summary_found
            )
            self._is_summarized = True
            logger.debug("Found a {} words long summary section.", len(self.summary.split(" ")))

    # TODO: Can we avoid that we spend resources to run _extract_texts_and_tables, to then duplicate part of its data?
    # TODO: Must this method be public?
    def extract_texts_and_tables_selected(
        self,
        *,
        sectiontitles_selected: dict[str, None] | None = None,
    ) -> dict[str, Flatsection]:
        """
        Extracts flat sections based on a given list of section titles.
        If they don't exist, or if no section titles are provided returns all sections/titles
        """
        # If `sectiontitles` is provided, filter the sections based on it.
        sectiontitle_filtered_to_flatsection: dict[str, Flatsection] = {}
        if sectiontitles_selected:
            for sectiontitle, flatsection in self.sectiontitle_to_flatsection.items():
                for sectiontitle_selected in sectiontitles_selected:
                    if sectiontitle_selected.lower() in sectiontitle.lower():
                        sectiontitle_filtered_to_flatsection.setdefault(
                            sectiontitle,
                            Flatsection(),
                        ).tables = flatsection.tables
                        if len(flatsection.text) > self.LENGTH_SECTION_MIN:
                            sectiontitle_filtered_to_flatsection[sectiontitle].text = flatsection.text
            if not sectiontitle_filtered_to_flatsection:
                # If none of the selected section titles were found, simply use the entire text.
                logger.debug("No matching selected sections.")
                # TODO: Why return values that are public attributes of the object?
                return self.sectiontitle_to_flatsection
        return sectiontitle_filtered_to_flatsection

    def _detect_language(self, text: str) -> Language:
        if not (language := self._languagedetector.detect_language_of(text=text)):
            raise DocumentLanguageNotdetectedError()
        if language not in self._language_to_nermodel:
            raise DocumentLanguageUnsupportedError(language=language, languages=self._language_to_nermodel.keys())
        return language
