from collections.abc import Mapping
from typing import ClassVar

from knowledgeplatformmanagement_generic.data.extract.documents.document import (
    Entities,
    Entity,
    Entitytype,
    Flatsection,
)
from loguru import logger
from numpy import str_
from pandas import RangeIndex
from pydantic import BaseModel, Field

from knowledgeplatformmanagement_han.data.extract.documents.proposal import Proposal


class Entitysource(BaseModel):
    """Entities along with their source in a Proposal. The attributes are of `dict` type, but used as efficient ordered
    sets."""

    ner_text: dict[Entity, None] = Field(default_factory=dict)
    """Entities extracted from NER on section text."""
    ner_title: dict[Entity, None] = Field(default_factory=dict)
    """Entities extracted from NER on section titles."""
    partners_known_text: dict[Entity, None] = Field(default_factory=dict)
    """Entities extracted given the known partners in text."""
    partnertable: dict[Entity, None] = Field(default_factory=dict)
    """Entities extracted from the partner table."""


class ExtractorPartnerExclusionError(ValueError):
    def __init__(self) -> None:
        super().__init__("Unknown entities can only be excluded if at least one known entity was specified. ")


class ExtractorPartnerSelectionError(ValueError):
    def __init__(self) -> None:
        super().__init__("At least one entity type must be selected. ")


