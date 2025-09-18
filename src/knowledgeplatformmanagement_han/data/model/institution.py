from enum import StrEnum, auto, unique
from typing import Annotated

from knowledgeplatformmanagement_generic.data.services.typedb.typeql import TypeqlThingEntity
from pydantic import ConfigDict, Field

from knowledgeplatformmanagement_han.data.model.namelike_name import NamelikeName


@unique
class LegalformNld(StrEnum):
    beslotenvennootschap = auto()
    commanditairevennootschap = auto()
    # Accept the non-ASCII enum name, since it’s true to the data and not confusing.
    coöperatie = auto()  # noqa: PLC2401
    eenmanszaak = auto()
    maatschap = auto()
    stichting = auto()
    vennootschaponderfirma = auto()
    verenigingmetbeperkterechtsbevoegdheid = auto()
    verenigingmetvolledigerechtsbevoegdheid = auto()


# TODO: Use StrEnum
type Legalform = str
type LegalformBel = Legalform
type LegalformDeu = Legalform
type LegalformFra = Legalform
type LegalformIrl = Legalform


class Institution(TypeqlThingEntity):
    model_config = ConfigDict(title="institution")

    legalform_bel: LegalformBel | None = Field(default=None, title="Belgian legal form")
    legalform_deu: LegalformDeu | None = Field(default=None, title="German legal form")
    legalform_fra: LegalformFra | None = Field(default=None, title="French legal form")
    legalform_irl: LegalformIrl | None = Field(default=None, title="Irish legal form")
    legalform_nld: LegalformNld | None = Field(default=None, title="Dutch legal form")
    namelike_name: Annotated[NamelikeName, "key"] = Field(title="name")
