from collections import ChainMap
from collections.abc import Generator
from itertools import chain
from typing import Final
from uuid import UUID

from knowledgeplatformmanagement_generic.data.services.typedb.typeql import TypeqlThing
from loguru import logger
from openpyxl.worksheet._read_only import ReadOnlyWorksheet

from knowledgeplatformmanagement_han.data.dao.dataqualityissue import Dataqualityissue
from knowledgeplatformmanagement_han.data.dao.datasink import Datasink
from knowledgeplatformmanagement_han.data.model.compositionproject import CompositionProject
from knowledgeplatformmanagement_han.data.model.educationalproject import Educationalproject
from knowledgeplatformmanagement_han.data.model.learningcommunity import Learningcommunity
from knowledgeplatformmanagement_han.data.model.operationalproject import Operationalproject
from knowledgeplatformmanagement_han.data.model.participationinternal import Participationinternal
from knowledgeplatformmanagement_han.data.model.personubwfris import PersonUbwfris
from knowledgeplatformmanagement_han.data.model.projectlike import Projectlike
from knowledgeplatformmanagement_han.data.model.projectlikes import Projectlikes
from knowledgeplatformmanagement_han.data.model.projectmanagement import Projectmanagement
from knowledgeplatformmanagement_han.data.model.researchproject import Researchproject
from knowledgeplatformmanagement_han.data.model.school import School
from knowledgeplatformmanagement_han.data.model.strategicpartnership import Strategicpartnership
from knowledgeplatformmanagement_han.data.model.subproject import Subproject
from knowledgeplatformmanagement_han.data.model.timesheet import Timesheet
from knowledgeplatformmanagement_han.data.model.unclearproject import Unclearproject
from knowledgeplatformmanagement_han.settings.timesheets import ConfigurationTimesheets


# This implements a slim interface and is a dataclass-like type.
# pylint: disable-next=too-few-public-methods, too-many-instance-attributes
class DatasinkUbwfris(Datasink):
    def __init__(self) -> None:
        self.compositionprojects: list[CompositionProject] = []
        self.configurationtimesheets = ConfigurationTimesheets()
        self.id_to_educationalproject: dict[str, Educationalproject] = {}
        self.id_to_learningcommunity: dict[str, Learningcommunity] = {}
        self.id_to_operationalproject: dict[str, Operationalproject] = {}
        self.id_to_personubwfris: dict[str, PersonUbwfris] = {}
        self.id_to_researchproject: dict[str, Researchproject] = {}
        self.id_to_school: dict[str, School] = {}
        self.id_to_strategicpartnership: dict[str, Strategicpartnership] = {}
        self.id_to_subproject: dict[str, Subproject] = {}
        self.id_to_unclearproject: dict[str, Unclearproject] = {}
        # See https://github.com/python/typeshed/issues/8430.
        self.id_to_projectlike: Final[ChainMap[str, Projectlikes]] = ChainMap(
            self.id_to_subproject,  # type: ignore[arg-type]
            self.id_to_educationalproject,  # type: ignore[arg-type]
            self.id_to_learningcommunity,  # type: ignore[arg-type]
            self.id_to_operationalproject,  # type: ignore[arg-type]
            self.id_to_researchproject,  # type: ignore[arg-type]
            self.id_to_strategicpartnership,  # type: ignore[arg-type]
            self.id_to_unclearproject,  # type: ignore[arg-type]
        )
        self.participationinternals: list[Participationinternal] = []
        self.uuid_to_persons_missing: dict[UUID, list[str]] = {}
        self.projectmanagements: list[Projectmanagement] = []
        # TODO: Since we don't have unique timesheet IDs, we can't deduplicate them, so we can't use a set.
        self.timesheets: list[Timesheet] = []
        self.uuid_to_dataqualityissues: dict[UUID, list[Dataqualityissue]] = {}
        self.uuid_to_worksheet: dict[UUID, ReadOnlyWorksheet] = {}

    def populate(self) -> Generator[TypeqlThing, None]:
        things = chain(
            self.id_to_personubwfris.values(),
            self.id_to_school.values(),
            self.id_to_projectlike.values(),
            self.timesheets,
            self.compositionprojects,
            self.projectmanagements,
            self.participationinternals,
        )
        logger.debug(
            "The UBW FRIS datasink now contains (with count): {personubwfris} ({n_personubwfriss}), {school} "
            "({n_schools}), {projectlike} ({n_projectlikes}), {timesheet} ({n_timesheets}), {compositionproject} "
            "({n_compositions}), {projectmanagement} ({n_projectmanagements}) and {participationinternal} "
            "({n_participationinternals}) ...",
            compositionproject=CompositionProject.model_config["title"],
            n_compositions=len(self.compositionprojects),
            n_participationinternals=len(self.participationinternals),
            n_personubwfriss=len(self.id_to_personubwfris.values()),
            n_projectlikes=len(self.id_to_projectlike.values()),
            n_projectmanagements=len(self.projectmanagements),
            n_schools=len(self.id_to_school.values()),
            n_timesheets=len(self.timesheets),
            participationinternal=Participationinternal.model_config["title"],
            personubwfris=PersonUbwfris.model_config["title"],
            projectlike=Projectlike.model_config["title"],
            projectmanagement=Projectmanagement.model_config["title"],
            school=School.model_config["title"],
            timesheet=Timesheet.model_config["title"],
        )
        yield from things
