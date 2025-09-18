from pydantic import ConfigDict

from knowledgeplatformmanagement_han.data.model.projectlike import Projectlike


class Subproject(Projectlike):
    def nonabstract_marker(self) -> None:
        pass

    model_config = ConfigDict(title="subproject in UBW FRIS")
