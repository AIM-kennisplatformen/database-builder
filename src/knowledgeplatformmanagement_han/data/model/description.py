from typing import Annotated

from pydantic import ConfigDict, Field, StringConstraints

from knowledgeplatformmanagement_han.data.model.provenant import ProvenantString


class Description(ProvenantString):
    def nonabstract_marker(self) -> None:
        pass

    model_config = ConfigDict(title="description")

    value: Annotated[str, StringConstraints(min_length=1)] = Field(title="value")
