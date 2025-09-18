from datetime import date
from enum import StrEnum, auto, unique
from typing import Annotated

from knowledgeplatformmanagement_generic.data.services.typedb.typeql import TypeqlThingEntity
from pydantic import ConfigDict, Field, FiniteFloat, StringConstraints

from knowledgeplatformmanagement_han.data.model.description import Description
from knowledgeplatformmanagement_han.data.model.namelike_id_ubwcostcentre import NamelikeIdUbwcostcentre
from knowledgeplatformmanagement_han.data.model.namelike_name import NamelikeName


@unique
class ProjectclassifierStatus(StrEnum):
    completed = auto()
    ongoing = auto()
    smfmatching = auto()
    smfseed = auto()


# Accept the non-ASCII enum name, since it’s true to the data and not confusing.
class Projectstatus(StrEnum):
    Actief = "ongoing"
    Afgesloten = "completed"
    Beëindigd = "completed"  # noqa: PLC2401


@unique
class ProjectclassifierFinancial(StrEnum):
    contractonderwijs = "contractonderwijs"
    empty = ""
    interndeclarabel = "intern-declarabel"
    internemarktprojecten = "interne-marktprojecten"
    marktactiviteiten = "marktactiviteiten"
    onderzoekmarkt = "onderzoekmarkt"
    rijksbijdrage = "rijksbijdrage"
    subsidieprojecten = "subsidieprojecten"


# This is a dataclass and I see no reason to require fewer instance attributes.
# pylint: disable-next=too-many-instance-attributes
class Projectlike(TypeqlThingEntity):
    model_config = ConfigDict(title="project")

    budget: FiniteFloat | None = Field(default=None, title="budget")
    date_event_end: date = Field(title="project end date")
    date_event_start: date = Field(title="project start date")
    description: Description | None = Field(default=None, title="description")
    namelike_id_ubwcostcentre: NamelikeIdUbwcostcentre = Field(title="UBW FRIS cost centre")
    # Cannot be reused as typedef in combination with "key" due to
    # https://docs.pydantic.dev/latest/internals/resolving_annotations/.
    namelike_id_ubw: Annotated[
        str,
        "key",
        StringConstraints(
            pattern=r"^[a-zA-ZÌ]{2,3}[0-9]{3,6}[\-]{0,1}[0-9]{0,3}$",
        ),
    ] = Field(title="UBW FRIS project ID")
    namelike_name: NamelikeName = Field(title="UBW FRIS project ID")
    projectclassifier_financial: ProjectclassifierFinancial = Field(title="UBW FRIS financial classifier")
    projectclassifier_status: ProjectclassifierStatus | None = Field(
        default=None,
        title="UBW FRIS status classifier",
    )
