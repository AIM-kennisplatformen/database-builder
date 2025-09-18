from knowledgeplatformmanagement_generic.data.services.typedb.typeql import Key
from pydantic import ConfigDict, Field

from knowledgeplatformmanagement_han.data.model.composition import Composition
from knowledgeplatformmanagement_han.data.model.projectlike import Projectlike
from knowledgeplatformmanagement_han.data.model.subproject import Subproject


class CompositionProject(Composition):
    def nonabstract_marker(self) -> None:
        pass

    model_config = ConfigDict(title="project composition")

    overarchingproject: Key[Projectlike] = Field(title="overarching project")
    projectpart: Key[Subproject] = Field(title="project part")
