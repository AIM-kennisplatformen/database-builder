from datetime import date
from enum import Enum, IntEnum, unique
from re import Pattern
from re import compile as re_compile
from typing import Annotated, ClassVar, Final
from zoneinfo import ZoneInfo

from annotated_types import Ge, Le
from pydantic import AfterValidator, BaseModel, StringConstraints
from pydantic.types import FiniteFloat

from knowledgeplatformmanagement_han.data.model.educationalproject import Educationalproject
from knowledgeplatformmanagement_han.data.model.namelike_id_school import NamelikeIdSchool
from knowledgeplatformmanagement_han.data.model.operationalproject import Operationalproject
from knowledgeplatformmanagement_han.data.model.projectlike import ProjectclassifierFinancial, Projectstatus
from knowledgeplatformmanagement_han.data.model.researchproject import Researchproject
from knowledgeplatformmanagement_han.data.model.strategicpartnership import Strategicpartnership
from knowledgeplatformmanagement_han.data.model.unclearproject import Unclearproject


@unique
class RHA025A(IntEnum):
    medewerkerid = 1
    naammedewerker = 3
    projectid = 11
    projectmanager = 5
    project_status_nl = 12
    projectnaam = 13
    deelprojectid = 14
    deelproject_status_nl = 15
    deelprojectnaam = 16
    namelike_id_ubwcostcentre_project = 18
    registratiedatum = 20
    geboekte_uren = 21
    projecttypecode = 23
    employmentcontract_ftepercentage = 26
    namelike_id_school = 33
    namelike_department = 36
    namelike_id_ubwcostcentre_employee = 38


@unique
class IB630(IntEnum):
    projectid = 0
    projectnaam = 1
    naammedewerker = 2
    begrote_uren = 3
    prognose_uren = 4
    geboekte_uren = 5
    periode = 6
    resterende_uren = 7
    namelike_id_ubwcostcentre_project = 8


# TODO: Rename.
@unique
class IB630Withoutbooked(IntEnum):
    projectid = 0
    projectnaam = 1
    naammedewerker = 2
    begrote_uren = 3
    prognose_uren = 4
    periode = 6
    resterende_uren = 7
    namelike_id_ubwcostcentre_project = 8


_STR_REGEX_PROJECTID: Final[str] = "[a-zA-ZÌ]{2,3}[0-9]{3,6}"
REGEX_PROJECTID_1: Final[Pattern[str]] = re_compile("([a-zA-ZÌ]{2,3})[0-9]{4,6}")
REGEX_PROJECTID_2: Final[Pattern[str]] = re_compile(_STR_REGEX_PROJECTID)
REGEX_DEELPROJECTID: Final[Pattern[str]] = re_compile(_STR_REGEX_PROJECTID + "-[0-9]{0,3}")


def validate_projecttypecode(projecttypecode: str) -> str:
    if projecttypecode in ProjecttypeToProjecttypeinfo.__members__:
        return projecttypecode
    raise ValueError()


def validate_projectid(projectid: str) -> str:
    if REGEX_PROJECTID_2.fullmatch(projectid):
        return projectid
    raise ValueError()


def validate_deelprojectid(deelprojectid: str) -> str:
    if REGEX_DEELPROJECTID.fullmatch(deelprojectid):
        return deelprojectid
    raise ValueError()


class Row(BaseModel):
    namelike_id_ubwcostcentre_project: Annotated[str, StringConstraints(min_length=1)]
    projectnaam: Annotated[str, StringConstraints(min_length=1)]
    naammedewerker: Annotated[str, StringConstraints(min_length=1)]
    projectid: Annotated[str, AfterValidator(validate_projectid)]


# The row has this many instance attributes.
# pylint: disable-next=too-many-instance-attributes
class RowRHA025A(Row):
    namelike_id_ubwcostcentre_employee: Annotated[str, StringConstraints(min_length=1)]
    deelproject_status_nl: Projectstatus
    deelprojectid: Annotated[str, AfterValidator(validate_deelprojectid)]
    deelprojectnaam: Annotated[str, StringConstraints(min_length=1)]
    employmentcontract_ftepercentage: Annotated[int, Ge(0), Le(100)] | None
    geboekte_uren: FiniteFloat
    medewerkerid: Annotated[str, StringConstraints(min_length=1)]
    namelike_department: Annotated[str, StringConstraints(min_length=1)]
    namelike_id_school: NamelikeIdSchool
    project_status_nl: Projectstatus
    projectmanager: Annotated[str, StringConstraints(min_length=1)]
    projecttypecode: Annotated[str, validate_projecttypecode]
    registratiedatum: date