# This class is simple, single-responsibility so we don't need many public methods.
# pylint: disable-next=too-few-public-methods
class ExtractorPartner:
    """
    Extract Named Entities that stand for Research Project Partners using string matching, partner tables parsing and
    NER.
    """

    # TODO: Parameterize, map to language.
    SECTIONTITLES_INCLUDED: ClassVar[dict[str, None]] = {
        "aanvragers": None,
        "Aanvragers": None,
        "AANVRAGERS": None,
        "consortium": None,
        "Consortium": None,
        "CONSORTIUM": None,
        "consortiumvorming": None,
        "Consortiumvorming": None,
        "CONSORTIUMVORMING": None,
        "netwerkvorming": None,
        "Netwerkvorming": None,
        "NETWERKVORMING": None,
        "partners": None,
        "Partners": None,
        "PARTNERS": None,
        "samenwerkingsverband": None,
        "Samenwerkingsverband": None,
        "SAMENWERKINGSVERBAND": None,
    }
    # See e.g.: https://spacy.io/models/en#en_core_news_lg-labels
    # TODO: GPE, PERSON?
    ENTITYTYPES_INCLUDED: ClassVar[tuple[Entitytype, ...]] = (
        "ORG",
        "NORP",
    )

    def __init__(
        self,
        *,
        do_exclude_entities_unknown: bool = True,
        do_exclude_entities_unknown_partner_tables: bool = False,
        entities_known: Entities | None = None,
        entitytypes_included: tuple[Entitytype, ...] = ENTITYTYPES_INCLUDED,
        sectiontitles_selected: dict[str, None] = SECTIONTITLES_INCLUDED,
    ) -> None:
        """
        Args:

            `do_exclude_entities_unknown`: Exclude entities not in `entities_known`. This implies that NER won't be
                used.
            `do_exclude_entities_unknown_partner_tables`: Also exclude entities not in `entities_known` sourced from
                partner table.
            `entities_known`: Known partners to extracting.
            `entitytypes_included`: Entity types to search for.
            `sectiontitles_selected`: List of section titles to extract entities from.
        """
        self._do_exclude_entities_unknown_partner_tables = do_exclude_entities_unknown_partner_tables
        self._do_exclude_entities_unknown = do_exclude_entities_unknown
        self._entities_known = entities_known
        self._entitytypes_included = entitytypes_included
        if not self._entitytypes_included:
            raise ExtractorPartnerSelectionError()
        self._sectiontitles_selected = sectiontitles_selected
        if not entities_known and do_exclude_entities_unknown:
            raise ExtractorPartnerExclusionError()

    # For now, I see no opportunity to simplify this further.
    def _from_partner_tables(  # noqa: C901, PLR0912
        self,
        *,
        proposal: Proposal,
        entitysource: Entitysource,
        sectiontitle_filtered_to_flatsection: Mapping[str, Flatsection],
    ) -> Entitysource:
        """
        For any tables in the document, check if they have a column with a name that contains `"partner"` and extract
        partners from there verbatim.
        """
        # TODO: Determine entitytype rather than picking the first from
        # `self._entitytypes_included`.
        entitytype = next(iter(self._entitytypes_included))
        # pylint: disable-next=too-many-nested-blocks
        for sectiontitle, flatsection in sectiontitle_filtered_to_flatsection.items():
            if flatsection.tables:
                header_first = flatsection.tables[0].columns
                for table in flatsection.tables:
                    # Reuse headers within section for tables without headers, because of merged cells.
                    # Mypy fails to detect that `table.columns` can be more than `Index`, namely `RangeIndex`.
                    if isinstance(table.columns, RangeIndex) and len(table.columns) == len(  # type: ignore[unreachable]
                        header_first,
                    ):
                        table.columns = header_first  # type: ignore[unreachable]
                    columnnames = (
                        table.columns
                        if all(isinstance(columnname_relevant, str) for columnname_relevant in table.columns)
                        else table.iloc[0].to_numpy(dtype=str_)
                    )
                    for index_column, name_column in enumerate(columnnames):
                        if "partner" in name_column.lower():
                            logger.debug(
                                "Found partner table column named ‘{}’ in section titled ‘{}’.",
                                name_column,
                                sectiontitle,
                            )
                            # Complicated to logic to deal with fact that table headers are sometimes detected, but
                            # sometimes regarded as content cells.
                            partners_maybe: list[str] = [
                                Proposal.normalize_string(text=partner_maybe_raw)
                                for partner_maybe_raw in table[name_column if name_column in table else index_column]
                                .iloc[1:]
                                .astype(str)
                            ]
                            for partner_maybe in partners_maybe:
                                partners = []
                                # TODO: Support additional separators.
                                if "," in partner_maybe:
                                    partners = partner_maybe.split(sep=",")
                                elif not partners and (value := partner_maybe.strip()):
                                    partners.append(value)
                                else:
                                    continue
                                entitysource.partnertable.update(
                                    (entity, None)
                                    for partner in partners
                                    if (
                                        (
                                            entity := Entity(
                                                entitytype=entitytype,
                                                value=partner.strip(),
                                            ),
                                        )
                                        and entity.value
                                        and not self._do_exclude_entities_unknown_partner_tables
                                        # Exclude numeric
                                        and not entity.value.lstrip("-")
                                        .replace(".", "")
                                        .replace(",", "")
                                        .replace(" ", "")
                                        .isdigit()
                                    )
                                    or (
                                        self._do_exclude_entities_unknown_partner_tables
                                        and self._entities_known is not None
                                        and entity not in self._entities_known
                                    )
                                )

        if not entitysource.partnertable and len(sectiontitle_filtered_to_flatsection) == 1 and self._entities_known:
            logger.debug(
                "Partner table not found, but Proposal consists of a single (quasi frontpage) section. Extracting known"
                " partners from Markdown export of this table.",
            )
            for flatsection in sectiontitle_filtered_to_flatsection.values():
                for table in flatsection.tables:
                    table_str = Proposal.normalize_string(text=table.to_markdown(), keep_newlines=True)
                    # TODO: Is this replace needed, and if so, can this be done among other replaces at a single time?
                    text = " ".join(cell.strip().replace("-", "").replace(":", "") for cell in table_str.split(sep="|"))
                    text_tokenized = proposal._language_to_nermodel[proposal.language](text)
                    words = frozenset({token.text.replace("-", " ") for token in text_tokenized if token.is_alpha})
                    entitysource.partnertable.update(
                        (partner, None)
                        for partner in self._entities_known
                        if partner.value in words or partner.value in text
                    )
        return entitysource

    def _from_text_using_partners_known(
        self,
        *,
        entitysource: Entitysource,
        proposal: Proposal,
    ) -> Entitysource:
        """Extract known partners from full document text (without table text) using string matching."""
        # Collect all words (tokenized).
        if self._entities_known:
            # TODO: Is this replace needed, and if so, can this be done among other replaces at a single time?
            words = frozenset({token.text.replace("-", " ") for token in proposal.text_tokenized if token.is_alpha})
            entitysource.partners_known_text.update(
                (partner, None)
                for partner in self._entities_known
                if partner.value in words or partner.value in proposal.text_full
            )
        return entitysource

    def _from_sectiontitles_using_ner(
        self,
        proposal: Proposal,
        entitysource: Entitysource,
    ) -> Entitysource:
        """Extract partners from `proposal`’s section titles using NER."""
        proposal.perform_ner_titles()
        entitysource.ner_title.update(
            (entity, None)
            for entities in proposal.sectiontitle_to_entities_title.values()
            for entity in entities
            if self._keep(entity)
        )
        return entitysource

    def _from_texts_selected_using_ner(
        self,
        proposal: Proposal,
        sectiontitle_selected_to_flatsection: Mapping[str, Flatsection],
        entitysource: Entitysource,
    ) -> Entitysource:
        """Extract partners from `proposal`’s section texts in `sectiontitle_filtered_to_flatsection` using NER."""
        proposal.perform_ner_texts(
            sectiontitle_selected_to_flatsection=sectiontitle_selected_to_flatsection,
        )
        entitysource.ner_text.update(
            (entity, None)
            for entities in proposal.sectiontitle_to_entities_text.values()
            for entity in entities
            if self._keep(entity)
        )
        return entitysource

    def _keep(self, entity: Entity) -> bool:
        """Determine whether an entity should be excluded or included as a Partner if they weren't known before (if so
            configured).

        Returns:
            bool: `True` if the entity meets all conditions for excluding or including, `False` otherwise.

        Args:
            entity: The entity to be excluded or included.
        """
        return entity.entitytype in self._entitytypes_included and (
            not self._do_exclude_entities_unknown
            or (
                self._do_exclude_entities_unknown
                and self._entities_known is not None
                and entity in self._entities_known
            )
        )

    def _from_all(
        self,
        *,
        proposal: Proposal,
        sectiontitle_selected_to_flatsection: Mapping[str, Flatsection],
    ) -> Entitysource | None:
        """Extracts partner entities from various sources within the proposal.

        Combines extraction methods to gather partners from known entities, tables, section titles, and section texts.
        If `self._do_exclude_entities_unknown == False`, also uses NER to find partners.

        Args:
            `proposal`: The Research Proposal document.
            `sectiontitle_filtered_to_flatsection`: Mapping of section titles to their corresponding `Flatsection`
            objects.

        Returns:
            An `Entitysource` object containing extracted partners, or `None` if no suitable sources are available
            (e.g., a section-less and also table-less document).
        """
        entitysource = Entitysource()
        if not sectiontitle_selected_to_flatsection:
            logger.error("No text, sections or tables to extract partners from.")
            return None
        entitysource = self._from_text_using_partners_known(entitysource=entitysource, proposal=proposal)
        entitysource = self._from_partner_tables(
            entitysource=entitysource,
            proposal=proposal,
            sectiontitle_filtered_to_flatsection=sectiontitle_selected_to_flatsection,
        )
        # Only perform NER if we aren't supposed to exclude unknown entities, since otherwise searching for
        # exact matches given the known partner set suffices.
        if not self._do_exclude_entities_unknown:
            entitysource = self._from_sectiontitles_using_ner(entitysource=entitysource, proposal=proposal)
            entitysource = self._from_texts_selected_using_ner(
                entitysource=entitysource,
                proposal=proposal,
                sectiontitle_selected_to_flatsection=sectiontitle_selected_to_flatsection,
            )
        return entitysource

    def run(
        self,
        *,
        proposal: Proposal,
    ) -> Entitysource | None:
        """
        Main pipeline method that processes a Research Proposal.

        Args:
            proposal: The Research Proposal.
        """
        sectiontitle_selected_to_flatsection = proposal.extract_texts_and_tables_selected(
            sectiontitles_selected=self._sectiontitles_selected,
        )
        return self._from_all(
            proposal=proposal,
            sectiontitle_selected_to_flatsection=sectiontitle_selected_to_flatsection,
        )
