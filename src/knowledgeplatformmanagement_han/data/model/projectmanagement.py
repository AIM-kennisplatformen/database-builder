from knowledgeplatformmanagement_generic.data.services.typedb.typeql import Key
from pydantic import ConfigDict, Field

from knowledgeplatformmanagement_han.data.model.personubwfris import PersonUbwfris
from knowledgeplatformmanagement_han.data.model.projectrole import Projectrole
from knowledgeplatformmanagement_han.data.model.subproject import Subproject


class Projectmanagement(Projectrole):
    def nonabstract_marker(self) -> None:
        pass

    model_config = ConfigDict(frozen=True, title="project management")

    managedsubproject: Key[Subproject] = Field(title="managed UBW subproject")
    projectmanager: Key[PersonUbwfris] = Field(title="project manager")