class RowIB630Withoutbooked(Row):
    begrote_uren: FiniteFloat
    periode: Annotated[int, Ge(2000_00)]
    """Periode must be in year 2000 later (arbitrary, perhaps too lax)."""
    prognose_uren: FiniteFloat
    registratiedatum: date
    """Imputed from `periode`."""
    resterende_uren: FiniteFloat
    projecttypecode: Annotated[str, AfterValidator(validate_projecttypecode)]
    """Imputed from `projectid`."""


class RowIB630(RowIB630Withoutbooked):
    geboekte_uren: FiniteFloat


@unique
class FormatToNamecolumnToIndexcolumn(Enum):
    RHA025A = RHA025A
    IB630 = IB630
    IB630WithoutBooked = IB630Withoutbooked


class Projecttypeinfo(BaseModel, frozen=True):
    projectlike_subentity: Annotated[str, StringConstraints(min_length=1)]
    projectclassifier_financial: ProjectclassifierFinancial
    project_type_name_powerbi: Annotated[str, StringConstraints(min_length=1)]
    billable: bool


class ProjecttypeToProjecttypeinfo(Enum):
    CO = Projecttypeinfo(
        projectlike_subentity=Educationalproject.to_typeql_name_schema(),
        projectclassifier_financial=ProjectclassifierFinancial.contractonderwijs.value,
        project_type_name_powerbi="Contractonderwijs",
        billable=True,
    )
    IM = Projecttypeinfo(
        projectlike_subentity=Strategicpartnership.to_typeql_name_schema(),
        projectclassifier_financial=ProjectclassifierFinancial.internemarktprojecten.value,
        project_type_name_powerbi="Interne Marktprojecten",
        billable=False,
    )
    IN = Projecttypeinfo(
        projectlike_subentity=Operationalproject.to_typeql_name_schema(),
        projectclassifier_financial=ProjectclassifierFinancial.interndeclarabel.value,
        project_type_name_powerbi="Intern Declarabel",
        billable=False,
    )
    ÌD = IN  # noqa: PLC2401
    MA = Projecttypeinfo(
        projectlike_subentity=Operationalproject.to_typeql_name_schema(),
        projectclassifier_financial=ProjectclassifierFinancial.marktactiviteiten.value,
        project_type_name_powerbi="Marktactiviteiten",
        billable=True,
    )
    OM = Projecttypeinfo(
        projectlike_subentity=Researchproject.to_typeql_name_schema(),
        projectclassifier_financial=ProjectclassifierFinancial.onderzoekmarkt.value,
        project_type_name_powerbi="Onderzoek Markt",
        billable=True,
    )
    SU = Projecttypeinfo(
        projectlike_subentity=Researchproject.to_typeql_name_schema(),
        projectclassifier_financial=ProjectclassifierFinancial.subsidieprojecten.value,
        project_type_name_powerbi="Subsidieprojecten",
        billable=True,
    )
    RB = Projecttypeinfo(
        projectlike_subentity=Researchproject.to_typeql_name_schema(),
        projectclassifier_financial=ProjectclassifierFinancial.rijksbijdrage.value,
        project_type_name_powerbi="Rijksbijdrage",
        billable=True,
    )
    BA = Projecttypeinfo(
        projectlike_subentity=Unclearproject.to_typeql_name_schema(),
        projectclassifier_financial=ProjectclassifierFinancial.empty,
        project_type_name_powerbi="Onbekend",
        billable=False,
    )
    AS = KP = BA


class ConfigurationTimesheets(BaseModel):
    # TODO: Use user-configurable configuration system.
    ZONEINFO_UBWFRIS: ClassVar[ZoneInfo] = ZoneInfo("Europe/Amsterdam")
