from pydantic import ConfigDict

from knowledgeplatformmanagement_han.data.model.knowledgeinstitution import Knowledgeinstitution


class Researchuniversity(Knowledgeinstitution):
    def nonabstract_marker(self) -> None:
        pass

    model_config = ConfigDict(title="research university")
